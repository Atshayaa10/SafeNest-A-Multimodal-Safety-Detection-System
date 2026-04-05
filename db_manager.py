import psycopg2
from colorama import Fore, Style

class DatabaseManager:
    def __init__(self):
        self.conn_params = {
            "host": "localhost",
            "port": 5432,

            "dbname": "postgres",
            "user": "postgres",
            "password": "atshu@10",
            "connect_timeout": 10,
            "sslmode": "prefer"
        }
        # Test connectivity briefly on initialization, but don't crash
        try:
            self.init_db()
        except Exception:
            pass

    def get_connection(self):
        try:
            return psycopg2.connect(**self.conn_params)
        except Exception as e:
            # Silent failure for tests/background tasks to avoid console spam
            return None

    def is_connected(self):
        """Check if the database is reachable."""
        conn = self.get_connection()
        if conn:
            conn.close()
            return True
        return False

    def init_db(self):
        conn = self.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS safety_alerts (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    alert_type VARCHAR(50),
                    trigger_text TEXT,
                    confidence_score FLOAT,
                    reason TEXT
                );
            """)
            # Ensure frame_image column exists for older tables
            cursor.execute("ALTER TABLE safety_alerts ADD COLUMN IF NOT EXISTS frame_image TEXT;")
            conn.commit()
            print(f"{Fore.GREEN}[System] Database connection and table 'safety_alerts' successfully verified.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[DB Error] Could not initialize table: {e}{Style.RESET_ALL}")
        finally:
            conn.close()

    def log_alert(self, alert_type, trigger_text, confidence_score, reason, frame_image=None):
        conn = self.get_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO safety_alerts (alert_type, trigger_text, confidence_score, reason, frame_image)
                VALUES (%s, %s, %s, %s, %s)
            """, (alert_type, trigger_text, float(confidence_score), reason, frame_image))
            conn.commit()
        except Exception as e:
            print(f"{Fore.RED}[DB Error] Insert failed: {e}{Style.RESET_ALL}")
        finally:
            conn.close()

    def get_all_alerts(self):
        """Fetch all historical alerts for reporting."""
        conn = self.get_connection()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, alert_type, trigger_text, confidence_score, reason 
                FROM safety_alerts 
                ORDER BY timestamp DESC
            """)
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print(f"{Fore.RED}[DB Error] Fetch failed: {e}{Style.RESET_ALL}")
            return []
        finally:
            conn.close()

# Export a single global instance
db = DatabaseManager()
