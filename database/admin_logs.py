from database.db_manager import c, conn
from datetime import datetime

def log_admin_action(admin_id, action, target_id=None, details=""):
    c.execute('INSERT INTO admin_logs (admin_id, action, target_id, details, timestamp) VALUES (?, ?, ?, ?, ?)',
              (admin_id, action, target_id, details, datetime.now().isoformat()))
    conn.commit()