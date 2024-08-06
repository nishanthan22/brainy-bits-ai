from datetime import date

from flask import Flask, request, redirect, render_template, Response, jsonify, url_for
from config import logger
from db_utils import create_database_tables
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.secret_key = 'forcontactus'
csrf = CSRFProtect(app)


@app.route('/init_database', methods=['GET'])
def init_database():
    logger.info("Initiating database setup.")
    status_code, error = create_database_tables()
    if status_code == 1:
        logger.info("Database initialized successfully.")
        return jsonify({"status": "SUCCESS", "code": "200 OK", "message": "Database initialized successfully"})
    else:
        logger.error(f"Database initialization failed: {error}")
        return jsonify(
            {"status": "FAILURE", "code": "500", "message": "Database initialization failed", "error": error})


@app.route('/')
def home():
    logger.debug("Rendering home page.")
    return render_template('index.html')


@app.route('/classroom_monitoring')
def classroom_monitoring():
    logger.debug("Rendering classroom monitoring page.")
    return render_template('classroom_monitoring.html')


@app.route('/dashboard')
def dashboard():
    logger.debug("Rendering dashboard page.")
    return render_template('dashboard.html')


@app.route('/socials')
def socials():
    return render_template('socials.html')


@app.route('/about_us')
def about_us():
    return render_template('about_us.html')


@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')


@app.route('/terms_of_service')
def terms_of_service():
    return render_template('terms_of_service.html')


@app.route('/advertise')
def advertise():
    return render_template('advertise.html')


@app.route('/contact_us', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        # Process the form data here
        # name = request.form.get('name')
        # email = request.form.get('email')
        # message = request.form.get('message')

        # After processing, redirect or respond accordingly
        return redirect(url_for('contact_us'))  # Or any other relevant route
    return render_template('contact_us.html')


@app.route('/team_details')
def team_details():
    return render_template('team_details.html')


def fetch_focus_data():
    from db_utils import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            user_id
        FROM emotion_detect_data
        WHERE Date >= CURDATE() - INTERVAL 7 DAY
    """)

    user_id_list = cursor.fetchall()
    user_id_list = [user_id[0] for user_id in user_id_list]

    focussed = 0
    not_focussed = 0
    for i in user_id_list:
        datalist = []
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
                   WHERE user_id = %s
               """, (i,))
        row = cursor.fetchone()

        if row:
            max_value = max(row)
            max_column_index = row.index(max_value)
            columns = ['Angry_s', 'Sad_s', 'Happy_s', 'Fear_s', 'Disgust_s', 'Neutral_s', 'Surprise_s']
            max_column = columns[max_column_index]

            datalist.append(max_column)

        cursor.execute("""
                           SELECT
                               Looking_Forward_s,
                               Looking_Left_s,
                               Looking_Right_s,
                               Looking_Up_s,
                               Looking_Down_s
                           FROM head_pose_data
                           WHERE user_id = %s
                       """, (i,))
        row = cursor.fetchone()

        if row:
            max_value = max(row)
            max_column_index = row.index(max_value)
            columns = ['Looking_Forward_s', 'Looking_Left_s', 'Looking_Right_s', 'Looking_Up_s', 'Looking_Down_s']
            max_column = columns[max_column_index]

            datalist.append(max_column)

        cursor.execute("""
                                   SELECT
                                       Duration_Eyes_Closed_s,
                                       Duration_Looking_Left_s,
                                       Duration_Looking_Right_s,
                                       Duration_Looking_Straight_s
                                   FROM eye_track_data
                                   WHERE user_id = %s
                               """, (i,))
        row = cursor.fetchone()

        if row:
            max_value = max(row)
            max_column_index = row.index(max_value)
            columns = ['Duration_Eyes_Closed_s', 'Duration_Looking_Left_s', 'Duration_Looking_Right_s',
                       'Duration_Looking_Straight_s']
            max_column = columns[max_column_index]

            datalist.append(max_column)

        if ('Happy_s' in datalist or 'Neutral_s' in datalist) and 'Duration_Looking_Straight_s' in datalist:
            focussed += 1
        elif 'Looking_Down_s' in datalist or 'Duration_Eyes_Closed_s' in datalist or 'Angry_s' in datalist or 'Fear_s' in datalist or 'Surprise_s' in datalist:
            not_focussed += 1
        elif 'Looking_Forward' in datalist and (
                'Duration_Looking_Left_s' in datalist or 'Duration_Looking_Right_s' in datalist):
            not_focussed += 1
        elif 'Sad_s' in datalist and 'Duration_Eyes_Closed_s' in datalist:
            not_focussed += 1
        elif 'Sad_s' in datalist and 'Looking_Forward_s' not in datalist:
            not_focussed += 1
        elif 'Duration_Looking_Left_s' in datalist and 'Looking_Left_s' in datalist:
            focussed += 1
        elif 'Duration_Right_Left_s' in datalist and 'Looking_Right_s' in datalist:
            focussed += 1
        else:
            focussed += 1

    conn.close()

    return {
        'Focussed': focussed,
        'Not Focussed': not_focussed
    }


@app.route('/get_data')
def get_data():
    logger.debug("Entering get_data method")
    try:
        focus_data = fetch_focus_data()
        logger.info('Fetched focus data:', focus_data)
        return jsonify(focus_data)
    except Exception as e:
        logger.error('Error fetching focus data:', exc_info=True)
        return jsonify({'error': str(e)})


def fetch_focus_data_today():
    from db_utils import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()

    today = date.today()

    cursor.execute("""
        SELECT
            user_id
        FROM emotion_detect_data
        WHERE Date = %s
    """, (today,))

    user_id_list = cursor.fetchall()
    user_id_list = [user_id[0] for user_id in user_id_list]

    focussed = 0
    not_focussed = 0
    for i in user_id_list:
        datalist = []
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
                   WHERE user_id = %s AND Date = %s
               """, (i, today))
        row = cursor.fetchone()

        if row:
            max_value = max(row)
            max_column_index = row.index(max_value)
            columns = ['Angry_s', 'Sad_s', 'Happy_s', 'Fear_s', 'Disgust_s', 'Neutral_s', 'Surprise_s']
            max_column = columns[max_column_index]

            datalist.append(max_column)

        cursor.execute("""
                           SELECT
                               Looking_Forward_s,
                               Looking_Left_s,
                               Looking_Right_s,
                               Looking_Up_s,
                               Looking_Down_s
                           FROM head_pose_data
                           WHERE user_id = %s AND Date = %s
                       """, (i, today))
        row = cursor.fetchone()

        if row:
            max_value = max(row)
            max_column_index = row.index(max_value)
            columns = ['Looking_Forward_s', 'Looking_Left_s', 'Looking_Right_s', 'Looking_Up_s', 'Looking_Down_s']
            max_column = columns[max_column_index]

            datalist.append(max_column)

        cursor.execute("""
                                   SELECT
                                       Duration_Eyes_Closed_s,
                                       Duration_Looking_Left_s,
                                       Duration_Looking_Right_s,
                                       Duration_Looking_Straight_s
                                   FROM eye_track_data
                                   WHERE user_id = %s AND Date = %s
                               """, (i, today))
        row = cursor.fetchone()

        if row:
            max_value = max(row)
            max_column_index = row.index(max_value)
            columns = ['Duration_Eyes_Closed_s', 'Duration_Looking_Left_s', 'Duration_Looking_Right_s',
                       'Duration_Looking_Straight_s']
            max_column = columns[max_column_index]

            datalist.append(max_column)

        if ('Happy_s' in datalist or 'Neutral_s' in datalist) and 'Duration_Looking_Straight_s' in datalist:
            focussed += 1
        elif 'Looking_Down_s' in datalist or 'Duration_Eyes_Closed_s' in datalist or 'Angry_s' in datalist or 'Fear_s' in datalist or 'Surprise_s' in datalist:
            not_focussed += 1
        elif 'Looking_Forward' in datalist and (
                'Duration_Looking_Left_s' in datalist or 'Duration_Looking_Right_s' in datalist):
            not_focussed += 1
        elif 'Sad_s' in datalist and 'Duration_Eyes_Closed_s' in datalist:
            not_focussed += 1
        elif 'Sad_s' in datalist and 'Looking_Forward_s' not in datalist:
            not_focussed += 1
        elif 'Duration_Looking_Left_s' in datalist and 'Looking_Left_s' in datalist:
            focussed += 1
        elif 'Duration_Right_Left_s' in datalist and 'Looking_Right_s' in datalist:
            focussed += 1
        else:
            focussed += 1

    conn.close()

    return {
        'Focussed': focussed,
        'Not Focussed': not_focussed
    }


@app.route('/get_data_today')
def get_data_today():
    logger.debug("Entering get_data_today method")
    try:
        today_data = fetch_focus_data_today()
        logger.info('Fetched today data:', today_data)
        return jsonify(today_data)
    except Exception as e:
        logger.error('Error fetching today data:', exc_info=True)
        return jsonify({'error': str(e)})


@app.route('/get_weekly_data')
def get_weekly_data():
    from db_utils import get_db_connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the last 7 days' data
        cursor.execute("""
            SELECT
                Date
            FROM emotion_detect_data
            WHERE Date >= CURDATE() - INTERVAL 30 DAY
            GROUP BY Date
            ORDER BY Date ASC
        """)

        weekly_data = cursor.fetchall()
        formatted_data = []

        for date_row in weekly_data:
            date = date_row[0]

            # Fetch user_id list for the current date
            cursor.execute("""
                SELECT
                    user_id
                FROM emotion_detect_data
                WHERE Date = %s
            """, (date,))

            user_id_list = cursor.fetchall()
            user_id_list = [user_id[0] for user_id in user_id_list]

            focussed = 0
            not_focussed = 0

            for i in user_id_list:
                datalist = []

                # Get emotion data
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
                    WHERE user_id = %s AND Date = %s
                """, (i, date))
                row = cursor.fetchone()

                if row:
                    max_value = max(row)
                    max_column_index = row.index(max_value)
                    columns = ['Angry_s', 'Sad_s', 'Happy_s', 'Fear_s', 'Disgust_s', 'Neutral_s', 'Surprise_s']
                    max_column = columns[max_column_index]
                    datalist.append(max_column)

                # Get head pose data
                cursor.execute("""
                    SELECT
                        Looking_Forward_s,
                        Looking_Left_s,
                        Looking_Right_s,
                        Looking_Up_s,
                        Looking_Down_s
                    FROM head_pose_data
                    WHERE user_id = %s AND Date = %s
                """, (i, date))
                row = cursor.fetchone()

                if row:
                    max_value = max(row)
                    max_column_index = row.index(max_value)
                    columns = ['Looking_Forward_s', 'Looking_Left_s', 'Looking_Right_s', 'Looking_Up_s',
                               'Looking_Down_s']
                    max_column = columns[max_column_index]
                    datalist.append(max_column)

                # Get eye track data
                cursor.execute("""
                    SELECT
                        Duration_Eyes_Closed_s,
                        Duration_Looking_Left_s,
                        Duration_Looking_Right_s,
                        Duration_Looking_Straight_s
                    FROM eye_track_data
                    WHERE user_id = %s AND Date = %s
                """, (i, date))
                row = cursor.fetchone()

                if row:
                    max_value = max(row)
                    max_column_index = row.index(max_value)
                    columns = ['Duration_Eyes_Closed_s', 'Duration_Looking_Left_s', 'Duration_Looking_Right_s',
                               'Duration_Looking_Straight_s']
                    max_column = columns[max_column_index]
                    datalist.append(max_column)

                # Determine focus status
                if ('Happy_s' in datalist or 'Neutral_s' in datalist) and 'Duration_Looking_Straight_s' in datalist:
                    focussed += 1
                elif 'Looking_Down_s' in datalist or 'Duration_Eyes_Closed_s' in datalist or 'Angry_s' in datalist or 'Fear_s' in datalist or 'Surprise_s' in datalist:
                    not_focussed += 1
                elif 'Looking_Forward_s' in datalist and (
                        'Duration_Looking_Left_s' in datalist or 'Duration_Looking_Right_s' in datalist):
                    not_focussed += 1
                elif 'Sad_s' in datalist and 'Duration_Eyes_Closed_s' in datalist:
                    not_focussed += 1
                elif 'Sad_s' in datalist and 'Looking_Forward_s' not in datalist:
                    not_focussed += 1
                elif 'Duration_Looking_Left_s' in datalist and 'Looking_Left_s' in datalist:
                    focussed += 1
                elif 'Duration_Looking_Right_s' in datalist and 'Looking_Right_s' in datalist:
                    focussed += 1
                else:
                    focussed += 1

            formatted_data.append({
                "date": date.strftime('%Y-%m-%d'),
                "focused": focussed,
                "not_focused": not_focussed
            })

        return jsonify(formatted_data)

    except Exception as e:
        logger.error('Error fetching weekly data:', exc_info=True)
        return jsonify({'error': str(e)})


@app.route('/video_feed')
def video_feed():
    from video_monitor import generate_frames  # Import inside the function to avoid circular import
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/generate_userid_QA', methods=['GET'])
def generate_userid_QA():
    logger.debug("Entering generate_userid_QA method")
    from video_monitor import generate_user_id
    user_id = generate_user_id()
    if user_id is None:
        return jsonify({'status': 'FAILURE', 'code': '500', 'message': 'User ID could not be generated.'})
    return jsonify({'status': 'SUCCESS', 'code': '200 OK', 'user_id': user_id})


if __name__ == '__main__':
    print("Starting the app...")
    logger.info("Starting the app...")
    with app.app_context():
        init_database()
    app.run(debug=True)
