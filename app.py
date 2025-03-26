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
    ''')
    db.commit()
    db.close()

# Initialize the database on startup
init_db()

@app.route('/')
@app.route('/login', methods =['GET', 'POST'])
def login():
    mesage = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']        
        password = request.form['password']
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM sms_user WHERE status="active" AND email = ? AND password = ?', 
                      (email, password))
        user = cursor.fetchone()
        db.close()
        
        if user:
            session['loggedin'] = True
            session['userid'] = user['id']
            session['name'] = user['first_name']
            session['email'] = user['email']
            session['role'] = user['type']
            mesage = 'Logged in successfully !'            
            return redirect(url_for('dashboard'))
        else:
            mesage = 'Please enter correct email / password !'
    return render_template('login.html', mesage = mesage)
    
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

@app.route("/classes", methods =['GET', 'POST'])
def classes():
    if 'loggedin' in session:  
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT c.id, c.name, s.section, t.teacher FROM sms_classes c LEFT JOIN sms_section s ON s.section_id = c.section LEFT JOIN sms_teacher t ON t.teacher_id = c.teacher_id')
        classes = cursor.fetchall() 
           
        cursor.execute('SELECT * FROM sms_section')
        sections = cursor.fetchall() 
        
        cursor.execute('SELECT * FROM sms_teacher')
        teachers = cursor.fetchall()
        
        db.close()
        return render_template("class.html", classes = classes, sections = sections, teachers = teachers)
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
    
if __name__ == "__main__":
    app.run(debug=True)

