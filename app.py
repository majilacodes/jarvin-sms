from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
from datetime import date, timedelta
import re
import os
import sys
    
app = Flask(__name__)

app.secret_key = 'abcd21234455'  
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
app.config['SESSION_TYPE'] = 'filesystem'

# Database initialization function
def get_db():
    db = sqlite3.connect('python_sms.db')
    db.row_factory = sqlite3.Row
    return db

# Initialize the database schema
def init_db():
    print("Initializing database...")
    db = get_db()
    cursor = db.cursor()
    
    # Create tables
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS sms_user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            type TEXT,
            status TEXT
        );

        CREATE TABLE IF NOT EXISTS sms_teacher (
            teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher TEXT,
            subject_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS sms_subjects (
            subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            type TEXT,
            code TEXT
        );

        CREATE TABLE IF NOT EXISTS sms_section (
            section_id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT
        );

        CREATE TABLE IF NOT EXISTS sms_classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            code TEXT,
            section INTEGER,
            teacher_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS sms_students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admission_no TEXT,
            roll_no TEXT,
            name TEXT,
            photo TEXT,
            gender TEXT,
            dob TEXT,
            mobile TEXT,
            email TEXT,
            current_address TEXT,
            father_name TEXT,
            mother_name TEXT,
            admission_date TEXT,
            academic_year TEXT,
            class INTEGER,
            section INTEGER
        );

        CREATE TABLE IF NOT EXISTS sms_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            attendance_status TEXT,
            attendance_date DATE
        );

        -- Exam Types (e.g., Midterm, Final, Quiz)
        CREATE TABLE IF NOT EXISTS sms_exam_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        );

        -- Exams
        CREATE TABLE IF NOT EXISTS sms_exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_type_id INTEGER,
            class_id INTEGER,
            subject_id INTEGER,
            exam_date DATE,
            total_marks INTEGER,
            passing_marks INTEGER,
            academic_year TEXT,
            status TEXT DEFAULT 'upcoming',
            FOREIGN KEY (exam_type_id) REFERENCES sms_exam_types(id),
            FOREIGN KEY (class_id) REFERENCES sms_classes(id),
            FOREIGN KEY (subject_id) REFERENCES sms_subjects(subject_id)
        );

        -- Student Exam Results
        CREATE TABLE IF NOT EXISTS sms_exam_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER,
            student_id INTEGER,
            marks_obtained DECIMAL(5,2),
            grade TEXT,
            remarks TEXT,
            date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (exam_id) REFERENCES sms_exams(id),
            FOREIGN KEY (student_id) REFERENCES sms_students(id)
        );
    ''')
    
    # Check if code column exists
    cursor.execute("PRAGMA table_info(sms_classes)")
    columns = cursor.fetchall()
    code_exists = any(column[1] == 'code' for column in columns)
    
    # Add code column if it doesn't exist
    if not code_exists:
        try:
            cursor.execute('ALTER TABLE sms_classes ADD COLUMN code TEXT')
            db.commit()
        except:
            pass  # Column might already exist
    
    # Insert default exam types if they don't exist
    cursor.execute('SELECT COUNT(*) FROM sms_exam_types')
    if cursor.fetchone()[0] == 0:
        cursor.executescript('''
            INSERT INTO sms_exam_types (name, description) VALUES 
            ('Midterm', 'Mid-semester examination'),
            ('Final', 'End of semester examination'),
            ('Quiz', 'Short assessment test'),
            ('Assignment', 'Homework/Project assessment');
        ''')
    
    # Add sample data only if tables are empty
    
    # 1. Add users (admin + faculty)
    cursor.execute('SELECT COUNT(*) FROM sms_user')
    user_count = cursor.fetchone()[0]
    print(f"Current user count: {user_count}")
    
    if user_count == 0:
        print("Creating admin user...")
        cursor.executescript('''
            INSERT INTO sms_user (first_name, email, password, type, status) VALUES 
            ('Admin', 'admin@college.ac.in', 'admin123', 'admin', 'active'),
            ('Dr. Rajesh Kumar', 'rajesh.kumar@college.ac.in', 'faculty123', 'teacher', 'active'),
            ('Dr. Priya Sharma', 'priya.sharma@college.ac.in', 'faculty123', 'teacher', 'active'),
            ('Prof. Amit Patel', 'amit.patel@college.ac.in', 'faculty123', 'teacher', 'active'),
            ('Dr. Sunita Verma', 'sunita.verma@college.ac.in', 'faculty123', 'teacher', 'active'),
            ('Prof. Deepak Singh', 'deepak.singh@college.ac.in', 'faculty123', 'teacher', 'active');
        ''')

    # 2. Add engineering subjects
    cursor.execute('SELECT COUNT(*) FROM sms_subjects')
    if cursor.fetchone()[0] == 0:
        cursor.executescript('''
            INSERT INTO sms_subjects (subject, type, code) VALUES 
            ('Data Structures', 'Core', 'CS201'),
            ('Digital Electronics', 'Core', 'EC201'),
            ('Engineering Mathematics', 'Core', 'MA201'),
            ('Computer Networks', 'Core', 'CS301'),
            ('Database Management', 'Core', 'CS302'),
            ('Machine Learning', 'Elective', 'CS401'),
            ('Artificial Intelligence', 'Elective', 'CS402'),
            ('VLSI Design', 'Core', 'EC301'),
            ('Operating Systems', 'Core', 'CS303'),
            ('Software Engineering', 'Core', 'CS304'),
            ('Web Technologies', 'Elective', 'CS403'),
            ('Cloud Computing', 'Elective', 'CS404'),
            ('Cyber Security', 'Elective', 'CS405'),
            ('IoT Systems', 'Elective', 'EC401'),
            ('Microprocessors', 'Core', 'EC202'),
            ('Computer Architecture', 'Core', 'CS202'),
            ('Theory of Computation', 'Core', 'CS305'),
            ('Compiler Design', 'Core', 'CS306'),
            ('Data Mining', 'Elective', 'CS406'),
            ('Mobile Computing', 'Elective', 'CS407');
        ''')

    # 3. Add sections
    cursor.execute('SELECT COUNT(*) FROM sms_section')
    if cursor.fetchone()[0] == 0:
        cursor.executescript('''
            INSERT INTO sms_section (section) VALUES 
            ('A'), ('B'), ('C'), ('D'), ('E');
        ''')

    # 4. Add faculty members
    cursor.execute('SELECT COUNT(*) FROM sms_teacher')
    if cursor.fetchone()[0] == 0:
        cursor.executescript('''
            INSERT INTO sms_teacher (teacher, subject_id) VALUES 
            ('Dr. Rajesh Kumar', 1),
            ('Dr. Priya Sharma', 2),
            ('Prof. Amit Patel', 3),
            ('Dr. Sunita Verma', 4),
            ('Prof. Deepak Singh', 5),
            ('Dr. Anita Desai', 6),
            ('Prof. Suresh Yadav', 7),
            ('Dr. Meena Iyer', 8),
            ('Prof. Rakesh Gupta', 9),
            ('Dr. Neha Kapoor', 10),
            ('Prof. Vikram Singh', 11),
            ('Dr. Anjali Mehta', 12),
            ('Prof. Sanjay Verma', 13),
            ('Dr. Pooja Reddy', 14),
            ('Prof. Arun Kumar', 15),
            ('Dr. Kavita Sharma', 16),
            ('Prof. Rahul Mishra', 17),
            ('Dr. Shweta Joshi', 18),
            ('Prof. Manoj Tiwari', 19),
            ('Dr. Ritu Patel', 20);
        ''')

    # 5. Add engineering classes/branches
    cursor.execute('SELECT COUNT(*) FROM sms_classes')
    if cursor.fetchone()[0] == 0:
        cursor.executescript('''
            INSERT INTO sms_classes (name, code, section, teacher_id) VALUES 
            ('CSE 1st Year', 'CSE1', 1, 1),
            ('CSE 2nd Year', 'CSE2', 2, 2),
            ('CSE 3rd Year', 'CSE3', 3, 3),
            ('CSE 4th Year', 'CSE4', 4, 4),
            ('ECE 1st Year', 'ECE1', 1, 5),
            ('ECE 2nd Year', 'ECE2', 2, 6),
            ('ECE 3rd Year', 'ECE3', 3, 7),
            ('ECE 4th Year', 'ECE4', 4, 8),
            ('IT 1st Year', 'IT1', 1, 9),
            ('IT 2nd Year', 'IT2', 2, 10),
            ('IT 3rd Year', 'IT3', 3, 11),
            ('IT 4th Year', 'IT4', 4, 12),
            ('ME 1st Year', 'ME1', 1, 13),
            ('ME 2nd Year', 'ME2', 2, 14),
            ('ME 3rd Year', 'ME3', 3, 15),
            ('ME 4th Year', 'ME4', 4, 16),
            ('EE 1st Year', 'EE1', 1, 17),
            ('EE 2nd Year', 'EE2', 2, 18),
            ('EE 3rd Year', 'EE3', 3, 19),
            ('EE 4th Year', 'EE4', 4, 20);
        ''')

    # 6. Add students
    cursor.execute('SELECT COUNT(*) FROM sms_students')
    if cursor.fetchone()[0] == 0:
        cursor.executescript('''
            INSERT INTO sms_students (
                admission_no, roll_no, name, gender, dob, mobile, email,
                current_address, father_name, mother_name, admission_date,
                academic_year, class, section
            ) VALUES 
            ('2023CSE001', '001', 'Aarav Sharma', 'Male', '2003-05-15', '9876543210', 'aarav.s@college.ac.in', 'Mumbai, Maharashtra', 'Rajesh Sharma', 'Priya Sharma', '2023-08-01', '2023-24', 1, 1),
            ('2023CSE002', '002', 'Diya Patel', 'Female', '2003-06-20', '9876543211', 'diya.p@college.ac.in', 'Ahmedabad, Gujarat', 'Amit Patel', 'Meena Patel', '2023-08-01', '2023-24', 1, 1),
            ('2023CSE003', '003', 'Arjun Singh', 'Male', '2003-07-10', '9876543212', 'arjun.s@college.ac.in', 'Delhi, Delhi', 'Vikram Singh', 'Anjali Singh', '2023-08-01', '2023-24', 1, 2),
            ('2023ECE001', '004', 'Ananya Kumar', 'Female', '2003-08-25', '9876543213', 'ananya.k@college.ac.in', 'Bangalore, Karnataka', 'Deepak Kumar', 'Sunita Kumar', '2023-08-01', '2023-24', 5, 1),
            ('2023ECE002', '005', 'Rohan Verma', 'Male', '2003-09-30', '9876543214', 'rohan.v@college.ac.in', 'Chennai, Tamil Nadu', 'Suresh Verma', 'Pooja Verma', '2023-08-01', '2023-24', 5, 1),
            ('2023IT001', '006', 'Ishaan Mehta', 'Male', '2003-10-15', '9876543215', 'ishaan.m@college.ac.in', 'Pune, Maharashtra', 'Rahul Mehta', 'Neha Mehta', '2023-08-01', '2023-24', 9, 1),
            ('2023IT002', '007', 'Zara Khan', 'Female', '2003-11-20', '9876543216', 'zara.k@college.ac.in', 'Hyderabad, Telangana', 'Imran Khan', 'Fatima Khan', '2023-08-01', '2023-24', 9, 1),
            ('2023ME001', '008', 'Vihaan Reddy', 'Male', '2003-12-05', '9876543217', 'vihaan.r@college.ac.in', 'Kolkata, West Bengal', 'Krishna Reddy', 'Lakshmi Reddy', '2023-08-01', '2023-24', 13, 1),
            ('2023ME002', '009', 'Aisha Gupta', 'Female', '2004-01-10', '9876543218', 'aisha.g@college.ac.in', 'Jaipur, Rajasthan', 'Sanjay Gupta', 'Ritu Gupta', '2023-08-01', '2023-24', 13, 1),
            ('2023EE001', '010', 'Kabir Joshi', 'Male', '2004-02-15', '9876543219', 'kabir.j@college.ac.in', 'Lucknow, UP', 'Anil Joshi', 'Shweta Joshi', '2023-08-01', '2023-24', 17, 1),
            ('2022CSE001', '011', 'Myra Singh', 'Female', '2002-03-20', '9876543220', 'myra.s@college.ac.in', 'Chandigarh, Punjab', 'Harpreet Singh', 'Gurpreet Kaur', '2022-08-01', '2023-24', 2, 2),
            ('2022ECE001', '012', 'Advait Mishra', 'Male', '2002-04-25', '9876543221', 'advait.m@college.ac.in', 'Bhopal, MP', 'Rajiv Mishra', 'Anjali Mishra', '2022-08-01', '2023-24', 6, 2),
            ('2022IT001', '013', 'Kiara Kapoor', 'Female', '2002-05-30', '9876543222', 'kiara.k@college.ac.in', 'Indore, MP', 'Arun Kapoor', 'Priya Kapoor', '2022-08-01', '2023-24', 10, 2),
            ('2021CSE001', '014', 'Reyansh Kumar', 'Male', '2001-06-05', '9876543223', 'reyansh.k@college.ac.in', 'Patna, Bihar', 'Manoj Kumar', 'Seema Kumar', '2021-08-01', '2023-24', 3, 3),
            ('2021ECE001', '015', 'Shanaya Iyer', 'Female', '2001-07-10', '9876543224', 'shanaya.i@college.ac.in', 'Trivandrum, Kerala', 'Krishnan Iyer', 'Meena Iyer', '2021-08-01', '2023-24', 7, 3),
            ('2021IT001', '016', 'Vivaan Malhotra', 'Male', '2001-08-15', '9876543225', 'vivaan.m@college.ac.in', 'Nagpur, Maharashtra', 'Rohit Malhotra', 'Pooja Malhotra', '2021-08-01', '2023-24', 11, 3),
            ('2020CSE001', '017', 'Anvi Desai', 'Female', '2000-09-20', '9876543226', 'anvi.d@college.ac.in', 'Surat, Gujarat', 'Mihir Desai', 'Rekha Desai', '2020-08-01', '2023-24', 4, 4),
            ('2020ECE001', '018', 'Dhruv Chatterjee', 'Male', '2000-10-25', '9876543227', 'dhruv.c@college.ac.in', 'Guwahati, Assam', 'Abhijit Chatterjee', 'Mitali Chatterjee', '2020-08-01', '2023-24', 8, 4),
            ('2020IT001', '019', 'Saanvi Rao', 'Female', '2000-11-30', '9876543228', 'saanvi.r@college.ac.in', 'Visakhapatnam, AP', 'Venkat Rao', 'Padma Rao', '2020-08-01', '2023-24', 12, 4),
            ('2020ME001', '020', 'Yash Tiwari', 'Male', '2000-12-05', '9876543229', 'yash.t@college.ac.in', 'Raipur, Chhattisgarh', 'Prakash Tiwari', 'Savita Tiwari', '2020-08-01', '2023-24', 16, 4);
        ''')

    # 7. Add attendance records (for last 30 days)
    cursor.execute('SELECT COUNT(*) FROM sms_attendance')
    if cursor.fetchone()[0] == 0:
        # Get current date and generate dates for last 30 days
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        for student_id in range(1, 21):
            current_date = start_date
            while current_date <= end_date:
                # Create realistic attendance patterns
                if student_id % 5 == 0:  # Students with poor attendance (80%)
                    status = 'present' if current_date.weekday() < 4 else 'absent'
                elif student_id % 3 == 0:  # Students with excellent attendance (95%)
                    status = 'absent' if current_date.weekday() == 4 and current_date.day % 15 == 0 else 'present'
                else:  # Regular students (90%)
                    status = 'absent' if current_date.weekday() == 4 and current_date.day % 10 == 0 else 'present'
                
                # Don't mark attendance for weekends
                if current_date.weekday() < 5:  # Monday to Friday
                    cursor.execute('''
                        INSERT INTO sms_attendance (student_id, attendance_status, attendance_date)
                        VALUES (?, ?, ?)
                    ''', (student_id, status, current_date.strftime('%Y-%m-%d')))
                
                current_date += timedelta(days=1)

    # 8. Add comprehensive exam records
    cursor.execute('SELECT COUNT(*) FROM sms_exam_results')
    if cursor.fetchone()[0] == 0:
        # First add more exam types if not exists
        cursor.executescript('''
            INSERT OR IGNORE INTO sms_exam_types (name, description) VALUES 
            ('Lab Test', 'Practical laboratory examination'),
            ('Project Review', 'Project progress evaluation'),
            ('Viva', 'Oral examination');
        ''')
        
        # Add various types of exams
        cursor.executescript('''
            -- Midterm Exams (Multiple subjects)
            INSERT INTO sms_exams (exam_type_id, class_id, subject_id, exam_date, total_marks, passing_marks, academic_year, status) VALUES 
            (1, 1, 1, '2024-02-01', 100, 40, '2023-24', 'upcoming'),
            (1, 1, 2, '2024-02-03', 100, 40, '2023-24', 'upcoming'),
            (1, 1, 3, '2024-02-05', 100, 40, '2023-24', 'upcoming'),
            (1, 2, 4, '2024-02-07', 100, 40, '2023-24', 'upcoming'),
            (1, 2, 5, '2024-02-09', 100, 40, '2023-24', 'upcoming'),
            (1, 3, 6, '2024-02-11', 100, 40, '2023-24', 'upcoming'),
            (1, 3, 7, '2024-02-13', 100, 40, '2023-24', 'upcoming'),
            (1, 4, 8, '2024-02-15', 100, 40, '2023-24', 'upcoming');
        ''')

        # Add Lab Tests
        cursor.executescript('''
            INSERT INTO sms_exams (exam_type_id, class_id, subject_id, exam_date, total_marks, passing_marks, academic_year, status) VALUES 
            (5, 1, 1, '2024-01-05', 50, 25, '2023-24', 'completed'),
            (5, 1, 2, '2024-01-12', 50, 25, '2023-24', 'completed'),
            (5, 2, 3, '2024-01-19', 50, 25, '2023-24', 'completed'),
            (5, 2, 4, '2024-01-26', 50, 25, '2023-24', 'completed');
        ''')

        # Add Project Reviews
        cursor.executescript('''
            INSERT INTO sms_exams (exam_type_id, class_id, subject_id, exam_date, total_marks, passing_marks, academic_year, status) VALUES 
            (6, 3, 5, '2024-01-08', 100, 50, '2023-24', 'completed'),
            (6, 3, 6, '2024-01-15', 100, 50, '2023-24', 'completed'),
            (6, 4, 7, '2024-01-22', 100, 50, '2023-24', 'completed'),
            (6, 4, 8, '2024-01-29', 100, 50, '2023-24', 'completed');
        ''')

        # Function to generate realistic marks based on student pattern
        def get_student_performance(student_id, total_marks):
            base_performance = {
                0: (0.85, 0.95),  # Excellent students (85-95%)
                1: (0.75, 0.85),  # Good students (75-85%)
                2: (0.65, 0.75),  # Average students (65-75%)
                3: (0.55, 0.65)   # Below average students (55-65%)
            }
            import random
            performance_range = base_performance[student_id % 4]
            percentage = random.uniform(performance_range[0], performance_range[1])
            return round(total_marks * percentage)

        # Add results for completed exams
        for exam_id in range(1, 13):  # For all completed exams
            for student_id in range(1, 21):  # For all 20 students
                # Get exam details
                cursor.execute('SELECT total_marks FROM sms_exams WHERE id = ?', (exam_id,))
                exam = cursor.fetchone()
                if exam:
                    total_marks = exam[0]
                    marks = get_student_performance(student_id, total_marks)
                    
                    # Calculate grade based on percentage
                    percentage = (marks / total_marks) * 100
                    if percentage >= 90:
                        grade = 'A+'
                        remarks = 'Outstanding performance'
                    elif percentage >= 80:
                        grade = 'A'
                        remarks = 'Excellent work'
                    elif percentage >= 70:
                        grade = 'B+'
                        remarks = 'Very good performance'
                    elif percentage >= 60:
                        grade = 'B'
                        remarks = 'Good effort'
                    elif percentage >= 50:
                        grade = 'C'
                        remarks = 'Average performance'
                    else:
                        grade = 'F'
                        remarks = 'Needs improvement'

                    cursor.execute('''
                        INSERT INTO sms_exam_results 
                        (exam_id, student_id, marks_obtained, grade, remarks)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (exam_id, student_id, marks, grade, remarks))

        # Add some special remarks for random students
        special_remarks = [
            "Exceptional problem-solving skills",
            "Shows great improvement",
            "Needs to focus more on practical aspects",
            "Outstanding project implementation",
            "Good theoretical understanding",
            "Excellent laboratory work",
            "Needs more practice with coding",
            "Shows leadership qualities",
            "Very creative approach to problems",
            "Good team player"
        ]
        
        import random
        for student_id in range(1, 21):
            # Update random exam results with special remarks
            for _ in range(2):  # 2 special remarks per student
                exam_id = random.randint(1, 12)
                remark = random.choice(special_remarks)
                cursor.execute('''
                    UPDATE sms_exam_results 
                    SET remarks = ? 
                    WHERE student_id = ? AND exam_id = ?
                ''', (remark, student_id, exam_id))

    # Verify admin user creation
    cursor.execute('SELECT COUNT(*) FROM sms_user')
    user_count = cursor.fetchone()[0]
    print(f"Current user count: {user_count}")
    
    if user_count == 0:
        print("Creating admin user...")
        cursor.execute('''
            INSERT INTO sms_user (first_name, email, password, type, status) 
            VALUES (?, ?, ?, ?, ?)
        ''', ('Admin', 'admin@college.ac.in', 'admin123', 'admin', 'active'))
        db.commit()
        print("Admin user created successfully")

    db.commit()
    db.close()

# Initialize the database on startup
init_db()

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any existing session
    session.clear()
    
    message = ''
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            
            # Debug print
            print(f"Login attempt - Email: {email}")
            
            if not email or not password:
                message = 'Please fill both email and password fields!'
                return render_template('login.html', message=message)
            
            db = get_db()
            cursor = db.cursor()
            
            # Debug print
            cursor.execute('SELECT COUNT(*) FROM sms_user')
            total_users = cursor.fetchone()[0]
            print(f"Total users in database: {total_users}")
            
            # Check if user exists
            cursor.execute('SELECT * FROM sms_user WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if user:
                # Debug print
                print(f"User found: {user['first_name']}")
                
                # Check password
                if user['password'] == password:
                    # Set session variables
                    session['loggedin'] = True
                    session['userid'] = user['id']
                    session['name'] = user['first_name']
                    session['email'] = user['email']
                    session['role'] = user['type']
                    
                    # Debug print
                    print(f"Session variables set: {session}")
                    
                    db.close()
                    return redirect(url_for('dashboard'))
                else:
                    message = 'Incorrect password!'
            else:
                message = 'Email not found!'
                
        except Exception as e:
            message = f'An error occurred: {str(e)}'
            print(f"Login error: {str(e)}")  # For debugging
            
        finally:
            if 'db' in locals():
                db.close()
            
    return render_template('login.html', message=message)

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    # Redirect to login page
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    # Debug print
    print(f"Dashboard access - Session: {session}")
    
    if 'loggedin' not in session:
        print("No login session found")
        return redirect(url_for('login'))
        
    return render_template('dashboard.html')

########################### Techer section ##################################

@app.route("/teacher", methods =['GET', 'POST'])
def teacher():
    if 'loggedin' in session:   
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT t.teacher_id, t.teacher, s.subject 
            FROM sms_teacher t 
            LEFT JOIN sms_subjects s ON s.subject_id = t.subject_id
        ''')
        teachers = cursor.fetchall()
        
        cursor.execute('SELECT * FROM sms_subjects')
        subjects = cursor.fetchall()  
        db.close()
        return render_template("teacher.html", teachers = teachers, subjects = subjects)
    return redirect(url_for('login')) 
    
@app.route("/edit_teacher", methods =['GET'])
def edit_teacher():
    if 'loggedin' in session:
        teacher_id = request.args.get('teacher_id') 
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT t.teacher_id, t.teacher, s.subject FROM sms_teacher t LEFT JOIN sms_subjects s ON s.subject_id = t.subject_id WHERE t.teacher_id = ?', (teacher_id,))
        teachers = cursor.fetchall() 
        
        cursor.execute('SELECT * FROM sms_subjects')
        subjects = cursor.fetchall()  
        
        db.close()
        return render_template("edit_teacher.html", teachers = teachers, subjects = subjects)
    return redirect(url_for('login'))  
    
@app.route("/save_teacher", methods=['GET', 'POST'])
def save_teacher():
    if 'loggedin' in session:    
        if request.method == 'POST' and 'techer_name' in request.form and 'specialization' in request.form:
            teacher_name = request.form['techer_name'].strip()
            specialization = request.form['specialization']
            
            if not teacher_name:
                return redirect(url_for('teacher'))
                
            db = get_db()
            cursor = db.cursor()
            
            try:
                if request.form['action'] == 'updateTeacher':
                    teacherid = request.form['teacherid']
                    cursor.execute('''
                        UPDATE sms_teacher 
                        SET teacher = ?, subject_id = ? 
                        WHERE teacher_id = ?''',
                        (teacher_name, specialization, teacherid))
                else:
                    cursor.execute('''
                        INSERT INTO sms_teacher (teacher, subject_id) 
                        VALUES (?, ?)''',
                        (teacher_name, specialization))
                
                db.commit()
            except Exception as e:
                print(f"Error saving teacher: {e}")
            finally:
                db.close()
                
            return redirect(url_for('teacher'))
                
    return redirect(url_for('login'))
    
@app.route("/delete_teacher", methods =['GET'])
def delete_teacher():
    if 'loggedin' in session:
        teacher_id = request.args.get('teacher_id') 
        db = get_db()
        cursor = db.cursor()
        cursor.execute('DELETE FROM sms_teacher WHERE teacher_id = ?', (teacher_id, ))
        db.commit()   
        db.close()
        return redirect(url_for('teacher'))
    return redirect(url_for('login'))
    
########################### SUBJECT ##################################
    
@app.route("/subject", methods =['GET', 'POST'])
def subject():
    if 'loggedin' in session:       
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM sms_subjects')
        subjects = cursor.fetchall()          
        db.close()
        return render_template("subject.html", subjects = subjects)
    return redirect(url_for('login'))
    
@app.route("/save_subject", methods=['GET', 'POST'])
def save_subject():
    if 'loggedin' in session:    
        if request.method == 'POST' and 'subject' in request.form and 's_type' in request.form and 'code' in request.form:
            subject = request.form['subject'].strip()
            s_type = request.form['s_type'].strip()
            code = request.form['code'].strip()
            
            if not all([subject, s_type, code]):
                return redirect(url_for('subject'))
                
            db = get_db()
            cursor = db.cursor()        
            
            try:
                if request.form['action'] == 'updateSubject':
                    subjectid = request.form['subjectid']
                    cursor.execute('''
                        UPDATE sms_subjects 
                        SET subject = ?, type = ?, code = ? 
                        WHERE subject_id = ?''', 
                        (subject, s_type, code, subjectid))
                else:
                    cursor.execute('''
                        INSERT INTO sms_subjects (subject, type, code) 
                        VALUES (?, ?, ?)''', 
                        (subject, s_type, code))
                
                db.commit()
            except Exception as e:
                print(f"Error saving subject: {e}")
            finally:
                db.close()
                
            return redirect(url_for('subject'))
                    
    return redirect(url_for('login'))

@app.route("/edit_subject", methods =['GET'])
def edit_subject():
    if 'loggedin' in session:
        subject_id = request.args.get('subject_id') 
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT subject_id, subject, type, code FROM sms_subjects WHERE subject_id = ?', (subject_id,))
        subjects = cursor.fetchall() 
        db.close()
        return render_template("edit_subject.html", subjects = subjects)
    return redirect(url_for('login'))    
    
@app.route("/delete_subject", methods =['GET'])
def delete_subject():
    if 'loggedin' in session:
        subject_id = request.args.get('subject_id') 
        db = get_db()
        cursor = db.cursor()
        cursor.execute('DELETE FROM sms_subjects WHERE subject_id = ?', (subject_id, ))
        db.commit()   
        db.close()
        return redirect(url_for('subject'))
    return redirect(url_for('login'))

################################ Classes  #######################################

@app.route("/classes", methods=['GET', 'POST'])
def classes():
    if 'loggedin' in session:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id as class_id, name, COALESCE(code, "") as code FROM sms_classes')
        classes = cursor.fetchall()
        db.close()
        return render_template("classes.html", classes=classes)
    return redirect(url_for('login'))

@app.route("/edit_class", methods =['GET'])
def edit_class():
    if 'loggedin' in session:
        class_id = request.args.get('class_id') 
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT c.id, c.name, s.section, t.teacher FROM sms_classes c LEFT JOIN sms_section s ON s.section_id = c.section LEFT JOIN sms_teacher t ON t.teacher_id = c.teacher_id WHERE c.id = ?', (class_id,))
        classes = cursor.fetchall() 
        
        cursor.execute('SELECT * FROM sms_section')
        sections = cursor.fetchall() 
        
        cursor.execute('SELECT * FROM sms_teacher')
        teachers = cursor.fetchall()
        
        db.close()
        return render_template("edit_class.html", classes = classes, sections = sections, teachers = teachers)
    return redirect(url_for('login'))  

@app.route("/save_class", methods =['GET', 'POST'])
def save_class():
    if 'loggedin' in session:    
        db = get_db()
        cursor = db.cursor()        
        if request.method == 'POST' and 'cname' in request.form:
            cname = request.form['cname'] 
            sectionid = request.form['sectionid']
            teacherid = request.form['teacherid']            
            action = request.form['action']             
            
            if action == 'updateClass':
                class_id = request.form['classid'] 
                cursor.execute('UPDATE sms_classes SET name = ?, section = ?, teacher_id = ? WHERE id  =?', (cname, sectionid, teacherid, class_id))
            else: 
                cursor.execute('INSERT INTO sms_classes (name, section, teacher_id) VALUES (?, ?, ?)', (cname, sectionid, teacherid))
            
            db.commit()
            db.close()
            return redirect(url_for('classes'))        
        elif request.method == 'POST':
            msg = 'Please fill out the form field !'        
        return redirect(url_for('classes'))        
    return redirect(url_for('login'))
    

@app.route("/delete_class", methods =['GET'])
def delete_class():
    if 'loggedin' in session:
        class_id = request.args.get('class_id') 
        db = get_db()
        cursor = db.cursor()
        cursor.execute('DELETE FROM sms_classes WHERE id = ?', (class_id,))
        db.commit()   
        db.close()
        return redirect(url_for('classes'))
    return redirect(url_for('login'))     

########################### SECTIONS ##################################

@app.route("/sections", methods =['GET', 'POST'])
def sections():
    if 'loggedin' in session:      
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM sms_section')
        sections = cursor.fetchall()          
        db.close()
        return render_template("sections.html", sections = sections)
    return redirect(url_for('login')) 
    
@app.route("/edit_sections", methods =['GET'])
def edit_sections():
    if 'loggedin' in session:
        section_id = request.args.get('section_id') 
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM sms_section WHERE section_id = ?', (section_id,))
        sections = cursor.fetchall() 
        db.close()
        return render_template("edit_section.html", sections = sections)
    return redirect(url_for('login'))    
    
@app.route("/save_sections", methods =['GET', 'POST'])
def save_sections():
    if 'loggedin' in session:    
        db = get_db()
        cursor = db.cursor()        
        if request.method == 'POST' and 'section_name' in request.form:
            section_name = request.form['section_name']                         
            action = request.form['action']             
            
            if action == 'updateSection':
                section_id = request.form['sectionid'] 
                cursor.execute('UPDATE sms_section SET section = ? WHERE section_id  =?', (section_name, section_id))
            else: 
                cursor.execute('INSERT INTO sms_section (section) VALUES (?)', (section_name, ))
            
            db.commit()
            db.close()
            return redirect(url_for('sections'))        
        elif request.method == 'POST':
            msg = 'Please fill out the form field !'        
        return redirect(url_for('sections'))        
    return redirect(url_for('login')) 
    
@app.route("/delete_sections", methods =['GET'])
def delete_sections():
    if 'loggedin' in session:
        section_id = request.args.get('section_id') 
        db = get_db()
        cursor = db.cursor()
        cursor.execute('DELETE FROM sms_section WHERE section_id = ?', (section_id, ))
        db.commit()   
        db.close()
        return redirect(url_for('sections'))
    return redirect(url_for('login'))  

########################### STUDENTS ##################################
    
@app.route("/student", methods =['GET', 'POST'])
def student():
    if 'loggedin' in session:       
        search_query = request.args.get('search', '')
        
        db = get_db()
        cursor = db.cursor()
        
        if search_query:
            search_param = f'%{search_query}%'
            cursor.execute('''
                SELECT s.id, s.admission_no, s.roll_no, s.name, s.photo, 
                       c.name AS class, sec.section 
                FROM sms_students s 
                LEFT JOIN sms_section sec ON sec.section_id = s.section 
                LEFT JOIN sms_classes c ON c.id = s.class
                WHERE s.name LIKE ? OR s.admission_no LIKE ? OR s.roll_no LIKE ?
            ''', (search_param, search_param, search_param))
        else:
            cursor.execute('''
                SELECT s.id, s.admission_no, s.roll_no, s.name, s.photo, 
                       c.name AS class, sec.section 
                FROM sms_students s 
                LEFT JOIN sms_section sec ON sec.section_id = s.section 
                LEFT JOIN sms_classes c ON c.id = s.class
            ''')
        
        students = cursor.fetchall() 
        
        cursor.execute('SELECT * FROM sms_classes')
        classes = cursor.fetchall() 
        
        cursor.execute('SELECT * FROM sms_section')
        sections = cursor.fetchall()
        
        db.close()
        return render_template("student.html", students=students, classes=classes, sections=sections, search_query=search_query)
    return redirect(url_for('login')) 
    
@app.route("/edit_student", methods =['GET'])
def edit_student():
    if 'loggedin' in session:
        student_id = request.args.get('student_id') 
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT s.id, s.admission_no, s.roll_no, s.name, s.photo, c.name AS class, sec.section FROM sms_students s LEFT JOIN sms_section sec ON sec.section_id = s.section LEFT JOIN sms_classes c ON c.id = s.class WHERE s.id = ?', (student_id,))
        students = cursor.fetchall() 
        
        cursor.execute('SELECT * FROM sms_classes')
        classes = cursor.fetchall() 
        
        cursor.execute('SELECT * FROM sms_section')
        sections = cursor.fetchall()
        
        db.close()
        return render_template("edit_student.html", students = students, classes = classes, sections = sections)
    return redirect(url_for('login'))  

@app.route("/save_student", methods=['GET', 'POST'])
def save_student():
    if 'loggedin' in session:    
        if request.method == 'POST' and all(k in request.form for k in ['name', 'class_id', 'section_id']):
            try:
                # Get form data
                student_data = {
                    'admission_no': request.form['admission_no'].strip(),
                    'roll_no': request.form['roll_no'].strip(),
                    'name': request.form['name'].strip(),
                    'gender': request.form['gender'],
                    'dob': request.form['dob'],
                    'mobile': request.form['mobile'].strip(),
                    'email': request.form['email'].strip(),
                    'current_address': request.form['current_address'].strip(),
                    'father_name': request.form['father_name'].strip(),
                    'mother_name': request.form['mother_name'].strip(),
                    'admission_date': request.form['admission_date'],
                    'academic_year': request.form['academic_year'],
                    'class_id': request.form['class_id'],
                    'section_id': request.form['section_id']
                }
                
                # Validate required fields
                if not all([student_data['name'], student_data['admission_no'], student_data['class_id']]):
                    return redirect(url_for('student'))
                
                # Handle photo upload
                photo = ""
                if 'photo' in request.files:
                    photo_file = request.files['photo']
                    if photo_file.filename:
                        if not os.path.exists('static/uploads'):
                            os.makedirs('static/uploads')
                        photo = f"uploads/{student_data['admission_no']}_{photo_file.filename}"
                        photo_file.save(os.path.join('static', photo))
                
                db = get_db()
                cursor = db.cursor()
                
                if request.form['action'] == 'updateStudent':
                    student_id = request.form['student_id']
                    update_fields = list(student_data.keys())
                    if photo:
                        update_fields.append('photo')
                        student_data['photo'] = photo
                    
                    query = f'''UPDATE sms_students SET 
                        {', '.join(f'{field} = ?' for field in update_fields)}
                        WHERE id = ?'''
                    
                    cursor.execute(query, list(student_data.values()) + [student_id])
                else:
                    student_data['photo'] = photo
                    fields = list(student_data.keys())
                    query = f'''INSERT INTO sms_students 
                        ({', '.join(fields)}) 
                        VALUES ({', '.join(['?'] * len(fields))})'''
                    
                    cursor.execute(query, list(student_data.values()))
                
                db.commit()
                db.close()
                return redirect(url_for('student'))
                
            except Exception as e:
                print(f"Error saving student: {e}")
                return redirect(url_for('student'))
                
    return redirect(url_for('login'))
    
@app.route("/delete_student", methods =['GET'])
def delete_student():
    if 'loggedin' in session:
        student_id = request.args.get('student_id') 
        db = get_db()
        cursor = db.cursor()
        cursor.execute('DELETE FROM sms_students WHERE id = ?', (student_id, ))
        db.commit()   
        db.close()
        return redirect(url_for('student'))
    return redirect(url_for('login'))  

@app.route("/add_student", methods =['GET'])
def add_student():
    if 'loggedin' in session:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT * FROM sms_classes')
        classes = cursor.fetchall() 
        
        cursor.execute('SELECT * FROM sms_section')
        sections = cursor.fetchall()
        
        db.close()
        return render_template("add_student.html", classes=classes, sections=sections)
    return redirect(url_for('login'))

@app.route("/view_student/<int:student_id>", methods=['GET'])
def view_student(student_id):
    if 'loggedin' in session:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT s.*, c.name AS class_name, sec.section AS section_name 
            FROM sms_students s 
            LEFT JOIN sms_section sec ON sec.section_id = s.section 
            LEFT JOIN sms_classes c ON c.id = s.class 
            WHERE s.id = ?
        ''', (student_id,))
        student = cursor.fetchone()
        
        # Get attendance records
        cursor.execute('''
            SELECT * FROM sms_attendance 
            WHERE student_id = ? 
            ORDER BY attendance_date DESC
        ''', (student_id,))
        attendance = cursor.fetchall()
        
        db.close()
        
        if student:
            return render_template("view_student.html", student=student, attendance=attendance)
        else:
            return redirect(url_for('student'))
    return redirect(url_for('login'))

# Add academic history tracking
@app.route("/student_history", methods=['GET', 'POST'])
def student_history():
    if 'loggedin' in session:
        if request.method == 'POST' and 'student_id' in request.form:
            student_id = request.form['student_id']
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute('''
                SELECT s.*, c.name AS class_name, sec.section AS section_name 
                FROM sms_students s 
                LEFT JOIN sms_section sec ON sec.section_id = s.section 
                LEFT JOIN sms_classes c ON c.id = s.class 
                WHERE s.id = ?
            ''', (student_id,))
            student = cursor.fetchone()
            
            # Get attendance statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_days,
                    SUM(CASE WHEN attendance_status = 'present' THEN 1 ELSE 0 END) as present_days,
                    SUM(CASE WHEN attendance_status = 'absent' THEN 1 ELSE 0 END) as absent_days
                FROM sms_attendance 
                WHERE student_id = ?
            ''', (student_id,))
            attendance_stats = cursor.fetchone()
            
            db.close()
            
            if student:
                return render_template("student_history.html", student=student, attendance_stats=attendance_stats)
        
        return redirect(url_for('student'))
    return redirect(url_for('login'))

@app.route("/attendance", methods =['GET', 'POST'])
def attendance():
    if 'loggedin' in session:  
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT * FROM sms_classes')
        classes = cursor.fetchall() 
        
        cursor.execute('SELECT * FROM sms_section')
        sections = cursor.fetchall()
        
        db.close()
        return render_template("attendance.html", classes = classes, sections = sections)
    return redirect(url_for('login')) 
    
    
@app.route("/getClassAttendance", methods =['GET', 'POST'])
def getClassAttendance():
    if 'loggedin' in session:  
        if request.method == 'POST' and 'classid' in request.form and 'sectionid' in request.form:
        
            classid = request.form['classid']
            sectionid = request.form['sectionid']
            
            db = get_db()
            cursor = db.cursor()   
            
            cursor.execute('SELECT * FROM sms_classes')
            classes = cursor.fetchall() 
            
            cursor.execute('SELECT * FROM sms_section')
            sections = cursor.fetchall() 

            currentDate = date.today().strftime('%Y/%m/%d')
                     
            cursor.execute('SELECT s.id, s.name, s.photo, s.gender, s.dob, s.mobile, s.email, s.current_address, s.father_name, s.mother_name,s.admission_no, s.roll_no, s.admission_date, s.academic_year, a.attendance_status, a.attendance_date FROM sms_students as s LEFT JOIN sms_attendance as a ON s.id = a.student_id WHERE s.class = ? AND s.section = ?', (classid, sectionid))              
            students = cursor.fetchall()   
                      
            db.close()
            return render_template("attendance.html", classes = classes, sections = sections, students = students, classId = classid, sectionId = sectionid)        
        elif request.method == 'POST':
            msg = 'Please fill out the form field !'        
        return redirect(url_for('attendance'))        
    return redirect(url_for('login')) 
    

@app.route("/report", methods =['GET', 'POST'])
def report():
    if 'loggedin' in session:  
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT * FROM sms_classes')
        classes = cursor.fetchall() 
        
        cursor.execute('SELECT * FROM sms_section')
        sections = cursor.fetchall()
        
        db.close()
        return render_template("report.html", classes = classes, sections = sections)
    return redirect(url_for('login'))     

# Course & Faculty Management routes
@app.route('/course-faculty/assign', methods=['GET', 'POST'])
def assign_faculty():
    if not session.get('id'):
        return redirect(url_for('login'))
    
    courses = []
    faculty = []
    assignments = []
    
    # Get all courses
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM subjects ORDER BY name")
    courses = cursor.fetchall()
    
    # Get all faculty/teachers
    cursor.execute("SELECT * FROM teacher ORDER BY name")
    faculty = cursor.fetchall()
    
    # Get existing assignments
    cursor.execute("""
        SELECT a.id, s.name as course_name, t.name as faculty_name, a.days, a.time_slot 
        FROM faculty_assignments a 
        JOIN subjects s ON a.subject_id = s.id 
        JOIN teacher t ON a.teacher_id = t.id
    """)
    assignments = cursor.fetchall()
    
    # Handle assignment submission
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        teacher_id = request.form.get('teacher_id')
        days = request.form.get('days')
        time_slot = request.form.get('time_slot')
        
        # Validate input
        if not all([subject_id, teacher_id, days, time_slot]):
            flash('All fields are required', 'error')
        else:
            try:
                cursor.execute(
                    "INSERT INTO faculty_assignments (subject_id, teacher_id, days, time_slot) VALUES (%s, %s, %s, %s)",
                    (subject_id, teacher_id, days, time_slot)
                )
                conn.commit()
                flash('Faculty assigned successfully', 'success')
                return redirect(url_for('assign_faculty'))
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
    
    cursor.close()
    conn.close()
    
    return render_template('course_faculty/assign.html', 
                          courses=courses, 
                          faculty=faculty, 
                          assignments=assignments)

@app.route('/course-faculty/schedules', methods=['GET', 'POST'])
def manage_schedules():
    if not session.get('id'):
        return redirect(url_for('login'))
    
    schedules = []
    
    # Get all schedules
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.id, s.class_id, c.name as class_name, s.section_id, sec.section as section_name,
               s.subject_id, sub.name as subject_name, s.day, s.start_time, s.end_time
        FROM schedules s
        JOIN classes c ON s.class_id = c.id
        JOIN sections sec ON s.section_id = sec.section_id
        JOIN subjects sub ON s.subject_id = sub.id
        ORDER BY c.name, sec.section, s.day, s.start_time
    """)
    schedules = cursor.fetchall()
    
    # Get classes for dropdown
    cursor.execute("SELECT * FROM classes ORDER BY name")
    classes = cursor.fetchall()
    
    # Get sections for dropdown
    cursor.execute("SELECT * FROM sections ORDER BY section")
    sections = cursor.fetchall()
    
    # Get subjects for dropdown
    cursor.execute("SELECT * FROM subjects ORDER BY name")
    subjects = cursor.fetchall()
    
    # Handle schedule submission
    if request.method == 'POST':
        class_id = request.form.get('class_id')
        section_id = request.form.get('section_id')
        subject_id = request.form.get('subject_id')
        day = request.form.get('day')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        
        # Validate input
        if not all([class_id, section_id, subject_id, day, start_time, end_time]):
            flash('All fields are required', 'error')
        else:
            try:
                cursor.execute(
                    """INSERT INTO schedules 
                       (class_id, section_id, subject_id, day, start_time, end_time) 
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (class_id, section_id, subject_id, day, start_time, end_time)
                )
                conn.commit()
                flash('Schedule added successfully', 'success')
                return redirect(url_for('manage_schedules'))
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
    
    cursor.close()
    conn.close()
    
    return render_template('course_faculty/schedules.html', 
                          schedules=schedules,
                          classes=classes,
                          sections=sections,
                          subjects=subjects)

@app.route('/course-faculty/resources', methods=['GET', 'POST'])
def allocate_resources():
    if not session.get('id'):
        return redirect(url_for('login'))
    
    resources = []
    allocations = []
    
    # Connect to database
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get all resources
    cursor.execute("SELECT * FROM resources ORDER BY name")
    resources = cursor.fetchall()
    
    # Get subjects
    cursor.execute("SELECT * FROM subjects ORDER BY name")
    subjects = cursor.fetchall()
    
    # Get existing allocations
    cursor.execute("""
        SELECT a.id, r.name as resource_name, s.name as subject_name, 
               a.quantity, a.allocation_date, a.return_date
        FROM resource_allocations a
        JOIN resources r ON a.resource_id = r.id
        JOIN subjects s ON a.subject_id = s.id
        ORDER BY a.allocation_date DESC
    """)
    allocations = cursor.fetchall()
    
    # Handle resource allocation submission
    if request.method == 'POST':
        resource_id = request.form.get('resource_id')
        subject_id = request.form.get('subject_id')
        quantity = request.form.get('quantity')
        allocation_date = request.form.get('allocation_date')
        return_date = request.form.get('return_date')
        
        # Validate input
        if not all([resource_id, subject_id, quantity, allocation_date]):
            flash('Required fields are missing', 'error')
        else:
            try:
                cursor.execute(
                    """INSERT INTO resource_allocations 
                       (resource_id, subject_id, quantity, allocation_date, return_date) 
                       VALUES (%s, %s, %s, %s, %s)""",
                    (resource_id, subject_id, quantity, allocation_date, return_date)
                )
                conn.commit()
                flash('Resource allocated successfully', 'success')
                return redirect(url_for('allocate_resources'))
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
    
    cursor.close()
    conn.close()
    
    return render_template('course_faculty/resources.html', 
                          resources=resources,
                          subjects=subjects,
                          allocations=allocations)

@app.route("/get_class/<int:class_id>", methods=['GET'])
def get_class(class_id):
    if 'loggedin' in session:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, name, COALESCE(code, "") as code FROM sms_classes WHERE id = ?', (class_id,))
        class_data = cursor.fetchone()
        db.close()
        
        if class_data:
            return jsonify({
                'class_id': class_data['id'],
                'name': class_data['name'],
                'code': class_data['code']
            })
    return jsonify({'error': 'Class not found'}), 404

@app.route("/save_classes", methods=['POST'])
def save_classes():
    if 'loggedin' in session:
        if request.method == 'POST':
            class_name = request.form.get('className')
            class_code = request.form.get('classCode')
            section_id = request.form.get('sectionid', None)  # Added section
            teacher_id = request.form.get('teacherid', None)  # Added teacher
            action = request.form.get('action')
            
            if not class_name:
                return jsonify({'error': 'Class name is required'}), 400
                
            db = get_db()
            cursor = db.cursor()
            
            try:
                if action == 'updateClass':
                    class_id = request.form.get('classid')
                    cursor.execute('''
                        UPDATE sms_classes 
                        SET name = ?, code = ?, section = ?, teacher_id = ? 
                        WHERE id = ?''',
                        (class_name, class_code, section_id, teacher_id, class_id))
                else:
                    cursor.execute('''
                        INSERT INTO sms_classes (name, code, section, teacher_id) 
                        VALUES (?, ?, ?, ?)''',
                        (class_name, class_code, section_id, teacher_id))
                
                db.commit()
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
            finally:
                db.close()
    return jsonify({'error': 'Unauthorized'}), 401

# Add these routes
@app.route("/examination", methods=['GET'])
def examination():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    db = get_db()
    cursor = db.cursor()
    
    # Get upcoming exams
    cursor.execute('''
        SELECT e.*, et.name as exam_type, c.name as class_name, s.subject as subject_name
        FROM sms_exams e
        JOIN sms_exam_types et ON e.exam_type_id = et.id
        JOIN sms_classes c ON e.class_id = c.id
        JOIN sms_subjects s ON e.subject_id = s.subject_id
        WHERE e.exam_date >= date('now')
        ORDER BY e.exam_date ASC
        LIMIT 5
    ''')
    upcoming_exams = cursor.fetchall()
    
    # Get recent results
    cursor.execute('''
        SELECT er.*, e.exam_date, et.name as exam_type, 
               s.name as student_name, c.name as class_name, 
               sub.subject as subject_name
        FROM sms_exam_results er
        JOIN sms_exams e ON er.exam_id = e.id
        JOIN sms_exam_types et ON e.exam_type_id = et.id
        JOIN sms_students s ON er.student_id = s.id
        JOIN sms_classes c ON e.class_id = c.id
        JOIN sms_subjects sub ON e.subject_id = sub.subject_id
        ORDER BY er.date_added DESC
        LIMIT 5
    ''')
    recent_results = cursor.fetchall()
    
    # Get summary stats
    cursor.execute('SELECT COUNT(*) FROM sms_exams')
    total_exams = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM sms_exam_results')
    total_results = cursor.fetchone()[0]
    
    cursor.execute('SELECT AVG(marks_obtained) FROM sms_exam_results')
    avg_score = cursor.fetchone()[0] or 0
    
    # Get classes and subjects for the form
    cursor.execute('SELECT * FROM sms_classes')
    classes = cursor.fetchall()
    
    cursor.execute('SELECT * FROM sms_subjects')
    subjects = cursor.fetchall()
    
    cursor.execute('SELECT * FROM sms_exam_types')
    exam_types = cursor.fetchall()
    
    db.close()
    
    return render_template('examination.html',
                         upcoming_exams=upcoming_exams,
                         recent_results=recent_results,
                         total_exams=total_exams,
                         total_results=total_results,
                         avg_score=round(avg_score, 2),
                         classes=classes,
                         subjects=subjects,
                         exam_types=exam_types)

@app.route("/add_exam", methods=['POST'])
def add_exam():
    if 'loggedin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    exam_type = request.form.get('exam_type')
    class_id = request.form.get('class_id')
    subject_id = request.form.get('subject_id')
    exam_date = request.form.get('exam_date')
    total_marks = request.form.get('total_marks')
    passing_marks = request.form.get('passing_marks')
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO sms_exams 
            (exam_type_id, class_id, subject_id, exam_date, total_marks, passing_marks, academic_year)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (exam_type, class_id, subject_id, exam_date, total_marks, passing_marks, '2023-24'))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route("/grade_exam/<int:exam_id>", methods=['GET', 'POST'])
def grade_exam(exam_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('grade_'):
                student_id = key.split('_')[1]
                marks = value
                grade = calculate_grade(float(marks))  # You'll need to implement this function
                
                cursor.execute('''
                    INSERT INTO sms_exam_results 
                    (exam_id, student_id, marks_obtained, grade)
                    VALUES (?, ?, ?, ?)
                ''', (exam_id, student_id, marks, grade))
        
        db.commit()
        return redirect(url_for('examination'))
    
    # Get exam details
    cursor.execute('''
        SELECT e.*, et.name as exam_type, c.name as class_name, s.subject as subject_name
        FROM sms_exams e
        JOIN sms_exam_types et ON e.exam_type_id = et.id
        JOIN sms_classes c ON e.class_id = c.id
        JOIN sms_subjects s ON e.subject_id = s.subject_id
        WHERE e.id = ?
    ''', (exam_id,))
    exam = cursor.fetchone()
    
    # Get students in this class
    cursor.execute('''
        SELECT s.*, COALESCE(er.marks_obtained, -1) as marks, er.grade
        FROM sms_students s
        LEFT JOIN sms_exam_results er ON er.student_id = s.id AND er.exam_id = ?
        WHERE s.class = ?
    ''', (exam_id, exam['class_id']))
    students = cursor.fetchall()
    
    db.close()
    
    return render_template('grade_exam.html', exam=exam, students=students)

def calculate_grade(marks, total_marks=100):
    percentage = (marks / total_marks) * 100
    if percentage >= 90:
        return 'A+'
    elif percentage >= 80:
        return 'A'
    elif percentage >= 70:
        return 'B'
    elif percentage >= 60:
        return 'C'
    elif percentage >= 50:
        return 'D'
    else:
        return 'F'

def safe_execute(query, params=None, fetchall=True):
    """Execute SQL safely with automatic connection handling"""
    try:
        db = get_db()
        cursor = db.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        result = cursor.fetchall() if fetchall else cursor.fetchone()
        db.commit()
        return result
    except Exception as e:
        print(f"Database error: {e}")
        return None
    finally:
        db.close()

def validate_required_fields(form_data, required_fields):
    """Validate that all required fields are present and not empty"""
    return all(form_data.get(field, '').strip() for field in required_fields)

# Temporary code to reinitialize database
if __name__ == "__main__":
    # Delete existing database if it exists
    if os.path.exists('python_sms.db'):
        os.remove('python_sms.db')
    # Initialize fresh database
    init_db()
    app.run(port=5006, debug=True)

