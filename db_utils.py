import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from config import logger
load_dotenv()

# Database configuration
db_config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME')
}


# Function to create a connection to the database
def get_db_connection():
    logger.info('Connecting to MySQL database...')
    return mysql.connector.connect(**db_config)


def create_database_tables():
    status = 1
    connection = None
    error_message = 'None'
    logger.info('Creating database tables...')
    try:
        connection = get_db_connection()
        db_cursor = connection.cursor()

        db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS eye_track_data (
                user_id INTEGER PRIMARY KEY,
                Date DATE NULL,
                Person_ID VARCHAR(255),
                Duration_Eyes_Closed_s FLOAT,
                Duration_Looking_Left_s FLOAT,
                Duration_Looking_Right_s FLOAT,
                Duration_Looking_Straight_s FLOAT,
                Left_Counts INTEGER,
                Right_Counts INTEGER,
                Straight_Counts INTEGER
            )
        ''')
        logger.info('eye_track_data table created.')
        db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS emotion_detect_data (
                user_id INTEGER PRIMARY KEY,
                Date DATE NULL,
                Person_ID VARCHAR(255),
                Angry_s FLOAT,
                Sad_s FLOAT,
                Happy_s FLOAT,
                Fear_s FLOAT,
                Disgust_s FLOAT,
                Neutral_s FLOAT,
                Surprise_s FLOAT
            )
        ''')
        logger.info('emotion_detect_data table created.')
        db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS head_pose_data (
                user_id INTEGER PRIMARY KEY,
                Date DATE NULL,
                Person_ID VARCHAR(255),
                Looking_Forward_s FLOAT,
                Looking_Left_s FLOAT,
                Looking_Right_s FLOAT,
                Looking_Up_s FLOAT,
                Looking_Down_s FLOAT
            )
        ''')
        logger.info('head_pose_data table created.')
        connection.commit()
    except Error as e:
        logger.error(f"Database error: {e}")
        status = 0
        error_message = str(e)
    except Exception as e:
        logger.error(f"Unknown error: {e}")
        status = 0
        error_message = str(e)
    finally:
        if connection and connection.is_connected():
            connection.close()
    return status, error_message
