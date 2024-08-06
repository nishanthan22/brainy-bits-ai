import csv
import os
import time
import sqlite3

import cv2
import dlib
import mediapipe as mp
import numpy as np
import tensorflow as tf
from imutils import face_utils
from scipy.ndimage import zoom
from tensorflow.keras.models import load_model
from datetime import datetime
from config import logger

def get_abs_path(directory, file):
    directory_path = os.path.join(os.getcwd(), '', directory)
    file_path = os.path.join(directory_path, file)
    return file_path


def generate_user_id():
    from db_utils import get_db_connection
    db_conn = get_db_connection()
    db_cursor = db_conn.cursor()

    logger.info("Creating user table if not exists")
    db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_ids (
            user_id REAL NOT NULL PRIMARY KEY,
            date_created DATE NULL
        )
    ''')

    # Get the last user_id from the table
    db_cursor.execute('SELECT user_id FROM user_ids ORDER BY user_id DESC LIMIT 1')
    result = db_cursor.fetchone()
    if result:
        last_id = int(result[0])
    else:
        last_id = 70000
    logger.info("Last user id is: {}".format(last_id))
    next_id = last_id + 1
    date_created = datetime.now().date()

    # Insert the new user_id into the table
    db_cursor.execute('''
        INSERT INTO user_ids (user_id, date_created)
        VALUES (%s, %s)
    ''', (next_id, date_created))
    logger.info("New user id : {} inserted in database".format(next_id))
    db_conn.commit()
    db_conn.close()

    return next_id


def generate_frames():
    print("Generating the frames...")

    def custom_VarianceScaling_deserializer(config):
        from tensorflow.keras.initializers import VarianceScaling
        config.pop('dtype', None)
        return VarianceScaling(**config)

    tf.keras.utils.get_custom_objects().update({'VarianceScaling': custom_VarianceScaling_deserializer})
    tf.keras.utils.get_custom_objects().update({'BatchNormalization': tf.keras.layers.BatchNormalization})

    def detect_eyes(frame, shape):
        left_eye = shape[36:42]
        right_eye = shape[42:48]
        return left_eye, right_eye

    def calculate_ear(eye):
        eye = np.array([(point[0], point[1]) for point in eye])
        A = np.linalg.norm(eye[1] - eye[5])
        B = np.linalg.norm(eye[2] - eye[4])
        C = np.linalg.norm(eye[0] - eye[3])
        if C == 0:
            return 0  # Avoid division by zero
        ear = (A + B) / (2.0 * C)
        return ear

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(get_abs_path('scripts', 'shape_predictor_68_face_landmarks.dat'))

    emotion_model = load_model(get_abs_path('scripts', 'FER_model.h5'))
    emotion_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

    cap = cv2.VideoCapture(0)

    person_ids = {}  # Dictionary to store person_id and corresponding user_id
    next_user_id = generate_user_id()

    duration_eyes_closed = {}
    duration_looking_left = {}
    duration_looking_right = {}
    duration_looking_straight = {}

    count_left = {}
    count_right = {}
    count_straight = {}

    emotion_start_time = time.time()
    emotion_duration = {"angry": {}, "sad": {}, "happy": {}, "fear": {}, "disgust": {}, "neutral": {}, "surprise": {}}

    time_forward_seconds = {}
    time_left_seconds = {}
    time_right_seconds = {}
    time_up_seconds = {}
    time_down_seconds = {}

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray)

            for i, face in enumerate(faces):
                shape = predictor(gray, face)
                shape = face_utils.shape_to_np(shape)

                person_id = f"Person {i + 1}"

                # Assign a unique user ID to each person and reuse it if they reappear
                if person_id not in person_ids:
                    person_ids[person_id] = next_user_id
                    next_user_id = generate_user_id()

                user_id = person_ids[person_id]

                if person_id not in duration_eyes_closed:
                    duration_eyes_closed[person_id] = 0
                    duration_looking_left[person_id] = 0
                    duration_looking_right[person_id] = 0
                    duration_looking_straight[person_id] = 0
                    count_left[person_id] = 0
                    count_right[person_id] = 0
                    count_straight[person_id] = 0
                    time_forward_seconds[person_id] = 0
                    time_left_seconds[person_id] = 0
                    time_right_seconds[person_id] = 0
                    time_up_seconds[person_id] = 0
                    time_down_seconds[person_id] = 0
                    for emotion in emotion_duration:
                        emotion_duration[emotion][person_id] = 0

                left_eye, right_eye = detect_eyes(frame, shape)
                if left_eye is not None and right_eye is not None:
                    ear_left = calculate_ear(left_eye)
                    ear_right = calculate_ear(right_eye)
                    avg_ear = (ear_left + ear_right) / 2.0
                    distraction_threshold = 0.2

                    if avg_ear < distraction_threshold:
                        cv2.putText(frame, f"{person_id}: Eyes Closed", (10, 30 + i * 30), cv2.FONT_HERSHEY_SIMPLEX,
                                    1.2,
                                    (0, 0, 255), 2)
                        duration_eyes_closed[person_id] += 1 / cap.get(cv2.CAP_PROP_FPS)
                        count_straight[person_id] += 1

                    else:
                        horizontal_ratio = (left_eye[0][0] + right_eye[3][0]) / 2 / frame.shape[1]
                        if horizontal_ratio < 0.4:
                            cv2.putText(frame, f"{person_id}: Looking Left", (10, 30 + i * 30),
                                        cv2.FONT_HERSHEY_SIMPLEX,
                                        1.2, (0, 255, 0), 2)
                            duration_looking_left[person_id] += 1 / cap.get(cv2.CAP_PROP_FPS)
                            count_left[person_id] += 1
                        elif horizontal_ratio > 0.6:
                            cv2.putText(frame, f"{person_id}: Looking Right", (10, 30 + i * 30),
                                        cv2.FONT_HERSHEY_SIMPLEX,
                                        1.2, (0, 255, 0), 2)
                            duration_looking_right[person_id] += 1 / cap.get(cv2.CAP_PROP_FPS)
                            count_right[person_id] += 1
                        else:
                            cv2.putText(frame, f"{person_id}: Looking Straight", (10, 30 + i * 30),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
                            duration_looking_straight[person_id] += 1 / cap.get(cv2.CAP_PROP_FPS)

                    for eye in [left_eye, right_eye]:
                        for point in eye:
                            x, y = point[0], point[1]
                            cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)

                (x, y, w, h) = face_utils.rect_to_bb(face)
                face_crop = gray[y:y + h, x:x + w]
                face_crop = zoom(face_crop, (48 / face_crop.shape[0], 48 / face_crop.shape[1]))
                face_crop = face_crop.astype(np.float32)
                if face_crop.max() == 0:
                    continue
                face_crop /= float(face_crop.max())
                face_crop = np.reshape(face_crop.flatten(), (1, 48, 48, 1))

                prediction = emotion_model.predict(face_crop)
                prediction_result = np.argmax(prediction)

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                emotion_labels = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]
                emotion_label = emotion_labels[prediction_result]
                cv2.putText(frame, f"{person_id}: {emotion_label}", (x + w - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 255, 0), 2)
                emotion_duration[emotion_label.lower()][person_id] += time.time() - emotion_start_time
                emotion_start_time = time.time()

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_rgb.flags.writeable = False
                results = face_mesh.process(frame_rgb)
                frame_rgb.flags.writeable = True
                frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

                img_h, img_w, img_c = frame.shape
                face_3d = []
                face_2d = []

                if results.multi_face_landmarks:
                    for face_landmarks in results.multi_face_landmarks:
                        for idx, lm in enumerate(face_landmarks.landmark):
                            if idx == 33 or idx == 263 or idx == 1 or idx == 61 or idx == 291 or idx == 199:
                                if idx == 1:
                                    nose_2d = (lm.x * img_w, lm.y * img_h)
                                    nose_3d = (lm.x * img_w, lm.y * img_h, lm.z * 8000)
                                x, y = int(lm.x * img_w), int(lm.y * img_h)
                                face_2d.append([x, y])
                                face_3d.append([x, y, lm.z])

                    if face_2d and face_3d:
                        face_2d = np.array(face_2d, dtype=np.float64)
                        face_3d = np.array(face_3d, dtype=np.float64)
                        focal_length = 1 * img_w
                        cam_matrix = np.array([[focal_length, 0, img_w / 2],
                                               [0, focal_length, img_h / 2],
                                               [0, 0, 1]])

                        dist_matrix = np.zeros((4, 1), dtype=np.float64)

                        success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
                        if success:
                            rmat, jac = cv2.Rodrigues(rot_vec)

                            angles, mtx_r, mtx_q, qx, qy, qz = cv2.RQDecomp3x3(rmat)

                            x_angle = angles[0] * 360
                            y_angle = angles[1] * 360
                            z_angle = angles[2] * 360

                            if y_angle < -10:
                                text = "Looking Left"
                                time_left_seconds[person_id] += 1 / cap.get(cv2.CAP_PROP_FPS)
                            elif y_angle > 10:
                                text = "Looking Right"
                                time_right_seconds[person_id] += 1 / cap.get(cv2.CAP_PROP_FPS)
                            elif x_angle < -10:
                                text = "Looking Down"
                                time_down_seconds[person_id] += 1 / cap.get(cv2.CAP_PROP_FPS)
                            elif x_angle > 10:
                                text = "Looking Up"
                                time_up_seconds[person_id] += 1 / cap.get(cv2.CAP_PROP_FPS)
                            else:
                                text = "Looking Forward"
                                time_forward_seconds[person_id] += 1 / cap.get(cv2.CAP_PROP_FPS)

                            cv2.putText(frame, f"{person_id}: {text}", (500, 50 + i * 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                        (0, 255, 0), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    except Exception as e:
        print(f"Error: {e}")

    finally:
        cap.release()
        from db_utils import get_db_connection  # Import here to avoid circular import
        db_conn = get_db_connection()
        db_cursor = db_conn.cursor()
        logger.info("video_monitor: Database connection established")

        try:
            for person_id in duration_eyes_closed:
                user_id = person_ids[person_id]
                logger.debug(f"Eye Track Data: user_id={user_id}, person_id={person_id}, duration_eyes_closed={duration_eyes_closed[person_id]}, duration_looking_left={duration_looking_left[person_id]}, duration_looking_right={duration_looking_right[person_id]}, duration_looking_straight={duration_looking_straight[person_id]}, count_left={count_left[person_id]}, count_right={count_right[person_id]}, count_straight={count_straight[person_id]}")
                logger.debug(f"Executing SQL: INSERT INTO eye_track_data (user_id, Date, Person_ID, Duration_Eyes_Closed_s, Duration_Looking_Left_s, Duration_Looking_Right_s, Duration_Looking_Straight_s, Left_Counts, Right_Counts, Straight_Counts) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) with values ({user_id}, {datetime.now().date()}, {person_id}, {duration_eyes_closed[person_id]}, {duration_looking_left[person_id]}, {duration_looking_right[person_id]}, {duration_looking_straight[person_id]}, {count_left[person_id]}, {count_right[person_id]}, {count_straight[person_id]})")
                db_cursor.execute('''
                    INSERT INTO eye_track_data (user_id, Date, Person_ID, Duration_Eyes_Closed_s, Duration_Looking_Left_s, Duration_Looking_Right_s, Duration_Looking_Straight_s, Left_Counts, Right_Counts, Straight_Counts)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (user_id, datetime.now().date(), person_id, duration_eyes_closed[person_id], duration_looking_left[person_id],
                      duration_looking_right[person_id], duration_looking_straight[person_id], count_left[person_id],
                      count_right[person_id], count_straight[person_id]))
                logger.info(f"Inserted eye track data for {user_id}")

            for person_id in emotion_duration["angry"]:
                user_id = person_ids[person_id]
                logger.debug(f"Emotion Detect Data: user_id={user_id}, person_id={person_id}, angry={emotion_duration['angry'][person_id]}, sad={emotion_duration['sad'][person_id]}, happy={emotion_duration['happy'][person_id]}, fear={emotion_duration['fear'][person_id]}, disgust={emotion_duration['disgust'][person_id]}, neutral={emotion_duration['neutral'][person_id]}, surprise={emotion_duration['surprise'][person_id]}")
                logger.debug(f"Executing SQL: INSERT INTO emotion_detect_data (user_id, Date, Person_ID, Angry_s, Sad_s, Happy_s, Fear_s, Disgust_s, Neutral_s, Surprise_s) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) with values ({user_id}, {datetime.now().date()}, {person_id}, {emotion_duration['angry'][person_id]}, {emotion_duration['sad'][person_id]}, {emotion_duration['happy'][person_id]}, {emotion_duration['fear'][person_id]}, {emotion_duration['disgust'][person_id]}, {emotion_duration['neutral'][person_id]}, {emotion_duration['surprise'][person_id]})")
                db_cursor.execute('''
                    INSERT INTO emotion_detect_data (user_id, Date, Person_ID, Angry_s, Sad_s, Happy_s, Fear_s, Disgust_s, Neutral_s, Surprise_s)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (user_id, datetime.now().date(), person_id, emotion_duration["angry"][person_id], emotion_duration["sad"][person_id],
                      emotion_duration["happy"][person_id], emotion_duration["fear"][person_id],
                      emotion_duration["disgust"][person_id], emotion_duration["neutral"][person_id],
                      emotion_duration["surprise"][person_id]))
                logger.info(f"Inserted emotion detect data for {user_id}")

            for person_id in time_forward_seconds:
                user_id = person_ids[person_id]
                logger.debug(f"Head Pose Data: user_id={user_id}, person_id={person_id}, time_forward={time_forward_seconds[person_id]}, time_left={time_left_seconds[person_id]}, time_right={time_right_seconds[person_id]}, time_up={time_up_seconds[person_id]}, time_down={time_down_seconds[person_id]}")
                logger.debug(f"Executing SQL: INSERT INTO head_pose_data (user_id, Date, Person_ID, Looking_Forward_s, Looking_Left_s, Looking_Right_s, Looking_Up_s, Looking_Down_s) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) with values ({user_id}, {datetime.now().date()}, {person_id}, {time_forward_seconds[person_id]}, {time_left_seconds[person_id]}, {time_right_seconds[person_id]}, {time_up_seconds[person_id]}, {time_down_seconds[person_id]})")
                db_cursor.execute('''
                    INSERT INTO head_pose_data (user_id, Date, Person_ID, Looking_Forward_s, Looking_Left_s, Looking_Right_s, Looking_Up_s, Looking_Down_s)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (user_id, datetime.now().date(), person_id, time_forward_seconds[person_id], time_left_seconds[person_id],
                      time_right_seconds[person_id], time_up_seconds[person_id], time_down_seconds[person_id]))
                logger.info(f"Inserted head pose data for {user_id}")

            db_conn.commit()
            logger.debug("Data committed to the database.")
        except Exception as e:
            logger.error(f"Exception in database operation: {e}")
        finally:
            db_conn.close()
            logger.info("video_monitor: Database connection closed.")

