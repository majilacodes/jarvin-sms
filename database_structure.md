# School Management System Database Structure

The database contains the following tables with their respective schemas:

## User Management

### `sms_user`
- `id` (INTEGER, PRIMARY KEY): Unique identifier for each user
- `first_name` (TEXT): First name of user
- `email` (TEXT, UNIQUE): Email address (used for login)
- `password` (TEXT): User password
- `type` (TEXT): User role type (admin, teacher, etc.)
- `status` (TEXT): Account status (active, inactive)

## Faculty Management

### `sms_teacher`
- `teacher_id` (INTEGER, PRIMARY KEY): Unique identifier for each teacher
- `teacher` (TEXT): Teacher's name
- `subject_id` (INTEGER): Foreign key to subject specialization

### `sms_subjects`
- `subject_id` (INTEGER, PRIMARY KEY): Unique identifier for each subject
- `subject` (TEXT): Subject name
- `type` (TEXT): Subject type (Core, Elective)
- `code` (TEXT): Subject code (e.g., CS201)

## Class and Section Management

### `sms_section`
- `section_id` (INTEGER, PRIMARY KEY): Unique identifier for each section
- `section` (TEXT): Section name (e.g., A, B, C)

### `sms_classes`
- `id` (INTEGER, PRIMARY KEY): Unique identifier for each class
- `name` (TEXT): Class name (e.g., CSE 1st Year)
- `code` (TEXT): Class code (e.g., CSE1)
- `section` (INTEGER): Foreign key to section
- `teacher_id` (INTEGER): Foreign key to class teacher

## Student Management

### `sms_students`
- `id` (INTEGER, PRIMARY KEY): Unique identifier for each student
- `admission_no` (TEXT): Admission number
- `roll_no` (TEXT): Roll number
- `name` (TEXT): Student's name
- `photo` (TEXT): Path to student's photo
- `gender` (TEXT): Gender
- `dob` (TEXT): Date of birth
- `mobile` (TEXT): Mobile number
- `email` (TEXT): Email address
- `current_address` (TEXT): Current address
- `father_name` (TEXT): Father's name
- `mother_name` (TEXT): Mother's name
- `admission_date` (TEXT): Date of admission
- `academic_year` (TEXT): Academic year
- `class` (INTEGER): Foreign key to class
- `section` (INTEGER): Foreign key to section

## Attendance Management

### `sms_attendance`
- `id` (INTEGER, PRIMARY KEY): Unique identifier for each attendance record
- `student_id` (INTEGER): Foreign key to student
- `attendance_status` (TEXT): Status (present, absent)
- `attendance_date` (DATE): Date of attendance

## Examination Management

### `sms_exam_types`
- `id` (INTEGER, PRIMARY KEY): Unique identifier for each exam type
- `name` (TEXT, NOT NULL): Exam type name (Midterm, Final, Quiz, etc.)
- `description` (TEXT): Description of the exam type

### `sms_exams`
- `id` (INTEGER, PRIMARY KEY): Unique identifier for each exam
- `exam_type_id` (INTEGER): Foreign key to exam type
- `class_id` (INTEGER): Foreign key to class
- `subject_id` (INTEGER): Foreign key to subject
- `exam_date` (DATE): Date of exam
- `total_marks` (INTEGER): Total marks for the exam
- `passing_marks` (INTEGER): Passing marks for the exam
- `academic_year` (TEXT): Academic year
- `status` (TEXT, DEFAULT 'upcoming'): Status of exam (upcoming, completed)

### `sms_exam_results`
- `id` (INTEGER, PRIMARY KEY): Unique identifier for each result
- `exam_id` (INTEGER): Foreign key to exam
- `student_id` (INTEGER): Foreign key to student
- `marks_obtained` (DECIMAL(5,2)): Marks obtained by student
- `grade` (TEXT): Grade assigned (A+, A, B+, etc.)
- `remarks` (TEXT): Remarks about performance
- `date_added` (DATETIME, DEFAULT CURRENT_TIMESTAMP): Date result was added

## Sample Data

The database is initialized with comprehensive sample data including:

- Admin and teacher user accounts
- 20 subjects (core and elective)
- 5 sections (A through E)
- 20 teachers with subject specializations
- 20 classes (CSE, ECE, IT, ME, EE - 1st through 4th years)
- 20 students across different classes and sections
- Attendance records for the last 30 days
- Various exam types (Midterm, Final, Quiz, Lab Test, Project Review, Viva)
- Sample exams for different classes and subjects
- Complete exam results with grades and remarks

The database schema includes foreign key relationships to maintain data integrity across tables.
