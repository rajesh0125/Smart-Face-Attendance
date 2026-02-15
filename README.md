📚 Smart Attendance System with Face Recognition
A modern, AI-powered attendance management system using facial recognition. Built with Python Flask, OpenCV, and Bootstrap 5.
<img width="1497" height="891" alt="Screenshot 2026-02-14 023037" src="https://github.com/user-attachments/assets/69eca9c7-1b6d-4ce9-ac43-844d945c3164" />
<img width="1254" height="884" alt="Screenshot 2026-02-14 023235" src="https://github.com/user-attachments/assets/8c8d3bbb-e142-4f2e-87e0-d8738f4de386" />
<img width="848" height="628" alt="Screenshot 2026-02-14 023253" src="https://github.com/user-attachments/assets/5f1a0f82-f13d-45bf-b7e6-5eb64cac7e2f" />
<img width="1218" height="720" alt="Screenshot 2026-02-14 023317" src="https://github.com/user-attachments/assets/1bb5c896-99b2-459f-8e1a-8cf27709c0ad" />

✨ Key Features
Feature	Description
Face Recognition	Real-time detection using LBPH algorithm
Admin Security	Password-protected registration (admin123)
Attendance Rules	1-hour cooldown policy prevents duplicates
Auto Training	Model retrains automatically after registration
Excel Export	Attendance saved in Excel format
Modern UI	Glass morphism design, responsive, animations

🛠️ Tech Stack
text
Backend:  Python Flask, OpenCV, Pandas
Frontend: Bootstrap 5, Font Awesome, AOS
Database: CSV (students), Excel (attendance)

📁 Quick Structure
smart-attendance/
│
├── app.py                 # Main application
├── templates/             # HTML files
│   ├── index.html        # Home page
│   ├── attendance.html    # Mark attendance
│   └── register.html      # Student registration
│
├── dataset/               # Face samples (auto)
├── trainer/trainer.yml    # Trained model
├── data/students.csv      # Student database
└── attendance/attendance.xlsx  # Records

# Clone & install
git clone https://github.com/yourusername/smart-attendance.git
cd smart-attendance
pip install flask opencv-python opencv-contrib-python pandas openpyxl

**Install proper libararies for this dependency**
Numpy
pandas
flask
openCv

# Run
python app.py

# Open browser
http://localhost:5000
🎯 How to Use
Register Student (Admin only)
Click "Register Student"

Enter password: admin123
Fill details (Roll No, Name, Branch)
Click "Capture Face" (100 samples)
Click "Save"

Mark Attendance
Click "Mark Attendance"
Student looks at camera
Click "Scan & Mark Attendance"
Get status: ✅ Success / 🔄 Already / ❌ Unknown

⚙️ Key Configurations
Setting	Location	Default
Admin Password	register.html	admin123
Cooldown Period	app.py	1 hour
Confidence Threshold	app.py	85

🔑 Default Credentials
Admin Password: admin123

📊 Output Files
students.csv - Student database
attendance.xlsx - Daily attendance records
trainer.yml - Trained face model

🌟 Why This System?
✅ Real-time recognition
✅ Duplicate prevention
✅ Auto model training
✅ Professional UI
✅ Easy to deploy
✅ No cloud required

📱 Responsive Design
Works perfectly on:

💻 Desktop
📱 Mobile
📟 Tablet

Made with ❤️ for smarter attendance management
