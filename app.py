from flask import Flask, render_template, jsonify, Response, request, redirect
import cv2, os, time
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

# ---------------- PATHS ----------------
STUDENTS = "data/students.csv"
ATTENDANCE = "attendance/attendance.xlsx"
TRAINER = "trainer/trainer.yml"
CASCADE = "haarcascade/haarcascade_frontalface_default.xml"
DATASET = "dataset"

CONF_THRESHOLD = 85

# ---------------- LOAD DATA -------------
students = pd.read_csv(STUDENTS, sep="\t")
attendance_df = pd.read_excel(ATTENDANCE) if os.path.exists(ATTENDANCE) else pd.DataFrame(columns=["RollNo","Name","Date","Time","Status"])

# ------------ MODELS ----------------
face_cascade = cv2.CascadeClassifier(CASCADE)
recognizer = cv2.face.LBPHFaceRecognizer_create()
if os.path.exists(TRAINER):
    recognizer.read(TRAINER)

# -------------- DUPLICATION TRACKING ---------------
attendance_cache = {}  # NEW: Track last attendance time for each student
# Structure: {rollno: {"last_time": datetime, "date": "YYYY-MM-DD"}}

# ---------------- CAMERA ----------------
camera = None
latest_frame = None
last_detected = None   # MOST IMPORTANT

def get_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    return camera

# ---------------- ROUTES -------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/attendance")
def attendance_page():
    return render_template("attendance.html")

@app.route("/register")
def register():
    return render_template("register.html")

# ------------- VIDEO STREAM ----------------
def gen_frames():
    global latest_frame, last_detected

    cam = get_camera()
    while True:
        success, frame = cam.read()
        if not success:
            continue

        latest_frame = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        last_detected = None  # reset every frame

        for (x,y,w,h) in faces:
            face = gray[y:y+h, x:x+w]
            rollno, conf = recognizer.predict(face)

            if conf < CONF_THRESHOLD:
                student = students[students["rollno"] == rollno]
                if not student.empty:
                    name = student["name"].values[0]
                    last_detected = rollno  # SAVE ONLY
                    label = f"{rollno} - {name}"
                    color = (0,255,0)
                else:
                    label = "Unknown"
                    color = (0,0,255)
            else:
                label = "Unknown"
                color = (0,0,255)

            cv2.rectangle(frame,(x,y),(x+w,y+h),color,2)
            cv2.putText(frame,label,(x,y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.8,color,2)

        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame")

# ------------ MARK ATTENDANCE (FIXED) ----------------
@app.route("/mark-attendance")
def mark_attendance():
    global attendance_df, last_detected, attendance_cache

    if last_detected is None:
        return jsonify({"status":"fail","msg":"No face detected"})

    rollno = int(last_detected)
    student = students[students["rollno"] == rollno]
    name = student["name"].values[0]

    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    # FIXED LOGIC: Check last attendance time
    if rollno in attendance_cache:
        last_record = attendance_cache[rollno]
        last_date = last_record["date"]
        last_time = last_record["last_time"]
        
        # If same day and less than 1 hour difference
        if last_date == current_date:
            time_diff = now - last_time
            if time_diff < timedelta(hours=1):
                # This is RE-VERIFIED (not a duplicate to skip)
                return jsonify({
                    "status": "reverified", 
                    "name": name,
                    "time": current_time
                })
    
    # Mark new attendance
    new_entry = {
        "RollNo": rollno,
        "Name": name,
        "Date": current_date,
        "Time": current_time,
        "Status": "Present"
    }
    
    attendance_df = pd.concat([attendance_df, pd.DataFrame([new_entry])], ignore_index=True)
    attendance_df.to_excel(ATTENDANCE, index=False)
    
    # Update cache
    attendance_cache[rollno] = {
        "last_time": now,
        "date": current_date
    }
    
    return jsonify({
        "status": "success",
        "name": name,
        "time": current_time
    })

# ----------- FACE CAPTURE FOR REGISTRATION ----------------
@app.route("/capture-face")
def capture_face():
    rollno = request.args.get('rollno')
    if not rollno:
        return "Enter Roll No"
    
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    face_cascade = cv2.CascadeClassifier(CASCADE)
    
    # Create dataset folder for the student
    student_path = os.path.join(DATASET, str(rollno))
    if not os.path.exists(student_path):
        os.makedirs(student_path)
    
    count = 0
    while count < 100:  # Capture 100 images
        ret, frame = cam.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x,y,w,h) in faces:
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
            face_img = gray[y:y+h, x:x+w]
            face_path = os.path.join(student_path, f"{count}.jpg")
            cv2.imwrite(face_path, face_img)
            count += 1
        
        cv2.imshow('Capturing Face', frame)
        if cv2.waitKey(1) & 0xFF == 27 or count >= 100:
            break
    
    cam.release()
    cv2.destroyAllWindows()
    return f"Captured {count} images for Roll No: {rollno}"

# ---------------- SAVE STUDENT DETAILS ----------------
@app.route("/save-student", methods=["POST"])
def save_student():
    rollno = request.form['rollno']
    name = request.form['name']
    branch = request.form['branch']
    
    # Save to students.csv
    with open(STUDENTS, 'a') as f:
        f.write(f"{rollno}\t{name}\t{branch}\n")
    
    # Train the model
    train_model()
    
    return redirect("/")

# ---------------- TRAIN MODEL ----------------
def train_model():
    import numpy as np
    
    faces = []
    ids = []
    
    for foldername in os.listdir(DATASET):
        if foldername.isdigit():
            folder_path = os.path.join(DATASET, foldername)
            for filename in os.listdir(folder_path):
                if filename.endswith('.jpg'):
                    img_path = os.path.join(folder_path, filename)
                    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                    faces.append(img)
                    ids.append(int(foldername))
    
    if faces:
        recognizer.train(faces, np.array(ids))
        recognizer.write(TRAINER)
        print("Model trained successfully!")
    
    return "Model trained"

# ---------------- RUN ----------------
if __name__ == "__main__":
    # Initialize attendance cache from existing data
    if os.path.exists(ATTENDANCE):
        for _, row in attendance_df.iterrows():
            rollno = row['RollNo']
            date_str = row['Date']
            time_str = row['Time']
            
            try:
                dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
                attendance_cache[rollno] = {
                    "last_time": dt,
                    "date": date_str
                }
            except:
                pass
    
    app.run(debug=True)