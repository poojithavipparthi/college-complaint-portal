import os
import sys
import unittest

# Ensure current workspace directory is in sys.path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

import database
import ai_service
from app import app

class TestCollegeComplaintPortal(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db_path = os.path.join(PROJECT_DIR, 'college_complaints.db')
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass
        database.init_db()
        cls.client = app.test_client()
        app.config['TESTING'] = True

    def test_01_database_init(self):
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        conn.close()
        self.assertIn('users', tables)
        self.assertIn('complaints', tables)
        print("[OK] Database tables verified.")

    def test_02_admin_seed(self):
        user = database.authenticate_user('admin', 'admin123')
        self.assertIsNotNone(user)
        self.assertEqual(user['role'], 'admin')
        print("[OK] Seed admin authentication verified.")

    def test_03_student_registration_and_login(self):
        success, user_id = database.create_user('test_student', 'pass123', 'Test Student')
        self.assertTrue(success)
        
        user = database.authenticate_user('test_student', 'pass123')
        self.assertIsNotNone(user)
        self.assertEqual(user['full_name'], 'Test Student')
        print("[OK] Student registration & login verified.")

    def test_04_ai_classification(self):
        title = "The projector in Room 204 is not working and we have an exam tomorrow."
        desc = "The display is completely blank and we cannot see slides."
        result = ai_service.analyze_complaint_with_gemini(title, desc)
        
        self.assertIn('category', result)
        self.assertIn('priority', result)
        self.assertIn('department', result)
        self.assertIn('summary', result)
        self.assertIn(result['category'], ai_service.ALLOWED_CATEGORIES)
        self.assertIn(result['priority'], ai_service.ALLOWED_PRIORITIES)
        print(f"[OK] AI classification verified: Category={result['category']}, Priority={result['priority']}, Dept={result['department']}")

    def test_05_complaint_submission_and_id_generation(self):
        user = database.authenticate_user('test_student', 'pass123')
        title = "WiFi in hostel block B is disconnected"
        desc = "No signal on the 2nd floor since morning."
        
        analysis = ai_service.analyze_complaint_with_gemini(title, desc)
        complaint_id = database.create_complaint(
            user_id=user['id'],
            title=title,
            description=desc,
            category=analysis['category'],
            priority=analysis['priority'],
            department=analysis['department'],
            summary=analysis['summary']
        )
        
        self.assertTrue(complaint_id.startswith('CMP-'))
        print(f"[OK] Complaint creation verified with Ticket ID: {complaint_id}")

        # Check retrieval for user
        user_complaints = database.get_user_complaints(user['id'])
        self.assertEqual(len(user_complaints), 1)
        self.assertEqual(user_complaints[0]['complaint_id'], complaint_id)
        print("[OK] User complaints retrieval verified.")

    def test_06_admin_status_update(self):
        all_complaints = database.get_all_complaints()
        self.assertGreater(len(all_complaints), 0)
        target = all_complaints[0]
        
        success, msg = database.update_complaint_status(target['complaint_id'], 'In Progress')
        self.assertTrue(success)
        
        updated = database.get_complaint_by_id(target['complaint_id'])
        self.assertEqual(updated['status'], 'In Progress')
        print("[OK] Admin status update to 'In Progress' verified.")

        success, msg = database.update_complaint_status(target['complaint_id'], 'Resolved')
        self.assertTrue(success)
        
        updated = database.get_complaint_by_id(target['complaint_id'])
        self.assertEqual(updated['status'], 'Resolved')
        print("[OK] Admin status update to 'Resolved' verified.")

if __name__ == '__main__':
    unittest.main()
