import sqlite3

def create_admin():
    db = sqlite3.connect('python_sms.db')
    cursor = db.cursor()
    
    # Create admin user
    cursor.execute('''
        INSERT OR IGNORE INTO sms_user (
            first_name,
            email,
            password,
            type,
            status
        ) VALUES (?, ?, ?, ?, ?)
    ''', ('Admin', 'admin@example.com', 'admin123', 'admin', 'active'))
    
    db.commit()
    db.close()

if __name__ == "__main__":
    create_admin()
    print("Admin user created successfully!") 