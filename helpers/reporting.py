import io
import urllib.parse
import streamlit as st
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

@st.cache_data
def get_hourly_cycle_length(volume):
    """Get CVAG recommended cycle length based on volume"""
    if volume >= 2400:
        return "140 sec"
    elif volume >= 1500:
        return "130 sec"
    elif volume >= 600:
        return "120 sec"
    elif volume >= 300:
        return "110 sec"
    else:
        return "Free mode"

@st.cache_data
def get_existing_cycle_length(volume):
    """Get current system cycle length based on volume"""
    if volume >= 300:
        return "140 sec"
    else:
        return "Free mode"

@st.cache_data
def filter_by_period(df, time_col, period):
    """Filter dataframe by time period"""
    if period == "AM":
        return df[(df[time_col].dt.hour >= 5) & (df[time_col].dt.hour <= 10)]
    elif period == "MD":
        return df[(df[time_col].dt.hour >= 11) & (df[time_col].dt.hour <= 15)]
    elif period == "PM":
        return df[(df[time_col].dt.hour >= 16) & (df[time_col].dt.hour <= 20)]
    else:
        return df

def create_pdf_report(variable, date_range, chart_fig, data_source_info):
    """Create a PDF report with current screen info"""
    buffer = io.BytesIO()

    # Create PDF
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Add title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Traffic Data Report")

    # Add timestamp
    p.setFont("Helvetica", 10)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    p.drawString(50, height - 80, f"Generated: {timestamp}")

    # Add variable info
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 120, f"Variable: {variable}")
    p.drawString(50, height - 140, f"Date Range: {str(date_range)}")

    # Add data source (remove markdown formatting for PDF)
    data_source_clean = data_source_info.replace("✅ Data Source: [", "").replace("](", " - ").replace(")", "")
    p.drawString(50, height - 160, f"Data Source: {data_source_clean}")

    # Save chart as image and add to PDF
    if chart_fig:
        # Convert plotly figure to image
        img_bytes = chart_fig.to_image(format="png", width=500, height=300)
        img = ImageReader(io.BytesIO(img_bytes))
        p.drawImage(img, 50, height - 500, width=500, height=300)

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer

def generate_email_details(variable, date_range):
    """Generate email subject and body"""
    to_emails = "cortiz@advantec-usa.com;belenes@advantec-usa.com"
    subject = f"Traffic Data Report - {variable} - {datetime.now().strftime('%Y-%m-%d')}"
    body = f"""Hello,

Please find attached the traffic data report for:
- Variable: {variable}
- Date Range: {str(date_range)}
- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
Traffic Data System
"""
    mailto_url = f"mailto:{to_emails}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
    return to_emails, subject, body, mailto_url