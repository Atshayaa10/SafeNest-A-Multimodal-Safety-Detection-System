import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io

def generate_csv_report(data, columns):
    """Generates a CSV from provided data and columns."""
    df = pd.DataFrame(data, columns=columns)
    return df.to_csv(index=False).encode('utf-8')

class SafetyPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, '🛡️ SafeNest Safety Audit Report', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'R')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(data):
    """Generates a professional PDF report from database rows."""
    pdf = SafetyPDF()
    pdf.add_page()
    
    # Summary Table
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Alert Summary History', 0, 1, 'L')
    pdf.ln(5)
    
    # Table Header
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 10, 'Timestamp', 1, 0, 'C', 1)
    pdf.cell(30, 10, 'Type', 1, 0, 'C', 1)
    pdf.cell(80, 10, 'Trigger Text', 1, 0, 'C', 1)
    pdf.cell(40, 10, 'Confidence', 1, 1, 'C', 1)
    
    # Table Body
    pdf.set_font('Arial', '', 9)
    for row in data:
        timestamp = str(row[0])[:19] # Truncate microseconds
        alert_type = str(row[1])
        trigger = str(row[2])[:40] + "..." if len(str(row[2])) > 40 else str(row[2])
        confidence = f"{row[3]*100:.1f}%"
        
        pdf.cell(40, 10, timestamp, 1)
        pdf.cell(30, 10, alert_type, 1)
        pdf.cell(80, 10, trigger, 1)
        pdf.cell(40, 10, confidence, 1, 1)
        
    return pdf.output(dest='S') # Return string/bytes
