import os
import sys

sys.path.insert(0, r"c:\Users\vpooj\Desktop\college-complaint-portal")

import database
import ai_service

def reset_and_seed():
    db_path = os.path.join(r"c:\Users\vpooj\Desktop\college-complaint-portal", 'college_complaints.db')
    if os.path.exists(db_path):
        os.remove(db_path)
    
    database.init_db()
    print("Database initialized.")

    # Create demo student account
    success, student_id = database.create_user('student1', 'student123', 'John Doe')
    if success:
        print("Created demo student: student1 / student123")

        # Create sample complaint 1
        title1 = "The projector in Room 204 is not working and we have an exam tomorrow."
        desc1 = "The display projector remains pitch black despite connecting via HDMI. Urgent fix needed before 9 AM exam."
        res1 = ai_service.analyze_complaint_with_gemini(title1, desc1)
        cmp1 = database.create_complaint(student_id, title1, desc1, res1['category'], res1['priority'], res1['department'], res1['summary'])
        print(f"Created sample complaint 1: {cmp1}")

        # Create sample complaint 2
        title2 = "Hostel Block C 3rd floor Wi-Fi router is offline"
        desc2 = "No internet access on 3rd floor since yesterday evening."
        res2 = ai_service.analyze_complaint_with_gemini(title2, desc2)
        cmp2 = database.create_complaint(student_id, title2, desc2, res2['category'], res2['priority'], res2['department'], res2['summary'])
        database.update_complaint_status(cmp2, 'In Progress')
        print(f"Created sample complaint 2: {cmp2}")

if __name__ == '__main__':
    reset_and_seed()
