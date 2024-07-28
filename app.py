from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, Response, jsonify
from video_monitor import get_abs_path
from db_utils import check_create_database
import sqlite3, os
app = Flask(__name__)
from sqlalchemy import func, case, and_
import logging
from datetime import datetime, date


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


def fetch_focus_data_today():
    conn = connect_to_db('data/brainy_bits.db')  # Update with your actual database path
    cursor = conn.cursor()

    # Get the last N entries for today, assuming recent entries are today's data
    N = 2  # Adjust this value based on your data insertion frequency
    cursor.execute("SELECT user_id FROM emotion_detect_data ORDER BY user_id DESC LIMIT ?", (N,))
    user_id_list = cursor.fetchall()
    user_id_list = [user_id[0] for user_id in user_id_list]

    focussed = 0
    not_focussed = 0

    for i in user_id_list:
        datalist = []

        cursor.execute("""
            SELECT Angry_s, Sad_s, Happy_s, Fear_s, Disgust_s, Neutral_s, Surprise_s
            FROM emotion_detect_data
            WHERE user_id = ?
        """, (i,))
        row = cursor.fetchone()

        if row:
            max_value = max(row)
            max_column_index = row.index(max_value)
            columns = ['Angry_s', 'Sad_s', 'Happy_s', 'Fear_s', 'Disgust_s', 'Neutral_s', 'Surprise_s']
            max_column = columns[max_column_index]
            datalist.append(max_column)

        cursor.execute("""
            SELECT Looking_Forward_s, Looking_Left_s, Looking_Right_s, Looking_Up_s, Looking_Down_s
            FROM head_pose_data
            WHERE user_id = ?
        """, (i,))
        row = cursor.fetchone()

        if row:
            max_value = max(row)
            max_column_index = row.index(max_value)
            columns = ['Looking_Forward_s', 'Looking_Left_s', 'Looking_Right_s', 'Looking_Up_s', 'Looking_Down_s']
            max_column = columns[max_column_index]
            datalist.append(max_column)

        cursor.execute("""
            SELECT Duration_Eyes_Closed_s, Duration_Looking_Left_s, Duration_Looking_Right_s, Duration_Looking_Straight_s
            FROM eye_track_data
            WHERE user_id = ?
        """, (i,))
        row = cursor.fetchone()

        if row:
            max_value = max(row)
            max_column_index = row.index(max_value)
            columns = ['Duration_Eyes_Closed_s', 'Duration_Looking_Left_s', 'Duration_Looking_Right_s', 'Duration_Looking_Straight_s']
            max_column = columns[max_column_index]
            datalist.append(max_column)

        if 'Happy_s' in datalist and 'Duration_Looking_Straight_s' in datalist and 'Looking_Forward_s' in datalist:
            focussed += 1
        else:
            not_focussed += 1

    conn.close()

    print(focussed, 'and ', not_focussed)

    return {
        'focussed': focussed,
        'not_focussed': not_focussed
}


def fetch_focus_data():
    conn = connect_to_db('data/brainy_bits.db')  # Update with your actual database path
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            user_id
        FROM emotion_detect_data
        """)

    user_id_list = cursor.fetchall()
    user_id_list = [user_id[0] for user_id in user_id_list]

    focussed = 0
    not_focussed = 0
    for i in user_id_list:
        datalist=[]
        cursor.execute("""
                   SELECT
                       Angry_s,
                       Sad_s,
                       Happy_s,
                       Fear_s,
                       Disgust_s,
                       Neutral_s,
                       Surprise_s
                   FROM emotion_detect_data
                   WHERE user_id = ?
               """, (i,))
        row = cursor.fetchone()

        if row:
            max_value = max(row)
            max_column_index = row.index(max_value)
            columns = ['Angry_s', 'Sad_s', 'Happy_s', 'Fear_s', 'Disgust_s', 'Neutral_s', 'Surprise_s']
            max_column = columns[max_column_index]

            print('emotion: ', max_column)
            datalist.append(max_column)


        cursor.execute("""
                           SELECT
                               Looking_Forward_s,
                               Looking_Left_s,
                               Looking_Right_s,
                               Looking_Up_s,
                               Looking_Down_s
                           FROM head_pose_data
                           WHERE user_id = ?
                       """, (i,))
        row = cursor.fetchone()

        if row:
            max_value = max(row)
            max_column_index = row.index(max_value)
            columns = ['Looking_Forward_s', 'Looking_Left_s', 'Looking_Right_s', 'Looking_Up_s', 'Looking_Down_s']
            max_column = columns[max_column_index]

            print('head: ', max_column)
            datalist.append(max_column)

        cursor.execute("""
                                   SELECT
                                       Duration_Eyes_Closed_s,
                                       Duration_Looking_Left_s,
                                       Duration_Looking_Right_s,
                                       Duration_Looking_Straight_s
                                   FROM eye_track_data
                                   WHERE user_id = ?
                               """, (i,))
        row = cursor.fetchone()

        if row:
            max_value = max(row)
            max_column_index = row.index(max_value)
            columns = ['Duration_Eyes_Closed_s', 'Duration_Looking_Left_s', 'Duration_Looking_Right_s', 'Duration_Looking_Straight_s']
            max_column = columns[max_column_index]

            print('eye-tracking: ', max_column)
            datalist.append(max_column)

        if 'Happy_s' in datalist and 'Duration_Looking_Straight_s' in datalist and 'Looking_Forward_s' in datalist:
            focussed += 1
        else:
            not_focussed +=1
    conn.close()

    print(focussed, 'and ', not_focussed)

    return {
        'neutral': focussed,
        'not_neutral': not_focussed
    }

@app.route('/get_data')
def get_data():
    try:
        focus_data = fetch_focus_data()
        return jsonify(focus_data)
    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': str(e)}), 500


@app.route('/get_data_today')
def get_data_today():
    try:
        focus_data = fetch_focus_data_today()
        print('focus', focus_data)
        return jsonify(focus_data)
    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/video_feed')
def video_feed():
    from video_monitor import generate_frames  # Import inside the function to avoid circular import
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    print("Starting the app...")
    check_create_database(db_path)
    app.run(debug=True)