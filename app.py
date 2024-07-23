from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, Response, jsonify
from video_monitor import get_abs_path
from db_utils import check_create_database
import sqlite3, os

app = Flask(__name__)
from sqlalchemy import func, case, and_
import logging


db_path = get_abs_path('data', 'brainy_bits.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/brainy_bits.db'  # Update with your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Emotion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    emotion = db.Column(db.Float, nullable=False)

class EyeTracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    direction = db.Column(db.Float, nullable=False)

class HeadPose(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    pose = db.Column(db.Float, nullable=False)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/classroom_monitoring')
def classroom_monitoring():
    return render_template('classroom_monitoring.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

def get_abs_path(*args):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *args)

def connect_to_db(db_path):
    db_conn = sqlite3.connect(db_path)
    return db_conn


def fetch_focus_data():
    conn = connect_to_db('data/brainy_bits.db')  # Update with your actual database path
    cursor = conn.cursor()

    # Aggregate the total seconds for each emotion
    cursor.execute("""
        SELECT 
            SUM(Angry_s) AS Angry_s,
            SUM(Sad_s) AS Sad_s,
            SUM(Happy_s) AS Happy_s,
            SUM(Fear_s) AS Fear_s,
            SUM(Disgust_s) AS Disgust_s,
            SUM(Neutral_s) AS Neutral_s,
            SUM(Surprise_s) AS Surprise_s
        FROM emotion_detect_data
        GROUP BY Person_ID
    """)
    emotion_totals = cursor.fetchone()

    cursor.execute("""
            SELECT Person_ID,
            SUM(Looking_Forward_s) AS Looking_Forward_s,
            SUM(Looking_Left_s) AS Looking_Left_s,
            SUM(Looking_Right_s) AS Looking_Right_s,
            SUM(Looking_Up_s) AS Looking_Up_s,
            SUM(Looking_Down_s) AS Looking_Down_s
        FROM head_pose_data
        GROUP BY Person_ID
        """)

    head_pose_data = cursor.fetchall()

    cursor.execute("""
            SELECT Person_ID,
                SUM(Duration_Eyes_Closed_s) AS Duration_Eyes_Closed_s,
                SUM(Duration_Looking_Left_s) AS Duration_Looking_Left_s,
                SUM(Duration_Looking_Right_s) AS Duration_Looking_Right_s,
                SUM(Duration_Looking_Straight_s) AS Duration_Looking_Straight_s
            FROM eye_track_data
            GROUP BY Person_ID
        """)
    eye_track_data = cursor.fetchall()

    conn.close()

    def round_float(value):
        if isinstance(value, float):
            # Round to 1 decimal place if the decimal part has more than 2 digits
            return round(value, 1) if len(f"{value:.10f}".split('.')[1]) > 2 else value
        return value

    def process_row(row):
        if isinstance(row, (list, tuple)):
            # Apply rounding to each float in the row
            return tuple(round_float(item) for item in row)
        elif isinstance(row, float):
            # Convert single float to a tuple with the float value
            return (round_float(row),)
        else:
            # Handle other unexpected types if necessary
            print(f"Unexpected row type: {type(row)}")
            return None

    def create_dict_from_rows(rows):
        result = {}
        for index, row in enumerate(rows):
            if row:
                if len(row) > 1:
                    # Handle rows with multiple elements
                    result[row[0]] = row[1:]
                elif len(row) == 1:
                    # Handle single float rows by creating default key-value pairs
                    result[f"key_{index + 1}"] = row[0]
                else:
                    print(f"Row does not have enough data to create a dictionary entry: {row}")
        return result

    # Process and create dictionaries
    emotion_totals = [process_row(row) for row in emotion_totals]
    head_pose_data = [process_row(row) for row in head_pose_data]
    eye_track_data = [process_row(row) for row in eye_track_data]

    emotion_dict = create_dict_from_rows(emotion_totals)
    head_pose_dict = create_dict_from_rows(head_pose_data)
    eye_tracking_dict = create_dict_from_rows(eye_track_data)

    print(emotion_dict)

    focused = 0
    not_focused = 0

    print('works')

    for person_id in emotion_dict:
        # Directly access the float value
        neutral_time = emotion_dict[person_id]
        print('works2')

        # Calculate total emotion time if you have multiple values to sum
        # For single float values, this will be just the float itself
        total_emotion_time = neutral_time
        print(total_emotion_time)

        # Define conditions for being focused
        if (neutral_time > total_emotion_time / 2 or
                head_pose_dict.get(person_id, [0] * 5)[0] > sum(head_pose_dict.get(person_id, [0] * 5)[1:]) or
                eye_tracking_dict.get(person_id, [0] * 4)[3] > sum(eye_tracking_dict.get(person_id, [0] * 4)[:3])):
            focused += neutral_time
        else:
            not_focused += total_emotion_time - neutral_time

    print(focused)
    print(not_focused)

    return {
        'neutral': focused,
        'not_neutral': not_focused
    }

@app.route('/get_data')
def get_data():
    try:
        focus_data = fetch_focus_data()
        return jsonify(focus_data)
    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/video_feed')
def video_feed():
    from video_monitor import generate_frames  # Import inside the function to avoid circular import
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/data')
def get_data():
    data = []
    with open('data.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append({
                'date': row['date'],
                'focused': int(row['focused']),
                'not_focused': int(row['not_focused'])
            })
    return jsonify(data)



if __name__ == '__main__':
    print("Starting the app...")
    check_create_database(db_path)
    app.run(debug=True)
