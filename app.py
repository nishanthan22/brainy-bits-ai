from flask import Flask, render_template, Response, jsonify
from config import logger
from db_utils import create_database_tables
app = Flask(__name__)
import datetime


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


def fetch_focus_data():
    from db_utils import get_db_connection
    conn = get_db_connection()
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
                           WHERE user_id = %s
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
                                   WHERE user_id = %s
                               """, (i,))
        row = cursor.fetchone()

        if row:
            max_value = max(row)
            max_column_index = row.index(max_value)
            columns = ['Duration_Eyes_Closed_s', 'Duration_Looking_Left_s', 'Duration_Looking_Right_s',
                       'Duration_Looking_Straight_s']
            max_column = columns[max_column_index]

            print('eye-tracking: ', max_column)
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

    print(focussed, 'and ', not_focussed)

    return {
        'neutral': focussed,
        'not_neutral': not_focussed
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

    today = datetime.date.today()
    print(today)

    cursor.execute("""
        SELECT
            user_id
        FROM emotion_detect_data
        WHERE DATE(Date) = %s
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
                   WHERE user_id = %s AND DATE(Date) = %s
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
                           WHERE user_id = %s AND DATE(Date) = %s
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
                                   WHERE user_id = %s AND DATE(Date) = %s
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
        elif 'Looking_Forward' in datalist and ('Duration_Looking_Left_s' in datalist or 'Duration_Looking_Right_s' in datalist):
            not_focussed += 1
        elif 'Sad_s' in datalist and 'Duration_Eyes_Closed_s' in datalist:
            not_focussed += 1
        elif 'Sad_s' in datalist and 'Looking_Forward_s' not in datalist:
            not_focussed += 1
        elif 'Duration_Looking_Left_s' in datalist and 'Looking_Left_s' in datalist:
            focussed +=1
        elif 'Duration_Right_Left_s' in datalist and 'Looking_Right_s' in datalist:
            focussed +=1
        else:
            focussed += 1

    conn.close()

    return {
        'focussed': focussed,
        'not_focussed': not_focussed
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


def fetch_focus_data_over_time():
    from db_utils import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            Date,
            SUM(CASE WHEN condition_for_focussed THEN 1 ELSE 0 END) as Focussed,
            SUM(CASE WHEN NOT condition_for_focussed THEN 1 ELSE 0 END) as Not_Focussed
        FROM
            your_table_name
        GROUP BY
            Date
        ORDER BY
            Date ASC
    """)

    data = cursor.fetchall()
    conn.close()

    formatted_data = [{"date": str(row[0]), "focussed": row[1], "not_focussed": row[2]} for row in data]
    return formatted_data


def get_line_chart_data():
    logger.debug("Entering get_line_chart_data method")
    print('line')
    try:
        focus_data_over_time = fetch_focus_data_over_time()
        logger.info('Fetched focus data over time:', focus_data_over_time)
        return jsonify(focus_data_over_time)
    except Exception as e:
        logger.error('Error fetching focus data over time:', exc_info=True)
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
