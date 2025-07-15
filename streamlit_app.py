import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# PDF functionality imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import io
import base64
import webbrowser
import urllib.parse
import tempfile
import os

st.set_page_config(
    page_title="Transportation Dashboard",
    page_icon="📊",
    layout="wide"
)

# Initialize chart_type with default value
chart_type = "Line"

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


def send_email_with_pdf(pdf_buffer, variable, date_range):
    """Download PDF and open email client"""
    # Create download link for PDF
    pdf_data = pdf_buffer.getvalue()

    # Email details
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

    # Create mailto URL
    mailto_url = f"mailto:{to_emails}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

    # Create two buttons
    col1, col2 = st.columns(2)

    with col1:
        # Download PDF button
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_data,
            file_name=f"traffic_report_{variable}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with col2:
        # Open email button
        st.link_button(
            label="📧 Open Email Client",
            url=mailto_url,
            use_container_width=True
        )

    st.info(
        "💡 **Instructions:** Click 'Download PDF' first, then click 'Open Email' and attach the downloaded PDF file.")

    return None


# Add this to your Streamlit app layout (in the top right)
col1, col2, col3 = st.columns([2, 1, 1])

with col3:
    if st.button("📧 Send Email Report", use_container_width=True):
        # Toggle the email report visibility
        if 'show_email_report' not in st.session_state:
            st.session_state.show_email_report = True
        else:
            st.session_state.show_email_report = not st.session_state.show_email_report

    # Only show email report if toggled on
    if st.session_state.get('show_email_report', False):
        try:
            # Get current chart figure
            current_chart = st.session_state.get('current_chart', None)

            # Create PDF
            if st.session_state.data_source == "GitHub Repository":
                date_info = st.session_state.date_range
            elif st.session_state.data_source == "Uploaded CSV":
                date_info = "Data from uploaded CSV"
            else:  # API Connection
                date_info = "API Data Range"

            pdf_buffer = create_pdf_report(
                variable=st.session_state.variable,
                date_range=date_info,
                chart_fig=current_chart,
                data_source_info=f"Data Source: {st.session_state.data_source}"
            )

            # Send email
            send_email_with_pdf(pdf_buffer, st.session_state.variable, date_info)

        except Exception as e:
            st.error(f"Error creating email report: {str(e)}")


# App title
st.title("📊 Active Transportation & Operations Management Dashboard")

# === SIDEBAR ===
with st.sidebar:
    st.image("Logos/ACE-logo-HiRes.jpg", width=210)
    st.image("Logos/CV Sync__.jpg", width=205)


    # === 1. DATA SOURCE SELECTION ===
    st.markdown("## 📊 Data Source")
    data_source = st.radio(
    "Choose your data source:",
    ["GitHub Repository", "Uploaded CSV", "API Connection"],
    key="data_source"
)
    # === 2. DASHBOARD FILTERS ===
    st.markdown("## 🔍 Dashboard Filters")

    # Category selection (same for all data sources)
    variable = st.selectbox(
        "SELECT CATEGORY",
        ["Vehicle Volume", "Speed", "Travel Time"],
        key="variable"
    )

    # Direction selection (same for all data sources)
    direction = st.radio(
        "Direction",
        ["NB", "SB", "Both"],
        index=1,  # Default to SB
        key="direction"
    )

    # Date range selection (GitHub only, API will have different logic)
    if data_source == "GitHub Repository":
        if variable == "Vehicle Volume":
            date_options = ["April 10, 2025", "Feb 13, 2025"]
        else:  # Speed or Travel Time
            date_options = ["April 11–20, 2025", "May 9–18, 2025"]

        date_range = st.selectbox(
            "Select Date Range",
            date_options,
            key="date_range"
        )

    # === 3. KPI SETTINGS ===
    st.markdown("## ⚙️ KPI Settings")
    time_period = st.selectbox(
        "Time Period",
        ["AM (5:00-10:00)", "MD (11:00-15:00)", "PM (16:00-20:00)"],
        index=0,
        key="time_period"
    )

# === CSV UPLOAD SECTION ===
if data_source == "Uploaded CSV":
    st.markdown("## ⬆️ Upload CSV Files")

    # Initialize session state for uploaded files
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {}

    # File uploader
    uploaded_file = st.file_uploader(
        "Drag and drop CSV files here",
        type=['csv'],
        accept_multiple_files=False,
        help="Maximum file size: 200MB"
    )

    # Store uploaded file
    if uploaded_file is not None:
        st.session_state.uploaded_files[uploaded_file.name] = uploaded_file
        st.success(f"✅ {uploaded_file.name} uploaded successfully!")

    # File selection dropdown
    if st.session_state.uploaded_files:
        file_options = ["Select uploaded file..."] + list(st.session_state.uploaded_files.keys())
        selected_file = st.selectbox(
            "Select file to analyze:",
            file_options,
            key="selected_file"
        )

        # === 3. COLUMN MAPPING ===
        if selected_file != "Select uploaded file...":
            st.markdown("## 🧩 Map Your Columns")

            # Check if selected file exists in uploaded files
            if selected_file not in st.session_state.uploaded_files:
                st.error("Selected file not found in uploaded files")
                st.stop()

            try:
                # Load the selected file with better error handling
                file_obj = st.session_state.uploaded_files[selected_file]
                file_obj.seek(0)  # Reset file pointer to beginning
                df = pd.read_csv(file_obj, encoding='utf-8')

                # Check if dataframe is empty
                if df.empty:
                    st.error("The selected file contains no data")
                    st.stop()

            except UnicodeDecodeError:
                try:
                    file_obj.seek(0)  # Reset file pointer again
                    df = pd.read_csv(file_obj, encoding='latin-1')
                    if df.empty:
                        st.error("The selected file contains no data")
                        st.stop()
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
                    st.stop()
            except pd.errors.EmptyDataError:
                st.error("The file appears to be empty or contains no parseable data")
                st.stop()
            except Exception as e:
                st.error(f"Error processing uploaded file: {str(e)}")
                st.stop()

            # Column mapping dropdowns
            date_column = st.selectbox(
                "Select column for date:",
                ["Select column..."] + list(df.columns),
                key="date_column"
            )

            # Auto-detect data format
            nb_cols = [col for col in df.columns if
                       'NB' in col.upper() and any(word in col.lower() for word in ['speed', 'volume', 'count'])]
            sb_cols = [col for col in df.columns if
                       'SB' in col.upper() and any(word in col.lower() for word in ['speed', 'volume', 'count'])]
            has_directional_cols = len(nb_cols) > 0 and len(sb_cols) > 0

            if has_directional_cols:
                st.info("📊 Detected directional columns (NB/SB format)")
                data_format = st.radio(
                    "Select data format:",
                    ["Wide format (NB/SB columns)", "Long format (separate direction column)"],
                    key="data_format"
                )
            else:
                data_format = "Long format (separate direction column)"

            if data_format == "Wide format (NB/SB columns)":
                # For wide format data
                st.subheader("Select directional columns:")
                nb_column = st.selectbox(
                    "Northbound (NB) column:",
                    ["Select column..."] + [col for col in df.columns if col != date_column],
                    key="nb_column"
                )
                sb_column = st.selectbox(
                    "Southbound (SB) column:",
                    ["Select column..."] + [col for col in df.columns if col != date_column and col != nb_column],
                    key="sb_column"
                )

                # Validation for wide format
                if date_column == "Select column..." or nb_column == "Select column..." or sb_column == "Select column...":
                    st.warning("⚠️ Please map all columns to continue")
                    st.stop()

                # Transform data to your preferred format
                if nb_column and sb_column:
                    # Get the unit (mph, km/h, etc.)
                    unit = "mph"  # default
                    unit_col = None
                    for col in df.columns:
                        if 'unit' in col.lower():
                            unit_col = col
                            if not df[col].empty:
                                unit = df[col].iloc[0]  # Get the first unit value
                            break

                    # Create the new clean format
                    df_clean = pd.DataFrame()
                    df_clean[date_column] = df[date_column]
                    df_clean[f'Daily Avg Speed: NB ({unit})'] = df[nb_column]
                    df_clean[f'Daily Avg Speed: SB ({unit})'] = df[sb_column]

                    # Use the cleaned data
                    df = df_clean

                    # For internal processing, we still need to create the long format
                    # but we'll use the clean column names
                    df_long = pd.melt(df,
                                      id_vars=[date_column],
                                      value_vars=[f'Daily Avg Speed: NB ({unit})', f'Daily Avg Speed: SB ({unit})'],
                                      var_name='direction',
                                      value_name='variable')

                    # Clean up direction names for internal processing
                    df_long['direction'] = df_long['direction'].apply(
                        lambda x: 'NB' if 'NB' in x else 'SB'
                    )

                    # Keep both formats - clean for display, long for processing
                    df_display = df  # Clean format for user
                    df = df_long  # Long format for internal processing
                    direction_column = 'direction'
                    variable_column = 'variable'

                    # Determine variable type
                    if any(word in nb_column.lower() for word in ['speed', 'mph', 'velocity']):
                        variable = "Speed"
                    elif any(word in nb_column.lower() for word in ['volume', 'count', 'traffic']):
                        variable = "Volume"
                    else:
                        variable = "Speed"  # Default

                    # Show preview of the CLEAN data format
                    st.success(f"✅ Data transformed successfully! Variable type: {variable}")
                    with st.expander("Preview transformed data"):
                        st.dataframe(df_display.head())
            else:
                # For long format data
                direction_column = st.selectbox(
                    "Select column for direction:",
                    ["Select column..."] + [col for col in df.columns if col != date_column],
                    key="direction_column"
                )

                variable_column = st.selectbox(
                    "Select column for variable:",
                    ["Select column..."] + [col for col in df.columns if
                                            col != date_column and col != direction_column],
                    key="variable_column"
                )

                # Validation for long format
                if date_column == "Select column..." or direction_column == "Select column..." or variable_column == "Select column...":
                    st.warning("⚠️ Please map all columns to continue")
                    st.stop()
    else:
        st.info("📁 No files uploaded yet. Upload a CSV file to get started.")
        st.stop()

# === API CONNECTION SECTION ===
elif data_source == "API Connection":
    st.markdown("## 🔌 API Configuration")

    # API Type Selection
    api_type = st.selectbox(
        "Select API Type:",
        ["REST API", "GraphQL", "Database API", "Custom Endpoint"],
        key="api_type"
    )

    # API Configuration
    if api_type == "REST API":
        api_url = st.text_input(
            "API Endpoint URL:",
            placeholder="https://api.example.com/traffic-data",
            key="api_url"
        )

        # Authentication
        auth_method = st.selectbox(
            "Authentication Method:",
            ["None", "API Key", "Bearer Token", "Basic Auth"],
            key="auth_method"
        )

        if auth_method == "API Key":
            api_key = st.text_input(
                "API Key:",
                type="password",
                placeholder="Enter your API key",
                key="api_key"
            )
            key_header = st.text_input(
                "Header Name:",
                value="X-API-Key",
                key="key_header"
            )

        elif auth_method == "Bearer Token":
            bearer_token = st.text_input(
                "Bearer Token:",
                type="password",
                placeholder="Enter your bearer token",
                key="bearer_token"
            )

        elif auth_method == "Basic Auth":
            username = st.text_input("Username:", key="api_username")
            password = st.text_input("Password:", type="password", key="api_password")

        # Query Parameters
        with st.expander("🔧 Query Parameters (Optional)"):
            st.text_area(
                "Parameters (JSON format):",
                placeholder='{"date_from": "2025-01-01", "date_to": "2025-12-31"}',
                key="query_params"
            )

        # Test Connection
        if st.button("🔍 Test API Connection"):
            st.info("Testing API connection... (Feature coming soon)")
            # Future: Implement actual API testing

    elif api_type == "Database API":
        db_type = st.selectbox(
            "Database Type:",
            ["PostgreSQL", "MySQL", "SQLite", "MongoDB"],
            key="db_type"
        )

        connection_string = st.text_input(
            "Connection String:",
            type="password",
            placeholder="postgresql://user:password@host:port/database",
            key="connection_string"
        )

        query = st.text_area(
            "SQL Query:",
            placeholder="SELECT date, direction, speed FROM traffic_data WHERE date >= '2025-01-01'",
            key="sql_query"
        )

    # Data Mapping for API
    st.markdown("## 🧩 API Data Mapping")
    st.info("🚧 Configure how API response maps to your data structure (Feature coming soon)")

    # Placeholder for future API mapping
    with st.expander("📝 Response Structure"):
        st.code("""
        Expected API Response Format:
        {
            "data": [
                {
                    "date": "2025-01-01T10:00:00Z",
                    "direction": "NB",
                    "value": 45.5
                }
            ]
        }
        """)

    st.warning("🚧 API integration coming in future update!")
    st.stop()


# === Filepath Mapping Logic ===
base_url = "https://raw.githubusercontent.com/chrquija/Advantec-Dashboard-app/refs/heads/main/hwy111_to_ave52/"
corridor_segment = "Washington St: Highway 111 to Avenue 52"

path_map = {
    # === SPEED ===
    ("Speed", "NB",
     "April 11–20, 2025"): base_url + "SPEED/Weeks_04112025_to_04202025/NB_Washington_Avenue_52_to_Hwy_111_SPEED_1hr_0411_04202025.csv",
    ("Speed", "SB",
     "April 11–20, 2025"): base_url + "SPEED/Weeks_04112025_to_04202025/SB_Washington_Hwy_111_to_Avenue_52_SPEED_1hr_0411_04202025.csv",
    ("Speed", "Both", "April 11–20, 2025"): "BOTH",

    ("Speed", "NB",
     "May 9–18, 2025"): base_url + "SPEED/Weeks_05092025_to_05182025/NB_Washington_Avenue_52_to_Hwy_111_%20SPEED_1hr_0509_05182025.csv",
    ("Speed", "SB",
     "May 9–18, 2025"): base_url + "SPEED/Weeks_05092025_to_05182025/SB_Washington_Hwy%20111_to_Avenue%2052_SPEED_1hr_0509_05182025.csv",
    ("Speed", "Both", "May 9–18, 2025"): "BOTH",

    # === TRAVEL TIME ===
    ("Travel Time", "NB",
     "April 11–20, 2025"): base_url + "TRAVEL_TIME/Weeks_04112025_to_04202025/NB_Washington_Avenue_52_to_Hwy_111_TRAVEL_TIME_1hr_0411_04202025.csv",
    ("Travel Time", "SB",
     "April 11–20, 2025"): base_url + "TRAVEL_TIME/Weeks_04112025_to_04202025/SB_Washington_Hwy_111_to_Avenue_52_TRAVEL_TIME_1hr_0411_04202025.csv",
    ("Travel Time", "Both", "April 11–20, 2025"): "BOTH",

    ("Travel Time", "NB",
     "May 9–18, 2025"): base_url + "TRAVEL_TIME/Weeks_05092025_to_05182025/NB_Washington_Avenue_52_to_Hwy_111_TRAVEL_TIME_1_hr_0509_05182025.csv",
    ("Travel Time", "SB",
     "May 9–18, 2025"): base_url + "TRAVEL_TIME/Weeks_05092025_to_05182025/SB_Washington_Hwy_111_to_Avenue_52_TRAVEL_TIME_1_hr_0509_05182025.csv",
    ("Travel Time", "Both", "May 9–18, 2025"): "BOTH",

    # === VEHICLE VOLUME (April 10) — All 3 use same file ===
    ("Vehicle Volume", "NB",
     "April 10, 2025"): base_url + "VOLUME/Thursday_April_10/Washington_and_Ave_52_NB_and_SB_VolumeDATA_THURSDAY_APRIL_10.csv",
    ("Vehicle Volume", "SB",
     "April 10, 2025"): base_url + "VOLUME/Thursday_April_10/Washington_and_Ave_52_NB_and_SB_VolumeDATA_THURSDAY_APRIL_10.csv",
    ("Vehicle Volume", "Both",
     "April 10, 2025"): base_url + "VOLUME/Thursday_April_10/Washington_and_Ave_52_NB_and_SB_VolumeDATA_THURSDAY_APRIL_10.csv",

    # === VEHICLE VOLUME (Feb 13) — All 3 use same file ===
    ("Vehicle Volume", "NB",
     "Feb 13, 2025"): base_url + "VOLUME/Thursday_Feb_13/Washington_and_Ave_52_NB_and_SB_VolumeDATA_Thursday_Feb_13.csv",
    ("Vehicle Volume", "SB",
     "Feb 13, 2025"): base_url + "VOLUME/Thursday_Feb_13/Washington_and_Ave_52_NB_and_SB_VolumeDATA_Thursday_Feb_13.csv",
    ("Vehicle Volume", "Both",
     "Feb 13, 2025"): base_url + "VOLUME/Thursday_Feb_13/Washington_and_Ave_52_NB_and_SB_VolumeDATA_Thursday_Feb_13.csv",
}

# Define date_range if not already defined
if 'date_range' not in locals():
    date_range = "uploaded_file"

selected_path = path_map.get((variable, direction, date_range), "No path available for selection.")

# === EXTENSIBLE DATA LOADING SYSTEM (helps the sidebar do its job) ===

class DataLoader:
    """Centralized data loading system supporting multiple sources"""

    @staticmethod
    def load_github_data(url):
        """Load data from GitHub repository"""
        try:
            if url == "BOTH":
                return None
            return pd.read_csv(url)
        except Exception as e:
            st.error(f"Error loading GitHub data: {e}")
            return None

    @staticmethod
    def load_uploaded_data(file_obj, date_col, direction_col, variable_col, data_format="Long format", nb_col=None,
                           sb_col=None):
        """Load and process uploaded CSV data"""
        try:
            # Reset file pointer to beginning
            file_obj.seek(0)

            # Try to read the CSV with error handling
            try:
                df = pd.read_csv(file_obj)
            except pd.errors.EmptyDataError:
                st.error("The uploaded file is empty or contains no data")
                return None
            except pd.errors.ParserError as e:
                st.error(f"Error parsing CSV file: {e}")
                return None

            # Check if dataframe is empty
            if df.empty:
                st.error("The uploaded file contains no data rows")
                return None

            # Display first few rows for debugging
            st.write("**First few rows of uploaded data:**")
            st.dataframe(df.head())

            # Check if required columns exist
            if data_format == "Wide format (NB/SB columns)":
                if nb_col is None or sb_col is None:
                    st.error("NB and SB columns must be specified for wide format")
                    return None

                missing_cols = []
                for col in [date_col, nb_col, sb_col]:
                    if col not in df.columns:
                        missing_cols.append(col)

                if missing_cols:
                    st.error(f"Missing columns in uploaded file: {missing_cols}")
                    st.write(f"Available columns: {list(df.columns)}")
                    return None

                # Keep only the required columns
                df = df[[date_col, nb_col, sb_col]]

                # Rename date column
                df = df.rename(columns={date_col: 'Date'})

                # Convert to long format
                df_melted = df.melt(
                    id_vars=['Date'],
                    value_vars=[nb_col, sb_col],
                    var_name='Direction',
                    value_name='Value'
                )

                # Map column names to direction labels
                direction_map = {nb_col: 'NB', sb_col: 'SB'}
                df_melted['Direction'] = df_melted['Direction'].map(direction_map)

                df = df_melted

            else:
                # Handle long format data
                missing_cols = []
                for col in [date_col, direction_col, variable_col]:
                    if col not in df.columns:
                        missing_cols.append(col)

                if missing_cols:
                    st.error(f"Missing columns in uploaded file: {missing_cols}")
                    st.write(f"Available columns: {list(df.columns)}")
                    return None

                df = df.rename(columns={
                    date_col: 'Date',
                    direction_col: 'Direction',
                    variable_col: 'Value'
                })

            # Convert date column to datetime
            try:
                df['Date'] = pd.to_datetime(df['Date'])
            except Exception as e:
                st.error(f"Error converting date column: {e}")
                return None

            return df

        except Exception as e:
            st.error(f"Error processing uploaded file: {str(e)}")
            return None

    @staticmethod
    def load_api_data(api_config):
        """Load data from API (Future implementation)"""
        # This will be implemented when API feature is ready
        try:
            if api_config.get('type') == 'REST API':
                return DataLoader._load_rest_api(api_config)
            elif api_config.get('type') == 'Database API':
                return DataLoader._load_database_api(api_config)
            else:
                st.error("Unsupported API type")
                return None
        except Exception as e:
            st.error(f"Error loading API data: {e}")
            return None

    @staticmethod
    def _load_rest_api(config):
        """Load data from REST API"""
        # Future implementation
        import requests

        headers = {}
        if config.get('auth_method') == 'API Key':
            headers[config.get('key_header')] = config.get('api_key')
        elif config.get('auth_method') == 'Bearer Token':
            headers['Authorization'] = f"Bearer {config.get('bearer_token')}"

        response = requests.get(config.get('url'), headers=headers)
        # Process response and return DataFrame
        return pd.DataFrame(response.json().get('data', []))

    @staticmethod
    def _load_database_api(config):
        """Load data from database"""
        # Future implementation with SQLAlchemy
        # import sqlalchemy
        # engine = sqlalchemy.create_engine(config.get('connection_string'))
        # return pd.read_sql(config.get('query'), engine)
        pass


# === MAIN DATA LOADING WITH ROUTER ===
def load_data_by_source(data_source, **kwargs):
    """Load data based on selected source"""
    loader = DataLoader()

    if data_source == "GitHub Repository":
        return loader.load_github_data(kwargs.get('url'))

    elif data_source == "Uploaded CSV":
        return loader.load_uploaded_data(
            kwargs.get('file_obj'),
            kwargs.get('date_col'),
            kwargs.get('direction_col'),
            kwargs.get('variable_col'),
            kwargs.get('data_format', 'Long format'),
            kwargs.get('nb_col'),
            kwargs.get('sb_col')
        )

    elif data_source == "API Connection":
        return loader.load_api_data(kwargs.get('api_config'))

    else:
        st.error(f"Unknown data source: {data_source}")
        return None


# === USAGE IN MAIN APP ===
if data_source == "GitHub Repository":
    # Existing GitHub logic
    selected_path = path_map.get((variable, direction, date_range), "No path available for selection.")

    if selected_path == "No path available for selection.":
        st.error("No data available for the selected combination.")
        st.stop()
    elif selected_path == "BOTH":
        # Handle "Both" direction
        nb_path = path_map.get((variable, "NB", date_range))
        sb_path = path_map.get((variable, "SB", date_range))

        if nb_path and sb_path:
            df_nb = load_data_by_source("GitHub Repository", url=nb_path)
            df_sb = load_data_by_source("GitHub Repository", url=sb_path)

            if df_nb is not None and df_sb is not None:
                df = pd.concat([df_nb, df_sb], ignore_index=True)
            else:
                st.error("Error loading data for both directions.")
                st.stop()
        else:
            st.error("Data not available for both directions.")
            st.stop()
    else:
        df = load_data_by_source("GitHub Repository", url=selected_path)
        if df is None:
            st.stop()

elif data_source == "Uploaded CSV":
    # Validate file selection before accessing
    if selected_file == "Select uploaded file..." or selected_file not in st.session_state.uploaded_files:
        st.error("Please select a valid uploaded file")
        st.stop()

    df = load_data_by_source(
        "Uploaded CSV",
        file_obj=st.session_state.uploaded_files[selected_file],
        date_col=date_column,
        direction_col=direction_column,
        variable_col=variable_column,
        data_format=data_format,
        nb_col=nb_column if data_format == "Wide format (NB/SB columns)" else None,
        sb_col=sb_column if data_format == "Wide format (NB/SB columns)" else None
    )

    if df is None:
        st.stop()

    # Filter by direction if not "Both"
    if direction != "Both":
        df = df[df['Direction'] == direction]

elif data_source == "API Connection":
    # Future API implementation
    api_config = {
        'type': api_type,
        'url': api_url if 'api_url' in locals() else None,
        'auth_method': auth_method if 'auth_method' in locals() else None,
        # Add other API config parameters
    }

    df = load_data_by_source("API Connection", api_config=api_config)
    if df is None:
        st.stop()

#Create Unit Helper Functions for appropriate Units for each Variable Type
def get_units(variable):
    """Get the appropriate units for each variable type"""
    units_map = {
        "Vehicle Volume": "Vehicles",
        "Speed": "mph",
        "Travel Time": "mins"
    }
    return units_map.get(variable, "")

def format_value_with_units(value, variable):
    """Format value with appropriate units"""
    units = get_units(variable)
    return f"{value:.2f} {units}"
# end of Creating Unit Helper Functions code

# === Enhanced Chart Creation Function ===
def create_enhanced_line_chart(df, x_col, y_col, chart_title, color_name="blue"):
    """Create an enhanced line chart with day shading and peak/low annotations"""
    
    # Create the base figure using Graph Objects for more control
    fig = go.Figure()

    # Add the main line trace
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='lines+markers',
        name=color_name.title(),
        line=dict(color=color_name, width=2),
        marker=dict(size=4)
    ))

    # Add alternating day shading
    if not df.empty:
        # Get date range
        start_date = df[x_col].min().date()
        end_date = df[x_col].max().date()
        
        # Create alternating day bands
        current_date = start_date
        shade_toggle = True
        
        while current_date <= end_date:
            if shade_toggle:
                fig.add_vrect(
                    x0=current_date,
                    x1=current_date + timedelta(days=1),
                    fillcolor="lightgray",
                    opacity=0.1,
                    layer="below",
                    line_width=0,
                )
            shade_toggle = not shade_toggle
            current_date += timedelta(days=1)
    
    # Find top 5 highest and lowest points
    if len(df) >= 5:
        # Get indices of top 5 highest and lowest values
        highest_indices = df[y_col].nlargest(5).index
        lowest_indices = df[y_col].nsmallest(5).index

        # Add annotations for highest points (orange with up arrow) - LARGER SIZE
        for i, idx in enumerate(highest_indices):
            fig.add_annotation(
                x=df.loc[idx, x_col],
                y=df.loc[idx, y_col],
                text=f"▲ {df.loc[idx, y_col]:.2f}",
                showarrow=True,
                arrowhead=3,  # Increased from 2
                arrowsize=1.5,  # Increased from 1
                arrowwidth=3,  # Increased from 2
                arrowcolor="orange",
                ax=0,
                ay=-35 - (i * 12),  # Increased spacing from -30 and 10
                bgcolor="rgba(0,0,0,0.9)",  # Slightly more opaque
                bordercolor="orange",
                borderwidth=3,  # Increased from 2
                font=dict(color="orange", size=14),  # Increased from 10
                opacity=0.95  # Increased from 0.9
            )

            # Add annotations for lowest points (pink with down arrow) - LARGER SIZE
            for i, idx in enumerate(lowest_indices):
                fig.add_annotation(
                    x=df.loc[idx, x_col],
                    y=df.loc[idx, y_col],
                    text=f"▼ {df.loc[idx, y_col]:.2f}",
                    showarrow=True,
                    arrowhead=3,  # Increased from 2
                    arrowsize=1.5,  # Increased from 1
                    arrowwidth=3,  # Increased from 2
                    arrowcolor="hotpink",
                    ax=0,
                    ay=35 + (i * 12),  # Increased spacing from 30 and 10
                    bgcolor="rgba(0,0,0,0.9)",  # Slightly more opaque
                    bordercolor="hotpink",
                    borderwidth=3,  # Increased from 2
                    font=dict(color="hotpink", size=14),  # Increased from 10
                    opacity=0.95  # Increased from 0.9
                )

    # Update layout with prominent title
    fig.update_layout(
        title=dict(
            text=chart_title,
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=18, color="darkblue", family="Arial Black")
        ),
        xaxis_title="Time",
        yaxis_title="Vehicle Volume" if "Vehicle Volume" in chart_title else y_col,  # Fixed Y-axis title
        hovermode='x unified',
        showlegend=True,
        plot_bgcolor='white',
        margin=dict(t=80, b=50, l=50, r=50),
        height=500
    )
    
    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="lightgray",
        showline=True,
        linewidth=1,
        linecolor="black"
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="lightgray",
        showline=True,
        linewidth=1,
        linecolor="black"
    )
    
    return fig

def create_enhanced_multi_line_chart(df, x_col, y_cols, chart_title):
    """Create an enhanced multi-line chart for 'Both' direction data"""
    
    fig = go.Figure()
    
    colors = ["blue", "red"]
    
    # Add traces for each direction
    for i, col in enumerate(y_cols):
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[col],
            mode='lines+markers',
            name=col,
            line=dict(color=colors[i], width=2),
            marker=dict(size=4)
        ))
    
    # Add alternating day shading
    if not df.empty:
        start_date = df[x_col].min().date()
        end_date = df[x_col].max().date()
        
        current_date = start_date
        shade_toggle = True
        
        while current_date <= end_date:
            if shade_toggle:
                fig.add_vrect(
                    x0=current_date,
                    x1=current_date + timedelta(days=1),
                    fillcolor="lightgray",
                    opacity=0.1,
                    layer="below",
                    line_width=0,
                )
            shade_toggle = not shade_toggle
            current_date += timedelta(days=1)
    
    # Add annotations for each line's peaks and lows
    for i, col in enumerate(y_cols):
        if len(df) >= 3:  # Reduced to top 3 for multi-line to avoid clutter
            highest_indices = df[col].nlargest(3).index
            lowest_indices = df[col].nsmallest(3).index

            # Peaks - LARGER SIZE
            for j, idx in enumerate(highest_indices):
                fig.add_annotation(
                    x=df.loc[idx, x_col],
                    y=df.loc[idx, col],
                    text=f"▲ {df.loc[idx, col]:.2f}",
                    showarrow=True,
                    arrowhead=3,  # Increased from 2
                    arrowsize=1.3,  # Increased
                    arrowwidth=2.5,  # Increased
                    arrowcolor=colors[i],
                    ax=0,
                    ay=-30 - (j * 10),
                    bgcolor="rgba(0,0,0,0.9)",  # More opaque
                    bordercolor=colors[i],
                    borderwidth=2,
                    font=dict(color=colors[i], size=12),  # Increased from 9
                    opacity=0.9  # Increased from 0.8
                )

            # Lows - LARGER SIZE
            for j, idx in enumerate(lowest_indices):
                fig.add_annotation(
                    x=df.loc[idx, x_col],
                    y=df.loc[idx, col],
                    text=f"▼ {df.loc[idx, col]:.2f}",
                    showarrow=True,
                    arrowhead=3,  # Increased from 2
                    arrowsize=1.3,  # Increased
                    arrowwidth=2.5,  # Increased
                    arrowcolor=colors[i],
                    ax=0,
                    ay=30 + (j * 10),
                    bgcolor="rgba(0,0,0,0.9)",  # More opaque
                    bordercolor=colors[i],
                    borderwidth=2,
                    font=dict(color=colors[i], size=12),  # Increased from 9
                    opacity=0.9  # Increased from 0.8
                )

    # Update layout
    fig.update_layout(
        title=dict(
            text=chart_title,
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=18, color="darkblue", family="Arial Black")
        ),
        xaxis_title="Time",
        yaxis_title="Vehicle Volume" if "Vehicle Volume" in chart_title else "Value",  # Fixed Y-axis title
        hovermode='x unified',
        showlegend=True,
        plot_bgcolor='white',
        margin=dict(t=80, b=50, l=50, r=50),
        height=500
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")

    st.session_state['current_chart'] = fig  # store chart in session state so email function can access it later.

    return fig


# === CHART TITLE SECTION ===
st.markdown("---")


# Define helper function for finding columns
def find_column(df, patterns):
    """Find column that matches any of the patterns (case-insensitive)"""
    for pattern in patterns:
        for col in df.columns:
            if pattern.lower() in col.lower():
                return col
    return None


def determine_location_type_and_info():
    """Determine if viewing intersection or corridor data"""
    # You can customize this logic based on your data structure
    # For now, I'll assume intersection data - you can modify this
    is_intersection = True  # Change this logic based on your data

    if is_intersection:
        return {
            'type': 'intersection',
            'location': 'Washington St & Ave 52, La Quinta, California',
            'segment_label': 'Intersection:',
            'segment_info': 'Washington St & Ave 52'
        }
    else:
        return {
            'type': 'corridor',
            'location': 'Washington St, La Quinta, California',
            'segment_label': 'Corridor Segment:',
            'segment_info': 'Washington St: Highway 111 to Avenue 52'
        }


def determine_data_source(variable, date_range):
    """Determine data source based on variable type and date range"""
    # Convert date_range to string for checking
    date_str = str(date_range).lower()

    if variable == "Vehicle Volume":
        # Check if date range includes April 10, 2025 or Feb 13, 2025
        target_dates = ['2025-04-10', '2025-02-13', 'april 10, 2025', 'feb 13, 2025',
                        '04-10-2025', '02-13-2025', '10-04-2025', '13-02-2025']
        if any(date in date_str for date in target_dates):
            return "✅ Data Source: [Kinetic Mobility](http://172.29.100.200)"

    elif variable in ["Speed", "Travel Time"]:
        # Check for April 2025 and May 2025
        april_2025 = 'april' in date_str and '2025' in date_str
        may_2025 = 'may' in date_str and '2025' in date_str

        # Check for specific date ranges
        april_dates = [f'2025-04-{day:02d}' for day in range(11, 21)]
        may_dates = [f'2025-05-{day:02d}' for day in range(9, 19)]

        # Check alternative formats
        april_dates_alt = [f'04-{day:02d}-2025' for day in range(11, 21)]
        may_dates_alt = [f'05-{day:02d}-2025' for day in range(9, 19)]

        # Check if any of these dates are in the string
        april_match = any(date in date_str for date in april_dates + april_dates_alt)
        may_match = any(date in date_str for date in may_dates + may_dates_alt)

        if april_2025 or may_2025 or april_match or may_match:
            return "✅ Data Source: [Acyclica](https://go.acyclica.com/)"

    # Default fallback
    return "❗ Data Source: Unknown"


def determine_aggregation_type(variable, date_range):
    """Determine aggregation type based on variable and date range"""
    # You can customize this logic based on your needs
    return "Hourly Aggregated"  # or whatever logic you want for the title


# Create a more prominent title section
col1, col2 = st.columns([3, 1])

with col1:
    # Get location information
    location_info = determine_location_type_and_info()

    # Generate dynamic title based on selections
    corridor_info = location_info['location']
    aggregation_info = determine_aggregation_type(variable, date_range)
    data_source_info = determine_data_source(variable, date_range)

    if direction == "Both":
        if variable == "Vehicle Volume":
            base_title = f"{variable} - Northbound & Southbound"
        else:
            base_title = f"{variable} - Northbound & Southbound"
    else:
        direction_full = "Northbound" if direction == "NB" else "Southbound"
        base_title = f"{variable} - {direction_full}"

    # Add corridor and aggregation info to title
    full_title = f"{base_title} • {corridor_info}"

    # Handle subtitle creation safely
    subtitle = f"{aggregation_info} Data • {date_range}"

    # Display the title with custom styling
    st.markdown(f"""
    <div style="
        padding: 20px;
        background: linear-gradient(90deg, #1f4e79 0%, #2980b9 100%);
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    ">
        <h2 style="
            color: white;
            margin: 0;
            font-family: 'Arial', sans-serif;
            font-weight: 600;
            text-align: center;
            font-size: 22px;
            line-height: 1.2;
        ">{full_title}</h2>
        <p style="
            color: #e8f4fd;
            margin: 8px 0 0 0;
            text-align: center;
            font-size: 14px;
            font-style: italic;
        ">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

# Replace the determine_aggregation_type function call with determine_data_source
data_source_info = determine_data_source(variable, date_range)

# Store location info for use in location details section
st.session_state.location_info = location_info

# Get location info from session state
segment_label = st.session_state.location_info['segment_label']
segment_info = st.session_state.location_info['segment_info']

with col2:
    # Add corridor and data info (with data source instead of aggregation)
    st.markdown("**🌐 Location Details:**")
    st.caption(f"🛣️ {segment_label} {segment_info}")
    st.caption("🏙️City and State: La Quinta, California")
    st.caption(f"{data_source_info}")  # Data source info instead of aggregation info

    # CHART TYPE SELECTOR
    if data_source in ["GitHub Repository", "Uploaded CSV"]:
        # Theme-responsive gradient styling for just this selectbox
        st.markdown("""
        <style>
        .chart-type-selector .stSelectbox > div > div {
            background: linear-gradient(90deg, 
                color-mix(in srgb, var(--background-color) 95%, var(--text-color) 5%) 0%, 
                color-mix(in srgb, var(--background-color) 90%, var(--text-color) 10%) 100%);
            border-radius: 8px;
            border: 1px solid color-mix(in srgb, var(--background-color) 80%, var(--text-color) 20%);
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .chart-type-selector .stSelectbox label {
            font-weight: 600;
            color: var(--text-color);
        }
        </style>
        """, unsafe_allow_html=True)

        # Wrap in a container with the specific class
        with st.container():
            st.markdown('<div class="chart-type-selector">', unsafe_allow_html=True)
            chart_type = st.selectbox(
                "Choose Chart Type",
                ["Line", "Bar", "Scatter", "Box", "Heatmap"],
                key="chart_type_static"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Save Session State to help title tell what chart is being displayed
        st.session_state.chart_type = chart_type
    else:
        # For API connections, set a default or show selector elsewhere
        chart_type = "Line"
        st.session_state.chart_type = chart_type
        if st.button("🔄 Refresh Chart", use_container_width=True):
            # Refresh logic here
            pass
# === Load and Render Chart ===
try:
    # If "Both", load two files or one with two columns
    if direction == "Both":
        if variable == "Vehicle Volume":
            # KINETIC MOBILITY: Single file contains both directions
            df = pd.read_csv(selected_path)

            # Check if Time column exists, if not find it
            if "Time" not in df.columns:
                time_col = find_column(df, ["time", "timestamp", "date"])
                if not time_col:
                    raise ValueError("No time column found in the dataset")
            else:
                time_col = "Time"

            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
            df.dropna(subset=[time_col], inplace=True)
            df.set_index(time_col, inplace=True)

            # Find both direction columns - UPDATED LOGIC
            nb_col = find_column(df, ["northbound", "nb"])
            sb_col = find_column(df, ["southbound", "sb"])

            if nb_col and sb_col:
                df[nb_col] = pd.to_numeric(df[nb_col], errors='coerce')
                df[sb_col] = pd.to_numeric(df[sb_col], errors='coerce')

                # Rename for cleaner display
                df = df.rename(columns={nb_col: "Northbound", sb_col: "Southbound"})

                combined = df[["Northbound", "Southbound"]].copy()
                combined.dropna(inplace=True)
                combined.reset_index(inplace=True)

                # Use clean titles for charts (without the extra info)
                clean_title = base_title

                # Create charts based on chart type
                if chart_type == "Line":
                    fig = create_enhanced_multi_line_chart(combined, time_col, ["Northbound", "Southbound"],
                                                           clean_title)
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Bar":
                    fig = px.bar(combined, x=time_col, y=["Northbound", "Southbound"],
                                 title=clean_title, barmode='group')
                    fig.update_layout(yaxis_title="Vehicle Volume (vph)")
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Scatter":
                    fig = px.scatter(combined, x=time_col, y=["Northbound", "Southbound"],
                                     title=clean_title)
                    fig.update_layout(yaxis_title="Vehicle Volume (vph)")
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Box":
                    # Melt the dataframe for box plot
                    melted = combined.melt(id_vars=[time_col], value_vars=["Northbound", "Southbound"],
                                           var_name="Direction", value_name="Volume")
                    fig = px.box(melted, x="Direction", y="Volume",
                                 title=f"{clean_title} - Distribution Analysis")
                    fig.update_layout(yaxis_title="Vehicle Volume (vph)")
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Heatmap":
                    # Create side-by-side heatmaps
                    st.subheader("📊 Hourly Traffic Pattern Analysis")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**🔵 Northbound Traffic**")
                        df_nb = combined[[time_col, "Northbound"]].copy()
                        df_nb['hour'] = df_nb[time_col].dt.hour
                        df_nb['day'] = df_nb[time_col].dt.date
                        pivot_nb = df_nb.pivot_table(values="Northbound", index='day', columns='hour')
                        fig_nb = px.imshow(pivot_nb, aspect='auto', title="Northbound Pattern")
                        fig_nb.update_layout(coloraxis_colorbar_title="Volume (vph)")
                        st.plotly_chart(fig_nb, use_container_width=True)

                    with col2:
                        st.markdown("**🔴 Southbound Traffic**")
                        df_sb = combined[[time_col, "Southbound"]].copy()
                        df_sb['hour'] = df_sb[time_col].dt.hour
                        df_sb['day'] = df_sb[time_col].dt.date
                        pivot_sb = df_sb.pivot_table(values="Southbound", index='day', columns='hour')
                        fig_sb = px.imshow(pivot_sb, aspect='auto', title="Southbound Pattern")
                        fig_sb.update_layout(coloraxis_colorbar_title="Volume (vph)")
                        st.plotly_chart(fig_sb, use_container_width=True)

                        # Debug: Check the date range
                        try:
                            # Convert to datetime if not already
                            start_datetime = pd.to_datetime(combined.index.min())
                            end_datetime = pd.to_datetime(combined.index.max())
                            date_range = (end_datetime - start_datetime).days

                            st.write(f"Debug: Date range is {date_range} days")
                            st.write(f"Debug: Start date: {start_datetime}")
                            st.write(f"Debug: End date: {end_datetime}")
                            st.write(f"Debug: Index type: {type(combined.index[0])}")

                            # Check if date range is one day for cycle length recommendations
                            if date_range == 0:  # Single day selected
                                st.subheader("🚦 ADVANTEC Cycle Length Suggestions by Hour")


                                # Functions for cycle length calculations
                                def get_hourly_cycle_length(volume):
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


                                def get_existing_cycle_length(volume):
                                    if volume >= 300:
                                        return "140 sec"
                                    else:
                                        return "Free mode"


                                if direction == "Both":
                                    # Show combined table for both directions
                                    if "Northbound" in combined.columns and "Southbound" in combined.columns:
                                        hourly_df = combined.copy()
                                        hourly_df["Hour"] = pd.to_datetime(hourly_df.index).strftime("%H:%M")

                                        # Create the combined table
                                        table_df = pd.DataFrame({
                                            "Hour": hourly_df["Hour"],
                                            "NB Volume": hourly_df["Northbound"],
                                            "NB Existing": hourly_df["Northbound"].apply(get_existing_cycle_length),
                                            "NB Rec": hourly_df["Northbound"].apply(get_hourly_cycle_length),
                                            "SB Volume": hourly_df["Southbound"],
                                            "SB Existing": hourly_df["Southbound"].apply(get_existing_cycle_length),
                                            "SB Rec": hourly_df["Southbound"].apply(get_hourly_cycle_length)
                                        }).reset_index(drop=True)

                                        st.dataframe(
                                            table_df,
                                            hide_index=True,
                                            use_container_width=True,
                                            height=min(400, 50 * len(table_df))
                                        )
                                    else:
                                        st.info("No data available for both directions.")
                                else:
                                    # Show single direction table
                                    vol_col = "Northbound" if direction == "NB" else "Southbound"
                                    if vol_col and vol_col in combined.columns:
                                        hourly_df = combined.copy()
                                        hourly_df["Hour"] = pd.to_datetime(hourly_df.index).strftime("%H:%M")

                                        # Create the single direction table with renamed columns
                                        table_df = pd.DataFrame({
                                            "Hour": hourly_df["Hour"],
                                            "Vehicle Volume": hourly_df[vol_col],
                                            "Existing Cycle Length": hourly_df[vol_col].apply(
                                                get_existing_cycle_length),
                                            "Recommended Cycle Length": hourly_df[vol_col].apply(
                                                get_hourly_cycle_length)
                                        }).reset_index(drop=True)

                                        st.dataframe(
                                            table_df,
                                            hide_index=True,
                                            use_container_width=True,
                                            height=min(300, 50 * len(table_df))
                                        )
                                    else:
                                        st.info("No data available for the selected direction and period.")
                            else:
                                st.info(
                                    f"Cycle length recommendations only available for single day data. Current range: {date_range} days")

                        except Exception as e:
                            st.error(f"Error processing date range: {str(e)}")
                            st.write(f"Debug: Combined index sample: {combined.index[:5]}")

                # Show combined stats
                st.subheader("📈 Traffic Volume Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("**🔵 Northbound**", "", "")
                    st.write(f"Average: **{combined['Northbound'].mean():.0f} vph**")
                    st.write(f"Peak: **{combined['Northbound'].max():.0f} vph**")
                    st.write(f"Low: **{combined['Northbound'].min():.0f} vph**")
                with col2:
                    st.metric("**🔴 Southbound**", "", "")
                    st.write(f"Average: **{combined['Southbound'].mean():.0f} vph**")
                    st.write(f"Peak: **{combined['Southbound'].max():.0f} vph**")
                    st.write(f"Low: **{combined['Southbound'].min():.0f} vph**")
                with col3:
                    st.metric("**📊 Combined**", "", "")
                    total_avg = (combined['Northbound'].mean() + combined['Southbound'].mean())
                    total_peak = (combined['Northbound'].max() + combined['Southbound'].max())
                    st.write(f"Total Average: **{total_avg:.0f} vph**")
                    st.write(f"Total Peak: **{total_peak:.0f} vph**")
                    st.write(f"Daily Total: **{combined[['Northbound', 'Southbound']].sum().sum():.0f} vehicles**")
            else:
                st.error("Could not find both direction columns in volume data")
                st.write("Available columns:", list(df.columns))

        else:
            # FLIR ACYCLICA: Load both NB and SB files separately
            path_nb = path_map.get((variable, "NB", date_range))
            path_sb = path_map.get((variable, "SB", date_range))

            if not path_nb or not path_sb:
                raise FileNotFoundError("One or both directional files not found.")

            df_nb = pd.read_csv(path_nb)
            df_sb = pd.read_csv(path_sb)

            time_col = "Time"
            df_nb[time_col] = pd.to_datetime(df_nb[time_col], errors="coerce")
            df_sb[time_col] = pd.to_datetime(df_sb[time_col], errors="coerce")

            df_nb.dropna(subset=[time_col], inplace=True)
            df_sb.dropna(subset=[time_col], inplace=True)

            df_nb.set_index(time_col, inplace=True)
            df_sb.set_index(time_col, inplace=True)

            # Use "Strength" column for Speed and Travel Time (instead of "Firsts")
            y_col = "Strength"
            df_nb[y_col] = pd.to_numeric(df_nb[y_col], errors='coerce')
            df_sb[y_col] = pd.to_numeric(df_sb[y_col], errors='coerce')

            df_nb = df_nb.rename(columns={y_col: "Northbound"})
            df_sb = df_sb.rename(columns={y_col: "Southbound"})

            combined = pd.concat([df_nb["Northbound"], df_sb["Southbound"]], axis=1)
            combined.dropna(inplace=True)
            combined.reset_index(inplace=True)

            # Use clean titles for charts
            clean_title = base_title

            # Create charts based on chart type
            if chart_type == "Line":
                fig = create_enhanced_multi_line_chart(combined, time_col, ["Northbound", "Southbound"], clean_title)
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Bar":
                fig = px.bar(combined, x=time_col, y=["Northbound", "Southbound"],
                             title=clean_title, barmode='group')
                unit = "mph" if variable == "Speed" else "min"
                fig.update_layout(yaxis_title=f"{variable} ({unit})")
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Scatter":
                fig = px.scatter(combined, x=time_col, y=["Northbound", "Southbound"],
                                 title=clean_title)
                unit = "mph" if variable == "Speed" else "min"
                fig.update_layout(yaxis_title=f"{variable} ({unit})")
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Box":
                # Melt the dataframe for box plot
                melted = combined.melt(id_vars=[time_col], value_vars=["Northbound", "Southbound"],
                                       var_name="Direction", value_name="Value")
                fig = px.box(melted, x="Direction", y="Value",
                             title=f"{clean_title} - Distribution Analysis")
                unit = "mph" if variable == "Speed" else "min"
                fig.update_layout(yaxis_title=f"{variable} ({unit})")
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Heatmap":
                # Create side-by-side heatmaps
                st.subheader(f"📊 {variable} Pattern Analysis")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**🔵 Northbound**")
                    df_nb_heat = combined[[time_col, "Northbound"]].copy()
                    df_nb_heat['hour'] = df_nb_heat[time_col].dt.hour
                    df_nb_heat['day'] = df_nb_heat[time_col].dt.date
                    pivot_nb = df_nb_heat.pivot_table(values="Northbound", index='day', columns='hour')
                    fig_nb = px.imshow(pivot_nb, aspect='auto', title="Northbound Pattern")
                    unit = "mph" if variable == "Speed" else "min"
                    fig_nb.update_layout(coloraxis_colorbar_title=f"{variable} ({unit})")
                    st.plotly_chart(fig_nb, use_container_width=True)

                with col2:
                    st.markdown("**🔴 Southbound**")
                    df_sb_heat = combined[[time_col, "Southbound"]].copy()
                    df_sb_heat['hour'] = df_sb_heat[time_col].dt.hour
                    df_sb_heat['day'] = df_sb_heat[time_col].dt.date
                    pivot_sb = df_sb_heat.pivot_table(values="Southbound", index='day', columns='hour')
                    fig_sb = px.imshow(pivot_sb, aspect='auto', title="Southbound Pattern")
                    unit = "mph" if variable == "Speed" else "min"
                    fig_sb.update_layout(coloraxis_colorbar_title=f"{variable} ({unit})")
                    st.plotly_chart(fig_sb, use_container_width=True)

            # Show combined stats with proper units
            st.subheader(f"📈 {variable} Summary")
            col1, col2, col3 = st.columns(3)

            # Determine units based on variable
            if variable == "Speed":
                unit = "mph"
            elif variable == "Travel Time":
                unit = "min"
            else:
                unit = ""

            with col1:
                st.metric("**🔵 Northbound**", "", "")
                st.write(f"Average: **{combined['Northbound'].mean():.1f} {unit}**")
                st.write(f"Best: **{combined['Northbound'].max():.1f} {unit}**")
                st.write(f"Worst: **{combined['Northbound'].min():.1f} {unit}**")
            with col2:
                st.metric("**🔴 Southbound**", "", "")
                st.write(f"Average: **{combined['Southbound'].mean():.1f} {unit}**")
                st.write(f"Best: **{combined['Southbound'].max():.1f} {unit}**")
                st.write(f"Worst: **{combined['Southbound'].min():.1f} {unit}**")
            with col3:
                st.metric("**📊 Overall**", "", "")
                overall_avg = (combined['Northbound'].mean() + combined['Southbound'].mean()) / 2
                st.write(f"Combined Average: **{overall_avg:.1f} {unit}**")
                if variable == "Speed":
                    st.write(
                        f"Fastest: **{max(combined['Northbound'].max(), combined['Southbound'].max()):.1f} {unit}**")
                    st.write(
                        f"Slowest: **{min(combined['Northbound'].min(), combined['Southbound'].min()):.1f} {unit}**")
                else:
                    st.write(
                        f"Shortest: **{min(combined['Northbound'].min(), combined['Southbound'].min()):.1f} {unit}**")
                    st.write(
                        f"Longest: **{max(combined['Northbound'].max(), combined['Southbound'].max()):.1f} {unit}**")

    else:
        # SINGLE DIRECTION LOGIC
        df = pd.read_csv(selected_path)

        # Check if Time column exists, if not find it
        if "Time" not in df.columns:
            time_col = find_column(df, ["time", "timestamp", "date"])
            if not time_col:
                raise ValueError("No time column found in the dataset")
        else:
            time_col = "Time"

        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
        df.dropna(subset=[time_col], inplace=True)
        df.set_index(time_col, inplace=True)

        # Clean title for single direction
        clean_title = base_title

        # Determine column and chart rendering based on data source
        if variable == "Vehicle Volume":
            # KINETIC MOBILITY: Find the appropriate column - UPDATED LOGIC
            if direction == "NB":
                y_col = find_column(df, ["northbound", "nb"])
            else:  # SB
                y_col = find_column(df, ["southbound", "sb"])

            if y_col:
                df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                df.dropna(subset=[y_col], inplace=True)
                df.reset_index(inplace=True)

                # Create charts based on chart type
                if chart_type == "Line":
                    fig = create_enhanced_line_chart(df, time_col, y_col, clean_title)
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Bar":
                    fig = px.bar(df, x=time_col, y=y_col, title=clean_title)
                    fig.update_layout(yaxis_title="Vehicle Volume (vph)")
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Scatter":
                    fig = px.scatter(df, x=time_col, y=y_col, title=clean_title)
                    fig.update_layout(yaxis_title="Vehicle Volume (vph)")
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Box":
                    fig = px.box(df, y=y_col, title=f"{clean_title} - Distribution Analysis")
                    fig.update_layout(yaxis_title="Vehicle Volume (vph)")
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Heatmap":
                    df_heat = df.copy()
                    df_heat['hour'] = df_heat[time_col].dt.hour
                    df_heat['day'] = df_heat[time_col].dt.date
                    pivot_table = df_heat.pivot_table(values=y_col, index='day', columns='hour')
                    fig = px.imshow(pivot_table, aspect='auto', title=f"{clean_title} - Hourly Pattern")
                    fig.update_layout(coloraxis_colorbar_title="Volume (vph)")
                    st.plotly_chart(fig, use_container_width=True)

                # Show single direction stats
                st.subheader("📈 Traffic Volume Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("**📊 Average Volume**", f"{df[y_col].mean():.0f} vph")
                with col2:
                    st.metric("**📈 Peak Volume**", f"{df[y_col].max():.0f} vph")
                with col3:
                    st.metric("**📉 Low Volume**", f"{df[y_col].min():.0f} vph")

                # Additional stats
                st.write(f"**Total Daily Vehicles:** {df[y_col].sum():.0f}")
                st.write(f"**Standard Deviation:** {df[y_col].std():.1f} vph")
            else:
                st.error(f"Could not find {direction} column in volume data")
                st.write("Available columns:", list(df.columns))
        else:
            # FLIR ACYCLICA: Use "Strength" column
            y_col = "Strength"
            df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
            df.dropna(subset=[y_col], inplace=True)
            df.reset_index(inplace=True)

            # Create charts based on chart type
            if chart_type == "Line":
                fig = create_enhanced_line_chart(df, time_col, y_col, clean_title)
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Bar":
                fig = px.bar(df, x=time_col, y=y_col, title=clean_title)
                unit = "mph" if variable == "Speed" else "min"
                fig.update_layout(yaxis_title=f"{variable} ({unit})")
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Scatter":
                fig = px.scatter(df, x=time_col, y=y_col, title=clean_title)
                unit = "mph" if variable == "Speed" else "min"
                fig.update_layout(yaxis_title=f"{variable} ({unit})")
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Box":
                fig = px.box(df, y=y_col, title=f"{clean_title} - Distribution Analysis")
                unit = "mph" if variable == "Speed" else "min"
                fig.update_layout(yaxis_title=f"{variable} ({unit})")
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Heatmap":
                df_heat = df.copy()
                df_heat['hour'] = df_heat[time_col].dt.hour
                df_heat['day'] = df_heat[time_col].dt.date
                pivot_table = df_heat.pivot_table(values=y_col, index='day', columns='hour')
                fig = px.imshow(pivot_table, aspect='auto', title=f"{clean_title} - Hourly Pattern")
                unit = "mph" if variable == "Speed" else "min"
                fig.update_layout(coloraxis_colorbar_title=f"{variable} ({unit})")
                st.plotly_chart(fig, use_container_width=True)

            # Show single direction stats with proper units
            st.subheader(f"📈 {variable} Summary")

            # Determine units based on variable
            if variable == "Speed":
                unit = "mph"
                best_label = "Fastest"
                worst_label = "Slowest"
            elif variable == "Travel Time":
                unit = "min"
                best_label = "Shortest"
                worst_label = "Longest"
            else:
                unit = ""
                best_label = "Best"
                worst_label = "Worst"

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"**📊 Average {variable}**", f"{df[y_col].mean():.1f} {unit}")
            with col2:
                st.metric(f"**📈 {best_label}**", f"{df[y_col].max():.1f} {unit}")
            with col3:
                st.metric(f"**📉 {worst_label}**", f"{df[y_col].min():.1f} {unit}")

            # Additional stats
            st.write(f"**Standard Deviation:** {df[y_col].std():.2f} {unit}")
            st.write(f"**Median:** {df[y_col].median():.1f} {unit}")

except Exception as e:
    st.error(f"❌ Failed to load chart: {e}")
    st.write("Debug info - Available columns:", list(df.columns) if 'df' in locals() else "DataFrame not loaded")

# === KPI PANELS SECTION ===
# Add this after DataFrame load and before chart creation

# Helper function to robustly find columns
def find_column(df, patterns):
    """Find column that matches any of the patterns (case-insensitive)"""
    for pattern in patterns:
        for col in df.columns:
            if pattern.lower() in col.lower():
                return col
    return None

# Helper function to get cycle length recommendation
def get_cycle_length_recommendation(hourly_volumes):
    """
    Return recommended cycle length based on the highest volume hour in the period.
    Volume thresholds are: 305, 605, 1505, 2405 (all +5 from your original table).
    """
    cycle = "Free mode"
    for v in hourly_volumes:
        if v >= 2400:
            return "140 sec"
        elif v >= 1500:
            cycle = "130 sec"
        elif v >= 600:
            if cycle not in ["130 sec", "140 sec"]:
                cycle = "120 sec"
        elif v >= 300:
            if cycle not in ["120 sec", "130 sec", "140 sec"]:
                cycle = "110 sec"
    return cycle


# Helper function to filter data by time period, Recommended Cycle Length Activation Period (RCLAP)
def filter_by_period(df, time_col, period):
    """Filter dataframe by time period"""
    df_copy = df.copy()
    df_copy['hour'] = df_copy[time_col].dt.hour
    
    if period == "AM":
        return df_copy[(df_copy['hour'] >= 5) & (df_copy['hour'] <= 10)]  # 5:00 - 10:00
    elif period == "MD":
        return df_copy[(df_copy['hour'] >= 11) & (df_copy['hour'] <= 15)]  # 11:00 - 15:00
    elif period == "PM":
        return df_copy[(df_copy['hour'] >= 16) & (df_copy['hour'] <= 20)]  # 16:00 - 20:00
    return df_copy



# Only show KPI panels for Vehicle Volume data
if variable == "Vehicle Volume":
    st.markdown("---")
    st.subheader("📈 Key Performance Indicators")

    # Create 4 columns for KPI panels
    col1, col2, col3, col4 = st.columns(4)

    # Period_key is needed for processing - it extracts "AM, MD, or PM" from full string like "AM (5:00-10:00) and this line belongs in main logic flow - not side bar setup
    period_key = time_period.split(" ")[0]  # Extract AM/MD/PM

    # Prepare data for KPIs - use the original CSV data, not the renamed one
    if direction == "Both":
        # For "Both" direction, reload the original data to avoid column renaming issues
        kpi_df = pd.read_csv(selected_path)
        time_col = "Time"
    else:
        # For single direction, use the existing df
        kpi_df = df.copy()
        time_col = "Time"

    # Ensure 'Time' is datetime
    if time_col in kpi_df.columns:
        if not np.issubdtype(kpi_df[time_col].dtype, np.datetime64):
            kpi_df[time_col] = pd.to_datetime(kpi_df[time_col], errors='coerce')
    else:
        st.error("Time column not found in the dataset")
        st.stop()

    # --- Robust column finding for your specific format ---
    nb_vol_col = None
    sb_vol_col = None
    for col in kpi_df.columns:
        if "northbound" in col.lower():
            nb_vol_col = col
        if "southbound" in col.lower():
            sb_vol_col = col

    # Try to find speed columns if they exist (optional)
    nb_speed_col = None
    sb_speed_col = None
    for col in kpi_df.columns:
        if "speed" in col.lower() and "northbound" in col.lower():
            nb_speed_col = col
        if "speed" in col.lower() and "southbound" in col.lower():
            sb_speed_col = col

    if nb_vol_col and sb_vol_col:
        # Convert to numeric
        kpi_df[nb_vol_col] = pd.to_numeric(kpi_df[nb_vol_col], errors='coerce')
        kpi_df[sb_vol_col] = pd.to_numeric(kpi_df[sb_vol_col], errors='coerce')
        if nb_speed_col: kpi_df[nb_speed_col] = pd.to_numeric(kpi_df[nb_speed_col], errors='coerce')
        if sb_speed_col: kpi_df[sb_speed_col] = pd.to_numeric(kpi_df[sb_speed_col], errors='coerce')

        # Filter by selected time period
        period_df = filter_by_period(kpi_df, time_col, period_key)

        # === KPI 1: Peak Volume - Highest Direction ===
        with col1:
            st.markdown("### 🚦 Vehicle Volume Summary")

            if not period_df.empty:
                # Calculate total volume for each direction
                nb_total = period_df[nb_vol_col].sum()
                sb_total = period_df[sb_vol_col].sum()

                # Determine highest direction
                if nb_total >= sb_total:
                    peak_direction = "NB"
                    peak_volume = nb_total
                    peak_vol_col = nb_vol_col
                else:
                    peak_direction = "SB"
                    peak_volume = sb_total
                    peak_vol_col = sb_vol_col

                # Get the total sum of the selected column for "Total (direction) Vehicle Volume"
                if peak_vol_col == sb_vol_col:
                    total_peak_direction_volume = kpi_df[sb_vol_col].sum()  # Full day SB total
                else:
                    total_peak_direction_volume = kpi_df[nb_vol_col].sum()  # Full day NB total

                # Find consecutive hours with volume >= 300
                consecutive_hours = []
                current_sequence = []

                for _, row in period_df.iterrows():
                    if row[peak_vol_col] >= 300:
                        current_sequence.append(row[time_col])
                    else:
                        if len(current_sequence) > len(consecutive_hours):
                            consecutive_hours = current_sequence.copy()
                        current_sequence = []
                if len(current_sequence) > len(consecutive_hours):
                    consecutive_hours = current_sequence.copy()

                if consecutive_hours:
                    start_time = consecutive_hours[0].strftime("%H:%M")
                    end_time = consecutive_hours[-1].strftime("%H:%M")
                    hours_str = f"{start_time} - {end_time}"

                    # Calculate volume for "Recommended Cycle Length Activation Period (24 Hour)"
                    consecutive_df = period_df[period_df[time_col].isin(consecutive_hours)]
                    consecutive_volume = consecutive_df[peak_vol_col].sum()

                    # Get the hourly volumes for each hour in the consecutive period
                    hourly_volumes = consecutive_df[peak_vol_col].tolist()
                    cycle_rec = get_cycle_length_recommendation(hourly_volumes)  # Pass the list!

                    st.metric("Busiest Direction (NB or SB)", peak_direction)
                    st.metric("Cycle Length Activation Period (24-Hour)", hours_str)
                    st.metric("Total Activation Period Vehicle Volume", f"{consecutive_volume:,.0f} Vehicles")
                    st.metric("Total (direction) Vehicle Volume", f"{total_peak_direction_volume:,.0f} Vehicles")
                else:
                    st.metric("Busiest Direction (NB or SB)", peak_direction)
                    st.metric("Cycle Length Activation Period (24-Hour)", "Free mode")
                    st.metric("Total Activation Period Vehicle Volume", "Free mode")
                    st.metric("Total (direction) Vehicle Volume", f"{total_peak_direction_volume:,.0f} Vehicles")

            else:
                st.write("No data for selected period")

        # === KPI 2-4: Dynamic KPIs ===
        kpi_options = ["Average Speed", "Total Volume", "Peak Congestion Time"]
        if nb_speed_col and sb_speed_col:
            kpi_options = ["Average Speed", "Peak Speed", "Total Volume", "Peak Congestion Time"]

        for i, col in enumerate([col2, col3, col4]):
            with col:
                kpi_type = st.selectbox(f"KPI {i + 2}:", kpi_options, key=f"kpi_{i + 2}")

                # For Suggested Cycle Length Table, use sidebar direction; otherwise use local direction choice
                if kpi_type == "Suggested Cycle Length Table - Hourly":
                    direction_choice = direction  # Use sidebar direction
                    st.markdown(f"### 📈 {kpi_type} - {direction_choice}")
                else:
                    direction_choice = st.radio("Direction:", ["NB", "SB"], key=f"dir_{i + 2}")
                    st.markdown(f"### 📈 {kpi_type} - {direction_choice}")

                if not period_df.empty:
                    # KPIs for Speed (if available)
                    if kpi_type == "Average Speed" and nb_speed_col and sb_speed_col:
                        speed_col = nb_speed_col if direction_choice == "NB" else sb_speed_col
                        avg_speed = period_df[speed_col].mean()
                        st.metric("Average Speed", f"{avg_speed:.1f} mph")
                    elif kpi_type == "Peak Speed" and nb_speed_col and sb_speed_col:
                        speed_col = nb_speed_col if direction_choice == "NB" else sb_speed_col
                        peak_speed = period_df[speed_col].max()
                        peak_time = period_df.loc[period_df[speed_col].idxmax(), time_col].strftime("%H:%M")
                        st.metric("Peak Speed", f"{peak_speed:.1f} mph")
                        st.caption(f"at {peak_time}")
                    elif kpi_type == "Total Volume":
                        vol_col = nb_vol_col if direction_choice == "NB" else sb_vol_col
                        total_volume = period_df[vol_col].sum()
                        st.metric("Total Volume", f"{total_volume:,.0f} vph")
                    elif kpi_type == "Peak Congestion Time" and nb_speed_col and sb_speed_col:
                        speed_col = nb_speed_col if direction_choice == "NB" else sb_speed_col
                        min_speed = period_df[speed_col].min()
                        peak_cong_time = period_df.loc[period_df[speed_col].idxmin(), time_col].strftime("%H:%M")
                        st.metric("Congestion (Min Speed)", f"{min_speed:.1f} mph")
                        st.caption(f"at {peak_cong_time}")

                    else:
                        st.write("KPI not available for this direction or period.")
                else:
                    st.write("No data for selected period")
    else:
        st.warning("Could not find NB/SB columns in this dataset.")
