import sys
import os
sys.path.append(os.getcwd())
from db_manager import db
from reporting_utils import generate_csv_report, generate_pdf_report
from datetime import datetime

# 1. Test data fetching
print("Testing DB Fetching...")
data = db.get_all_alerts()
print(f"Fetched {len(data)} alerts.")

# 2. Test CSV generation
print("\nTesting CSV Generation...")
sample_data = [[datetime.now(), "TEST", "Some trigger", 0.95, "Test reason"]]
csv_bytes = generate_csv_report(sample_data, ["Timestamp", "Type", "Trigger", "Confidence", "Reason"])
print(f"CSV generated. {len(csv_bytes)} bytes.")

# 3. Test PDF generation (if possible)
print("\nTesting PDF Generation...")
try:
    pdf_bytes = generate_pdf_report(sample_data)
    print(f"PDF generated. {len(pdf_bytes)} bytes.")
except Exception as e:
    print(f"PDF generation failed: {e}")
