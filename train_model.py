import cv2
import pandas as pd
from datetime import datetime, timedelta

# Files
ATTENDANCE_FILE = "attendance/attendance.xlsx"
STUDENTS_FILE = "data/students.csv"

# Load student info
students = pd.read_csv(STUDENTS_FILE, sep="\t")
attendance_df = pd.read_excel(ATTENDANCE_FILE)

# Load face recognizer and cascade
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer/trainer.yml")
face_cascade = cv2.CascadeClassifier("haarcascade/haarcascade_frontalface_default.xml")

CONF_THRESHOLD = 85
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray,1.2,5)

    for (x,y,w,h) in faces:
        face = gray[y:y+h, x:x+w]
        rollno, conf = recognizer.predict(face)

        if conf < CONF_THRESHOLD:
            student = students[students["rollno"]==rollno]
            name = student["name"].values[0] if not student.empty else "Unknown"

            # Attendance check
            now = datetime.now()
            today = now.strftime("%Y-%m-%d")
            prev = attendance_df[(attendance_df["RollNo"]==rollno) & (attendance_df["Date"]==today)]

            if prev.empty or (now - datetime.strptime(prev.iloc[-1]["Time"], "%H:%M:%S")) >= timedelta(hours=1):
                attendance_df.loc[len(attendance_df)] = [rollno,name,today,now.strftime("%H:%M:%S"),"Present"]
                attendance_df.to_excel(ATTENDANCE_FILE,index=False)
                status = "Marked"
            else:
                status = "Reverified"

            label = f"{rollno} - {name} ({status})"
            color = (0,255,0)
        else:
            label = "Unknown"
            color = (0,0,255)

        cv2.rectangle(frame,(x,y),(x+w,y+h),color,2)
        cv2.putText(frame,label,(x,y-10),cv2.FONT_HERSHEY_SIMPLEX,0.8,color,2)

    cv2.imshow("Attendance", frame)
    if cv2.waitKey(1) & 0xFF==27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()
