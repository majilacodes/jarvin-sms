from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from datetime import date
import re
import os
import sys
    
app = Flask(__name__)

app.secret_key = 'abcd21234455'  

# Database initialization function
def get_db():
    db = sqlite3.connect('python_sms.db')
    db.row_factory = sqlite3.Row  # This allows accessing columns by name
    return db

# Initialize the database schema
def init_db():
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
    
    # Add default admin user if none exists
    cursor.execute('SELECT COUNT(*) FROM sms_user')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO sms_user (first_name, email, password, type, status)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Admin', 'admin@example.com', 'admin123', 'admin', 'active'))
    
    db.commit()
    db.close()

# Initialize the database on startup
init_db()

@app.route('/')
@app.route('/login', methods =['GET', 'POST'])
def login():
    message = ''  # Fixed typo in variable name
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']        
        password = request.form['password']
        
        db = get_db()
        cursor = db.cursor()
        
        # Add error handling for database connection
        try:
            # Simplified query and removed status check initially for debugging
            cursor.execute('SELECT * FROM sms_user WHERE email = ? AND password = ?', 
                         (email, password))
            user = cursor.fetchone()
            
            if user:
                # Convert SQLite Row to dict for easier access
                user_dict = dict(user)
                
                session['loggedin'] = True
                session['userid'] = user_dict['id']
                session['name'] = user_dict['first_name']
                session['email'] = user_dict['email']
                session['role'] = user_dict['type']
                
                message = 'Logged in successfully!'            
                return redirect(url_for('dashboard'))
            else:
                message = 'Invalid email or password!'
                
        except Exception as e:
            message = f'Database error: {str(e)}'
        finally:
            db.close()
            
    return render_template('login.html', message=message)  # Fixed variable name
    
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    session.pop('name', None)
    session.pop('role', None)
    return redirect(url_for('login'))
    
@app.route("/dashboard", methods =['GET', 'POST'])
def dashboard():
    if 'loggedin' in session:        
        return render_template("dashboard.html")
    return redirect(url_for('login'))    

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
    
@app.route("/save_teacher", methods =['GET', 'POST'])
def save_teacher():
    if 'loggedin' in session:    
        if request.method == 'POST' and 'techer_name' in request.form and 'specialization' in request.form:
            techer_name = request.form['techer_name'] 
            specialization = request.form['specialization']             
            action = request.form['action']             
            
            db = get_db()
            cursor = db.cursor()
            
            if action == 'updateTeacher':
                teacherid = request.form['teacherid'] 
                cursor.execute('UPDATE sms_teacher SET teacher = ?, subject_id = ? WHERE teacher_id = ?', 
                             (techer_name, specialization, teacherid))
            else: 
                cursor.execute('INSERT INTO sms_teacher (teacher, subject_id) VALUES (?, ?)', 
                             (techer_name, specialization))
            
            db.commit()
            db.close()
            return redirect(url_for('teacher'))        
        elif request.method == 'POST':
            msg = 'Please fill out the form field !'        
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
    
@app.route("/save_subject", methods =['GET', 'POST'])
def save_subject():
    if 'loggedin' in session:    
        db = get_db()
        cursor = db.cursor()        
        if request.method == 'POST' and 'subject' in request.form and 's_type' in request.form and 'code' in request.form:
            subject = request.form['subject'] 
            s_type = request.form['s_type'] 
            code = request.form['code']               
            action = request.form['action']             
            
            if action == 'updateSubject':
                subjectid = request.form['subjectid'] 
                cursor.execute('UPDATE sms_subjects SET subject = ?, type = ?, code = ? WHERE subject_id  =?', (subject, s_type, code, subjectid))
            else: 
                cursor.execute('INSERT INTO sms_subjects (subject, type, code) VALUES (?, ?, ?)', (subject, s_type, code))
            
            db.commit()
            db.close()
            return redirect(url_for('subject'))        
        elif request.method == 'POST':
            msg = 'Please fill out the form field !'        
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
        cursor.execute('DELETE FROM sms_classes WHERE id = ?', (class_id, ))
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

@app.route("/save_student", methods =['GET', 'POST'])
def save_student():
    if 'loggedin' in session:    
        db = get_db()
        cursor = db.cursor()        
        if request.method == 'POST' and 'name' in request.form and 'class_id' in request.form and 'section_id' in request.form:
            admission_no = request.form['admission_no']
            roll_no = request.form['roll_no']
            name = request.form['name']
            gender = request.form['gender']
            dob = request.form['dob']
            mobile = request.form['mobile']
            email = request.form['email']
            current_address = request.form['current_address']
            father_name = request.form['father_name']
            mother_name = request.form['mother_name']
            admission_date = request.form['admission_date']
            academic_year = request.form['academic_year']
            class_id = request.form['class_id']
            section_id = request.form['section_id']
            
            # Handle photo upload
            photo = ""
            if 'photo' in request.files:
                photo_file = request.files['photo']
                if photo_file.filename != '':
                    # Create uploads directory if it doesn't exist
                    if not os.path.exists('static/uploads'):
                        os.makedirs('static/uploads')
                    photo = f"uploads/{admission_no}_{photo_file.filename}"
                    photo_file.save(os.path.join('static', photo))
            
            action = request.form['action']             
            
            if action == 'updateStudent':
                student_id = request.form['student_id']
                if photo:
                    cursor.execute('''
                        UPDATE sms_students 
                        SET admission_no=?, roll_no=?, name=?, gender=?, dob=?, 
                            mobile=?, email=?, current_address=?, father_name=?, 
                            mother_name=?, admission_date=?, academic_year=?, 
                            class=?, section=?, photo=? 
                        WHERE id=?
                    ''', (admission_no, roll_no, name, gender, dob, mobile, email, 
                         current_address, father_name, mother_name, admission_date, 
                         academic_year, class_id, section_id, photo, student_id))
                else:
                    cursor.execute('''
                        UPDATE sms_students 
                        SET admission_no=?, roll_no=?, name=?, gender=?, dob=?, 
                            mobile=?, email=?, current_address=?, father_name=?, 
                            mother_name=?, admission_date=?, academic_year=?, 
                            class=?, section=? 
                        WHERE id=?
                    ''', (admission_no, roll_no, name, gender, dob, mobile, email, 
                         current_address, father_name, mother_name, admission_date, 
                         academic_year, class_id, section_id, student_id))
            else: 
                cursor.execute('''
                    INSERT INTO sms_students 
                    (admission_no, roll_no, name, photo, gender, dob, mobile, 
                     email, current_address, father_name, mother_name, 
                     admission_date, academic_year, class, section) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (admission_no, roll_no, name, photo, gender, dob, mobile, 
                     email, current_address, father_name, mother_name, 
                     admission_date, academic_year, class_id, section_id))
            
            db.commit()
            db.close()
            return redirect(url_for('student'))        
        elif request.method == 'POST':
            msg = 'Please fill out all required fields!'        
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
    conn = get_db_connection()
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
    conn = get_db_connection()
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
    conn = get_db_connection()
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
            action = request.form.get('action')
            
            db = get_db()
            cursor = db.cursor()
            
            try:
                if action == 'updateClass':
                    class_id = request.form.get('classid')
                    cursor.execute('UPDATE sms_classes SET name = ?, code = ? WHERE id = ?',
                                 (class_name, class_code, class_id))
                else:
                    cursor.execute('INSERT INTO sms_classes (name, code) VALUES (?, ?)',
                                 (class_name, class_code))
                
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

# Temporary code to reinitialize database
if __name__ == "__main__":
    # Delete existing database if it exists
    if os.path.exists('python_sms.db'):
        os.remove('python_sms.db')
    # Initialize fresh database
    init_db()
    app.run(port=5006, debug=True)

