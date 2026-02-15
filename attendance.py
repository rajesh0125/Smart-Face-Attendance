import cv2
import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta

# Paths
dataset_path = "dataset"
trainer_path = "trainer/trainer.yml"
students_file = "data/students.csv"
attendance_file = "attendance/attendance.xlsx"

# Load Haar Cascade
face_cascade = cv2.CascadeClassifier(
    "haarcascade/haarcascade_frontalface_default.xml"
)

# Load trained model
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(trainer_path)

# Load student info
students = pd.read_csv(students_file, sep="\t")  # rollno,name,branch

# Create attendance folder if not exists
if not os.path.exists("attendance"):
    os.makedirs("attendance")

# Load or create Excel file
if os.path.exists(attendance_file):
    attendance_df = pd.read_excel(attendance_file)
else:
    attendance_df = pd.DataFrame(columns=["RollNo","Name","Date","Time","Status"])

# Start webcam
cap = cv2.VideoCapture(0)
print("Press ESC to stop attendance capture...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

    for (x, y, w, h) in faces:
        face_img = gray[y:y+h, x:x+w]
        rollno, confidence = recognizer.predict(face_img)

        if confidence < 85:  # adjust threshold
            # Get student name
            student_row = students.loc[students["rollno"] == rollno]
            if student_row.empty:
                name = "Unknown"
            else:
                name = student_row["name"].values[0]

            # Attendance check
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")

            today_records = attendance_df[
                (attendance_df["RollNo"] == rollno) &
                (attendance_df["Date"] == date_str)
            ]

            mark_allowed = True

            if not today_records.empty:
                last_time_str = today_records.iloc[-1]["Time"]
                last_time = datetime.strptime(last_time_str, "%H:%M:%S")
                last_time = last_time.replace(
                    year=now.year, month=now.month, day=now.day
                )

                # STRICT 1 HOUR RULE
                if now - last_time < timedelta(hours=1):
                    mark_allowed = False
                    print(f"Re-Verified (within 1 hour): {rollno} - {name}")

            if mark_allowed:
                attendance_df = pd.concat([attendance_df, pd.DataFrame({
                    "RollNo":[rollno],
                    "Name":[name],
                    "Date":[date_str],
                    "Time":[time_str],
                    "Status":["Present"]
                })], ignore_index=True)

                print(f"Attendance marked: {rollno} - {name}")

            cv2.putText(
                frame,
                f"{rollno} {name}",
                (x, y-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0,255,0),
                2
            )
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)

        else:
            cv2.putText(
                frame,
                "Unknown",
                (x, y-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0,0,255),
                2
            )
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,0,255), 2)

    cv2.imshow("Attendance", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC key
        break

# Save Excel
attendance_df.to_excel(attendance_file, index=False)
cap.release()
cv2.destroyAllWindows()
print("Attendance capture completed ✅")
