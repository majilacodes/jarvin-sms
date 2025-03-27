from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.memory import ConversationBufferMemory
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import os
import sqlite3
import pickle
import re

class RAGSystem:
    def __init__(self, db_path, google_api_key):
        self.db_path = db_path
        os.environ["GOOGLE_API_KEY"] = google_api_key
        
        # Initialize the embeddings model
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Initialize the LLM with proper parameters for the Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            top_p=0.85,
            max_output_tokens=2048
        )
        
        # Get the vector store
        self.vectorstore = self._get_vectorstore()
        
        # Initialize memory for conversation history
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    
    def _get_vectorstore(self):
        """Get the vector store, creating it if necessary"""
        vector_store_path = "vectorstore.pkl"
        if os.path.exists(vector_store_path):
            try:
                with open(vector_store_path, "rb") as f:
                    vectorstore = pickle.load(f)
                    print("Loaded existing vector store")
                    return vectorstore
            except Exception as e:
                print(f"Error loading vector store: {e}")
        
        # Create the vector store from scratch
        print("Creating new vector store...")
        documents = self._extract_data_from_db()
        vectorstore = self._create_vectorstore(documents)
        
        # Save the vector store
        try:
            with open(vector_store_path, "wb") as f:
                pickle.dump(vectorstore, f)
                print("Vector store saved successfully")
        except Exception as e:
            print(f"Error saving vector store: {e}")
        
        return vectorstore
    
    def _extract_data_from_db(self):
        """Extract all relevant data from the database and prepare it for vectorization"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        documents = []
        
        # Extract system information first
        system_info = """
        Jarvin CMS is a comprehensive School Management System that helps educational institutions manage:
        - Student records and profiles
        - Teacher information and subject assignments
        - Attendance tracking and reporting
        - Examination schedules and results
        - Class and section organization
        - Academic performance analytics
        - Grade evaluation through AI
        
        The system provides detailed information about students, teachers, classes, subjects, exams, and attendance.
        """
        documents.append(system_info)
        
        # Extract more detailed students data 
        try:
            cursor.execute("""
                SELECT s.id, s.admission_no, s.roll_no, s.name, s.gender, s.dob, s.mobile, s.email, 
                       s.current_address, s.father_name, s.mother_name, s.admission_date, s.academic_year,
                       c.name as class_name, c.code as class_code,
                       sec.section as section_name
                FROM sms_students s
                LEFT JOIN sms_classes c ON s.class = c.id
                LEFT JOIN sms_section sec ON s.section = sec.section_id
            """)
            students = cursor.fetchall()
            
            for student in students:
                # Create a more detailed student document
                doc = f"""
                Student Information:
                Student ID: {student[0]}
                Admission Number: {student[1]}
                Roll Number: {student[2]}
                Student Name: {student[3]}
                Gender: {student[4]}
                Date of Birth: {student[5]}
                Contact Number: {student[6]}
                Email Address: {student[7]}
                Current Address: {student[8]}
                Father's Name: {student[9]}
                Mother's Name: {student[10]}
                Admission Date: {student[11]}
                Academic Year: {student[12]}
                Class: {student[13] or 'Not Assigned'}
                Class Code: {student[14] or 'Not Assigned'}
                Section: {student[15] or 'Not Assigned'}
                """
                documents.append(doc)
            
            print(f"Added {len(students)} student records to the knowledge base")
        except sqlite3.OperationalError as e:
            print(f"Error retrieving students: {e}")
        
        # Extract more detailed classes data
        try:
            cursor.execute("""
                SELECT c.id, c.name, c.code, t.teacher, COUNT(s.id) as total_students
                FROM sms_classes c
                LEFT JOIN sms_teacher t ON c.teacher_id = t.teacher_id
                LEFT JOIN sms_students s ON s.class = c.id
                GROUP BY c.id, c.name, c.code, t.teacher
            """)
            classes = cursor.fetchall()
            
            for class_data in classes:
                doc = f"""
                Class Information:
                Class ID: {class_data[0]}
                Class Name: {class_data[1]}
                Class Code: {class_data[2]}
                Class Teacher: {class_data[3] or 'Not Assigned'}
                Total Students: {class_data[4]}
                """
                documents.append(doc)
            
            print(f"Added {len(classes)} class records to the knowledge base")
        except sqlite3.OperationalError as e:
            print(f"Error retrieving classes: {e}")
        
        # Extract sections with student counts
        try:
            cursor.execute("""
                SELECT sec.section_id, sec.section, COUNT(s.id) as total_students
                FROM sms_section sec
                LEFT JOIN sms_students s ON s.section = sec.section_id
                GROUP BY sec.section_id, sec.section
            """)
            sections = cursor.fetchall()
            
            for section in sections:
                doc = f"""
                Section Information:
                Section ID: {section[0]}
                Section Name: {section[1]}
                Total Students: {section[2]}
                """
                documents.append(doc)
            
            print(f"Added {len(sections)} section records to the knowledge base")
        except sqlite3.OperationalError as e:
            print(f"Error retrieving sections: {e}")
        
        # Extract more detailed subjects data
        try:
            cursor.execute("""
                SELECT s.subject_id, s.subject, s.type, s.code, 
                       t.teacher, COUNT(e.id) as total_exams
                FROM sms_subjects s
                LEFT JOIN sms_teacher t ON t.subject_id = s.subject_id
                LEFT JOIN sms_exams e ON e.subject_id = s.subject_id
                GROUP BY s.subject_id, s.subject, s.type, s.code, t.teacher
            """)
            subjects = cursor.fetchall()
            
            for subject in subjects:
                doc = f"""
                Subject Information:
                Subject ID: {subject[0]}
                Subject Name: {subject[1]}
                Subject Type: {subject[2]}
                Subject Code: {subject[3]}
                Subject Teacher: {subject[4] or 'Not Assigned'}
                Total Exams: {subject[5]}
                """
                documents.append(doc)
            
            print(f"Added {len(subjects)} subject records to the knowledge base")
        except sqlite3.OperationalError as e:
            print(f"Error retrieving subjects: {e}")
        
        # Extract more detailed exams data
        try:
            cursor.execute("""
                SELECT e.id, et.name as exam_type, c.name as class_name, 
                       s.subject as subject_name, e.exam_date, e.total_marks, 
                       e.passing_marks, e.academic_year, e.status
                FROM sms_exams e
                JOIN sms_exam_types et ON e.exam_type_id = et.id
                JOIN sms_classes c ON e.class_id = c.id
                JOIN sms_subjects s ON e.subject_id = s.subject_id
            """)
            exams = cursor.fetchall()
            
            for exam in exams:
                doc = f"""
                Exam Information:
                Exam ID: {exam[0]}
                Exam Type: {exam[1]}
                Class: {exam[2]}
                Subject: {exam[3]}
                Exam Date: {exam[4]}
                Total Marks: {exam[5]}
                Passing Marks: {exam[6]}
                Academic Year: {exam[7]}
                Status: {exam[8]}
                """
                documents.append(doc)
            
            print(f"Added {len(exams)} exam records to the knowledge base")
        except sqlite3.OperationalError as e:
            print(f"Error retrieving exams: {e}")
        
        # Extract examination results with more details
        try:
            cursor.execute("""
                SELECT er.id, s.name as student_name, s.roll_no,
                       c.name as class_name, sec.section as section_name, 
                       et.name as exam_type, sub.subject as subject_name, 
                       e.total_marks, er.marks_obtained, 
                       er.grade, er.remarks
                FROM sms_exam_results er
                JOIN sms_students s ON er.student_id = s.id
                JOIN sms_exams e ON er.exam_id = e.id
                JOIN sms_exam_types et ON e.exam_type_id = et.id
                JOIN sms_classes c ON s.class = c.id
                JOIN sms_section sec ON s.section = sec.section_id
                JOIN sms_subjects sub ON e.subject_id = sub.subject_id
            """)
            results = cursor.fetchall()
            
            for result in results:
                doc = f"""
                Exam Result Information:
                Result ID: {result[0]}
                Student Name: {result[1]}
                Roll Number: {result[2]}
                Class: {result[3]}
                Section: {result[4]}
                Exam Type: {result[5]}
                Subject: {result[6]}
                Total Marks: {result[7]}
                Marks Obtained: {result[8]}
                Grade: {result[9]}
                Remarks: {result[10]}
                """
                documents.append(doc)
            
            print(f"Added {len(results)} exam result records to the knowledge base")
        except sqlite3.OperationalError as e:
            print(f"Error retrieving exam results: {e}")
        
        # Extract attendance data
        try:
            cursor.execute("""
                SELECT a.id, s.name as student_name, s.roll_no,
                       c.name as class_name, sec.section as section_name,
                       a.attendance_date, a.attendance_status
                FROM sms_attendance a
                JOIN sms_students s ON a.student_id = s.id
                JOIN sms_classes c ON s.class = c.id
                JOIN sms_section sec ON s.section = sec.section_id
                ORDER BY a.attendance_date DESC
                LIMIT 500
            """)
            attendance = cursor.fetchall()
            
            # Group attendance by student for better context
            attendance_by_student = {}
            for record in attendance:
                student_name = record[1]
                if student_name not in attendance_by_student:
                    attendance_by_student[student_name] = []
                attendance_by_student[student_name].append(record)
            
            # Create documents for each student's attendance
            for student_name, records in attendance_by_student.items():
                present_count = sum(1 for r in records if r[6].lower() == 'present')
                total_count = len(records)
                attendance_percentage = (present_count / total_count * 100) if total_count > 0 else 0
                
                recent_records = records[:5]  # Take the 5 most recent records
                recent_status = "\n".join([f"Date: {r[5]}, Status: {r[6]}" for r in recent_records])
                
                doc = f"""
                Attendance Information for {student_name}:
                Roll Number: {records[0][2]}
                Class: {records[0][3]}
                Section: {records[0][4]}
                Attendance Percentage: {attendance_percentage:.2f}%
                Present Days: {present_count}
                Total Records: {total_count}
                
                Recent Attendance:
                {recent_status}
                """
                documents.append(doc)
            
            print(f"Added attendance records for {len(attendance_by_student)} students to the knowledge base")
        except sqlite3.OperationalError as e:
            print(f"Error retrieving attendance: {e}")
        
        # Add teachers data with more details
        try:
            cursor.execute("""
                SELECT t.teacher_id, t.teacher, s.subject, s.code as subject_code,
                       s.type as subject_type
                FROM sms_teacher t
                LEFT JOIN sms_subjects s ON t.subject_id = s.subject_id
            """)
            teachers = cursor.fetchall()
            
            for teacher in teachers:
                doc = f"""
                Teacher Information:
                Teacher ID: {teacher[0]}
                Teacher Name: {teacher[1]}
                Subject Specialization: {teacher[2] or 'Not Assigned'}
                Subject Code: {teacher[3] or 'Not Assigned'}
                Subject Type: {teacher[4] or 'Not Assigned'}
                """
                documents.append(doc)
            
            print(f"Added {len(teachers)} teacher records to the knowledge base")
        except sqlite3.OperationalError as e:
            print(f"Error retrieving teachers: {e}")
        
        # Add common educational terms and FAQ content
        educational_terms = """
        Educational Terms and Concepts:
        
        GPA (Grade Point Average): A numerical representation of a student's academic achievement.
        
        Semester: A period of time, usually 15-18 weeks, comprising an academic term.
        
        Curriculum: The subjects comprising a course of study in a school.
        
        Assessment: Evaluation of student learning through tests, projects, and other methods.
        
        Attendance: Record of a student's presence in class.
        
        Parent-Teacher Meeting: Scheduled event where parents discuss their child's progress with teachers.
        
        Report Card: Document showing a student's grades for each subject.
        
        Transcript: Official record of a student's academic work and achievements.
        
        Marking Scheme: Standard method used for evaluating students' work and assigning grades.
        
        Academic Year: The annual period of sessions of an educational institution.
        
        Extra-curricular Activities: Activities outside the regular academic curriculum.
        """
        documents.append(educational_terms)
        
        # Add FAQ content
        faq_content = """
        Frequently Asked Questions:
        
        Q: How can I view a student's attendance record?
        A: You can go to the Attendance module, select the class and section, and then either view all students or search for a specific student.
        
        Q: How do I add a new student to the system?
        A: Navigate to the Students module, click on "Add Student", and fill in the required details such as name, class, section, and contact information.
        
        Q: How do I generate a report card?
        A: Go to the Reports module, select "Generate Report Card", choose the class, section, and student, then select the exam and click on "Generate".
        
        Q: How can I see the overall class performance in an exam?
        A: Navigate to the Examination module, select the exam, and view the "Results Analysis" which shows statistics like average score, highest score, and pass percentage.
        
        Q: How do I mark attendance for a class?
        A: Go to the Attendance module, click on "Mark Attendance", select the class and section, and then mark present/absent for each student.
        
        Q: How do I schedule a new exam?
        A: Navigate to the Examination module, click on "Add Exam", fill in details like exam type, subject, date, and total marks, then save.
        """
        documents.append(faq_content)
        
        # Add information about grade evaluation feature
        grade_evaluation_info = """
        Grade Evaluation Feature:
        
        The Grade Evaluation feature allows teachers to evaluate student answers using AI assistance. The system uses Retrieval Augmented Generation (RAG) with the marking scheme as the knowledge base.
        
        How it works:
        1. Teachers upload or enter a marking scheme that includes question criteria, expected answers, and point allocation.
        2. They then upload or enter the student's answer that needs to be evaluated.
        3. The AI system analyzes the student's answer against the marking scheme using advanced natural language processing.
        4. The system generates a score, detailed analysis, and feedback explaining the evaluation.
        
        Key benefits:
        - Consistent grading across all students
        - Detailed feedback with specific points for improvement
        - Time-saving for teachers when grading large numbers of responses
        - AI-assisted evaluation that maintains teacher oversight
        """
        documents.append(grade_evaluation_info)
        
        conn.close()
        
        # If we couldn't get any data, add some default information about the system
        if not documents:
            documents.append("""
            School Management System Information:
            This is a comprehensive school management system that tracks students, teachers, classes, subjects, attendance, and examination results.
            It allows administrators to manage student records, track attendance, schedule exams, and generate reports.
            Teachers can record attendance, input exam results, and view student information.
            """)
        
        print(f"Total documents extracted: {len(documents)}")
        return documents
    
    def _create_vectorstore(self, documents):
        """Create a vector store from the documents"""
        # Split the documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Create text chunks
        texts = text_splitter.split_text("\n\n".join(documents))
        print(f"Created {len(texts)} text chunks from {len(documents)} documents")
        
        # Create the vector store
        vectorstore = FAISS.from_texts(texts, self.embeddings)
        print(f"Vector store created with {len(texts)} embeddings")
        
        return vectorstore
    
    def query(self, query_text):
        """
        Query the RAG system with the given text
        
        Args:
            query_text: The query string from the user
            
        Returns:
            dict: A dictionary containing the answer
        """
        # Check if the query is empty
        if not query_text or not query_text.strip():
            return {
                "answer": "Please ask a question to get started."
            }
        
        print(f"Processing RAG query: {query_text}")
        
        try:
            # First try to get documents from vector store
            try:
                docs = self.vectorstore.similarity_search(query_text, k=3)
                context = "\n\n".join([doc.page_content for doc in docs])
            except Exception as e:
                print(f"Error retrieving from vector store: {e}")
                context = "No specific information available."
                docs = []
            
            # Create a simple prompt
            prompt = f"""
            You are Jarvin AI, a helpful assistant for a school management system.
            
            Always respond in English only.
            
            Here is some context information that might help you answer:
            {context}
            
            User's question: {query_text}
            
            Please provide a helpful, accurate, and concise response based on the given context.
            If you don't know the answer or don't have enough information, be honest about it.
            """
            
            # Direct call to the LLM
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # In case answer is empty or too short
            if not answer or len(answer.strip()) < 5:
                # Try a simpler prompt
                fallback_prompt = f"You are a school management system assistant. Please answer the following question in English: {query_text}"
                try:
                    fallback_response = self.llm.invoke(fallback_prompt)
                    answer = fallback_response.content if hasattr(fallback_response, 'content') else str(fallback_response)
                except Exception as fallback_e:
                    print(f"Error in fallback LLM call: {fallback_e}")
                    answer = "I'm sorry, I'm having trouble generating a response right now."
            
            # Add a note if there was no context
            if not docs:
                answer += "\n\nNote: I couldn't access specific data from the school management system for this response."
            
            return {
                "answer": answer
            }
        except Exception as e:
            print(f"Error in RAG query: {str(e)}")
            return {
                "answer": "I encountered an error while processing your question. Please try again with a different question."
            }
    
    def _is_english(self, text):
        # Check for high prevalence of non-Latin characters
        non_latin = len(re.findall(r'[^\x00-\x7F]', text))
        latin = len(re.findall(r'[a-zA-Z]', text))
        
        # If more than 30% of characters are non-Latin, it might not be English
        if latin == 0:
            return False
        
        if non_latin / (non_latin + latin) > 0.3:
            return False
            
        return True
