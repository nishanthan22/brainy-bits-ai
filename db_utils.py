import os
import sqlite3


def connect_to_db(db_path):
    db_conn = sqlite3.connect(db_path)
    return db_conn


def create_database(db_path):
    connection = sqlite3.connect(db_path)
    db_cursor = connection.cursor()
    db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS eye_track_data (
                user_id INTEGER PRIMARY KEY,
                Date DATE,
                Person_ID TEXT,
                Duration_Eyes_Closed_s REAL,
                Duration_Looking_Left_s REAL,
                Duration_Looking_Right_s REAL,
                Duration_Looking_Straight_s REAL,
                Left_Counts INTEGER,
                Right_Counts INTEGER,
                Straight_Counts INTEGER
            )
        ''')

    db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS emotion_detect_data (
                user_id INTEGER PRIMARY KEY,
                Date DATE,
                Person_ID TEXT,
                Angry_s REAL,
                Sad_s REAL,
                Happy_s REAL,
                Fear_s REAL,
                Disgust_s REAL,
                Neutral_s REAL,
                Surprise_s REAL
            )
        ''')

    db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS head_pose_data (
                user_id INTEGER PRIMARY KEY,
                Date DATE,
                Person_ID TEXT,
                Looking_Forward_s REAL,
                Looking_Left_s REAL,
                Looking_Right_s REAL,
                Looking_Up_s REAL,
                Looking_Down_s REAL
            )
        ''')
    connection.commit()
    connection.close()


def check_create_database(db_path):
    if not os.path.exists(db_path):
        create_database(db_path)
