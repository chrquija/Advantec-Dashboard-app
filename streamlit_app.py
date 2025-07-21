import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np



#Chart_components + helpers IMPORTS
from helpers.reporting import get_hourly_cycle_length, get_existing_cycle_length, filter_by_period
from chart_components.title_section import find_column, get_base_title
from helpers.reporting import create_pdf_report, generate_email_details #for pdf function
from chart_components.charts import create_enhanced_line_chart, create_enhanced_multi_line_chart


st.set_page_config(
    page_title="Transportation Dashboard",
    page_icon="📊",
    layout="wide"
)


def find_time_column(df):
    """Find time column with better pattern matching"""
    time_patterns = [
        'time', 'timestamp', 'datetime', 'date', 'hour', 'period',
        'time_period', 'time_hour', 'hour_period', 'interval'
    ]

    # First try exact matches
    for pattern in time_patterns:
        for col in df.columns:
            if pattern.lower() == col.lower():
                return col

    # Then try partial matches
    for pattern in time_patterns:
        for col in df.columns:
            if pattern.lower() in col.lower():
                return col

    # If no time column found, return the first column that looks like time
    for col in df.columns:
        if any(word in col.lower() for word in ['time', 'hour', 'date', 'period']):
            return col

    return None

# Initialize chart_type with default value
chart_type = "Line"


def send_email_with_pdf(pdf_buffer, variable, date_range):
    """Download PDF and open email client"""
    # Create download link for PDF
    pdf_data = pdf_buffer.getvalue()

    # Get email details from reporting module
    to_emails, subject, body, mailto_url = generate_email_details(variable, date_range)

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
        # == End of Data Source Code==

# ==IMPORTING chart title code inot Streamlit_app.py==
from chart_components.title_section import render_chart_title_section

# Render chart title section
chart_type = render_chart_title_section(variable, date_range, direction, data_source)

# === Load and Render Chart ===
try:
    # If "Both", load two files or one with two columns
    if direction == "Both":
        if variable == "Vehicle Volume":
            # KINETIC MOBILITY: Single file contains both directions
            df = pd.read_csv(selected_path)

            # Check if Time column exists, if not find it
            time_col = find_time_column(df)
            if not time_col:
                st.error("No time column found. Please ensure your data has a time-related column.")
                st.stop()

            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
            df.dropna(subset=[time_col], inplace=True)
            df.set_index(time_col, inplace=True)

            # Find both direction columns - UPDATED LOGIC
            nb_col = find_column(df, ["northbound", "nb"])
            sb_col = find_column(df, ["southbound", "sb"])

            if nb_col and sb_col:
                df[nb_col] = pd.to_numeric(df[nb_col], errors='coerce')
                df[sb_col] = pd.to_numeric(df[sb_col], errors='coerce')

                # Extract date from column names if present and create Date column if it doesn't exist
                if 'Date' not in df.columns:
                    # Try to extract date from column names (format: "MM/DD/YYYY Direction")
                    date_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'
                    dates_in_cols = []
                    for col in df.columns:
                        import re
                        match = re.search(date_pattern, col)
                        if match:
                            dates_in_cols.append(match.group(1))

                    if dates_in_cols:
                        # Use the first date found in column names
                        df['Date'] = dates_in_cols[0]
                    else:
                        # If no date in column names, use current date as fallback
                        from datetime import datetime
                        df['Date'] = datetime.now().strftime('%m/%d/%Y')

                # Rename for cleaner display
                df = df.rename(columns={nb_col: "Northbound", sb_col: "Southbound"})

                combined = df[["Northbound", "Southbound"]].copy()
                combined.dropna(inplace=True)
                combined.reset_index(inplace=True)

                # Use clean titles for charts (without the extra info)
                clean_title = get_base_title(variable, direction)

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
            clean_title = get_base_title(variable, direction)

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
        clean_title = get_base_title(variable, direction)

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


except Exception as e:
    st.error(f"❌ Failed to load chart: {e}")
    st.write("Debug info - Available columns:", list(df.columns) if 'df' in locals() else "DataFrame not loaded")


# --- Robust find_column function ---
def find_column(df, search_terms):
    # Try exact matches (case-insensitive)
    for term in search_terms:
        for col in df.columns:
            if col.strip().lower() == term.strip().lower():
                return col
    # Then, try substring matches (case-insensitive)
    for term in search_terms:
        for col in df.columns:
            if term.strip().lower() in col.strip().lower():
                return col
    return None

# === TRAFFIC VOLUME SUMMARY WITH CYCLE LENGTH TOGGLE ===
show_cycle_length = st.toggle("🚦 Get Cycle Length Recommendations", value=False)

if show_cycle_length:
    st.markdown("### 🚦 Cycle Length Recommendations - Hourly Analysis")
    st.markdown(f"**Time Period:** {time_period} | **Direction:** {direction}")

    # --- 1. Find the time column flexibly ---
    time_col = None
    possible_time_cols = ['Time', 'time', 'hour', 'Hour', 'TIME', 'DateTime', 'datetime']

    # Direct match first
    for col_name in possible_time_cols:
        if col_name in df.columns:
            time_col = col_name
            break
    # Try fuzzy search if not found
    if not time_col:
        time_col = find_column(df, ['time', 'hour', 'datetime'])
    # Last-ditch: any column containing time/hour/date in name and is datetime-convertible
    if not time_col:
        for col in df.columns:
            if 'time' in col.lower() or 'hour' in col.lower() or 'date' in col.lower():
                try:
                    pd.to_datetime(df[col].iloc[0])
                    time_col = col
                    break
                except:
                    continue
    if not time_col:
        st.error("❌ No time column found. Please ensure your data has a time/hour column.")
        st.error(f"Available columns: {list(df.columns)}")
        st.stop()

    # --- 2. Find volume column(s) based on direction ---
    if direction == "NB":
        vol_col = find_column(df, ['northbound', 'NB', 'north'])
        if not vol_col:
            # Try fuzzy match: search for any column containing 'north'
            for col in df.columns:
                if 'north' in col.lower():
                    vol_col = col
                    break
        if not vol_col:
            st.error("❌ Cannot find Northbound volume column.")
            st.info(f"Columns: {list(df.columns)}")
            st.stop()
        st.info(f"Using Northbound column: {vol_col}")

    elif direction == "SB":
        vol_col = find_column(df, ['southbound', 'SB', 'south'])
        if not vol_col:
            for col in df.columns:
                if 'south' in col.lower():
                    vol_col = col
                    break
        if not vol_col:
            st.error("❌ Cannot find Southbound volume column.")
            st.info(f"Columns: {list(df.columns)}")
            st.stop()
        st.info(f"Using Southbound column: {vol_col}")

    elif direction == "Both":  # Only sum when "Both" is selected
        nb_col = find_column(df, ['northbound', 'NB', 'north'])
        sb_col = find_column(df, ['southbound', 'SB', 'south'])
        # Fuzzy for NB
        if not nb_col:
            for col in df.columns:
                if 'north' in col.lower():
                    nb_col = col
                    break
        # Fuzzy for SB
        if not sb_col:
            for col in df.columns:
                if 'south' in col.lower():
                    sb_col = col
                    break
        if not nb_col or not sb_col:
            st.error(f"❌ Cannot find required columns. Found NB: {nb_col}, SB: {sb_col}")
            st.info(f"Columns: {list(df.columns)}")
            st.stop()
        if 'Combined' not in df.columns:
            df['Combined'] = df[nb_col] + df[sb_col]
        vol_col = 'Combined'
        st.info(f"Using columns: NB={nb_col}, SB={sb_col} (summed as Combined)")
        st.info(f"Using columns: NB={nb_col}, SB={sb_col} (summed as Combined)")

        # ADD THIS NEW CODE HERE - RIGHT AFTER THE st.info LINE
        # Create and display table for "Both" direction
        if time_col:
            # Show table with NB, SB, and Combined columns
            table_df = df[[time_col, nb_col, sb_col, 'Combined']].copy()
            table_df.columns = ['Hour', 'NB', 'SB', 'Combined']

            # Format the table nicely
            st.subheader("📊 Volume Data Table")
            st.dataframe(
                table_df,
                use_container_width=True,
                hide_index=True
            )
        # END OF NEW CODE

    else:
        st.error("❌ Invalid direction selection.")
        st.stop()

    # --- 3. Make sure time is datetime ---
    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        try:
            df[time_col] = pd.to_datetime(df[time_col])
        except:
            st.error(f"❌ Cannot convert '{time_col}' to datetime format.")
            st.stop()

    # --- 4. Only single day allowed for recommendations ---
    if 'Date' in df.columns and len(df['Date'].unique()) > 1:
        st.warning(
            "⚠️ Cycle Length Recommendations are only available for single-day analysis. Please select a single date to view hourly cycle length recommendations.")
    else:
        # Filter data by period
        period_key = time_period.split()[0]
        filtered_df = filter_by_period(df, time_col, period_key)

        # Make sure vol_col is defined before using it in aggregation
        if vol_col is None:
            st.error("❌ Volume column not found. Cannot proceed with analysis.")
            st.stop()

        # Hourly aggregation using the correct vol_col
        try:
            hourly_df = filtered_df.groupby(filtered_df[time_col].dt.hour).agg({
                vol_col: 'sum'
            }).reset_index()
        except KeyError as e:
            st.error(f"❌ Column '{vol_col}' not found in data. Available columns: {list(filtered_df.columns)}")
            st.stop()
        except Exception as e:
            st.error(f"❌ Error during aggregation: {str(e)}")
            st.stop()

        # Build recommendations table
        table_df = []
        for _, row in hourly_df.iterrows():
            hour = int(row[time_col])
            volume = row[vol_col]

            cvag_recommendation = get_hourly_cycle_length(volume)
            current_system = get_existing_cycle_length(volume)
            hour_display = f"{hour:02d}:00"
            needs_change = cvag_recommendation != current_system

            if needs_change:
                if cvag_recommendation == "Free mode" and current_system == "140 sec":
                    status_html = '<span style="color: #FF6B6B; font-weight: bold;">⬇️ REDUCE</span>'
                    status_text = "⬇️ REDUCE"
                elif cvag_recommendation == "140 sec" and current_system == "Free mode":
                    status_html = '<span style="color: #4ECDC4; font-weight: bold;">⬆️ INCREASE</span>'
                    status_text = "⬆️ INCREASE"
                else:
                    status_html = '<span style="color: #FFE66D; font-weight: bold;">⚠️ ADJUST</span>'
                    status_text = "⚠️ ADJUST"
            else:
                status_html = '<span style="color: #51CF66; font-weight: bold;">✅ OPTIMAL</span>'
                status_text = "✅ OPTIMAL"

            table_df.append({
                "Hour": hour_display,
                "Volume": f"{volume:,.0f}",
                "Current System": current_system,
                "CVAG Recommendation": cvag_recommendation,
                "Status": status_html,
                "Status_Text": status_text
            })

        # Sort by hour
        table_df = sorted(table_df, key=lambda x: int(x["Hour"].split(":")[0]))

        # Show table with HTML styling
        df_display = pd.DataFrame([{k: v for k, v in row.items() if k != "Status_Text"} for row in table_df])
        st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

        # --- Table CSS ---
        st.markdown("""
            <style>
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
            </style>
            """, unsafe_allow_html=True)

        # --- Metrics summary section ---
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_hours = len(df_display)
            period_name = time_period.split()[0]
            st.metric(f"{period_name} Hours Analyzed", total_hours)
        with col2:
            changes_needed = len([x for x in table_df if "OPTIMAL" not in x["Status_Text"]])
            st.metric("Hours Needing Changes", changes_needed,
                      delta=f"{changes_needed}/{total_hours}" if total_hours > 0 else "0/0")
        with col3:
            if total_hours > 0:
                efficiency = ((total_hours - changes_needed) / total_hours) * 100
                st.metric("Current System Efficiency", f"{efficiency:.1f}%",
                          delta=f"{'Good' if efficiency >= 80 else 'Needs Improvement'}")
            else:
                st.metric("Current System Efficiency", "N/A")
        with col4:
            reduce_count = len([x for x in table_df if "REDUCE" in x["Status_Text"]])
            increase_count = len([x for x in table_df if "INCREASE" in x["Status_Text"]])
            adjust_count = len([x for x in table_df if "ADJUST" in x["Status_Text"]])
            if reduce_count > 0:
                st.metric("🔽 Hours to Reduce", reduce_count)
            elif increase_count > 0:
                st.metric("🔼 Hours to Increase", increase_count)
            elif adjust_count > 0:
                st.metric("🔄 Hours to Adjust", adjust_count)
            else:
                st.metric("✅ Optimal Hours", total_hours - changes_needed)

        # --- Status Legend ---
        st.markdown("---")
        st.markdown("**Status Legend:**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(
                '<span style="color: #51CF66; font-weight: bold;">✅ OPTIMAL</span> - No changes needed',
                unsafe_allow_html=True)
        with col2:
            st.markdown(
                '<span style="color: #FF6B6B; font-weight: bold;">⬇️ REDUCE</span> - Lower cycle length',
                unsafe_allow_html=True)
        with col3:
            st.markdown(
                '<span style="color: #4ECDC4; font-weight: bold;">⬆️ INCREASE</span> - Higher cycle length',
                unsafe_allow_html=True)
        with col4:
            st.markdown(
                '<span style="color: #FFE66D; font-weight: bold;">⚠️ ADJUST</span> - Fine-tune cycle length',
                unsafe_allow_html=True)

        # --- Analysis period info ---
        period_info = {
            "AM": "5:00 - 10:00 (6 hours)",
            "MD": "11:00 - 15:00 (5 hours)",
            "PM": "16:00 - 20:00 (5 hours)"
        }
        st.info(
            f"📅 **Analysis Period:** {period_info.get(period_key, 'Full Day')} | **Direction:** {direction}")



else:
    # === DYNAMIC TRAFFIC VOLUME SUMMARY ===
    st.subheader("📈 Traffic Volume Summary")

    # Import the helper function
    from chart_components.title_section import find_column

    # Find the correct volume columns using the existing helper function
    nb_vol_col = find_column(df, ['north', 'nb'])
    sb_vol_col = find_column(df, ['south', 'sb'])

    if nb_vol_col and sb_vol_col:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("**🔵 Northbound**", "", "")
            st.write(f"Average: **{df[nb_vol_col].mean():.0f} vph**")
            st.write(f"Peak: **{df[nb_vol_col].max():.0f} vph**")
            st.write(f"Low: **{df[nb_vol_col].min():.0f} vph**")
        with col2:
            st.metric("**🔴 Southbound**", "", "")
            st.write(f"Average: **{df[sb_vol_col].mean():.0f} vph**")
            st.write(f"Peak: **{df[sb_vol_col].max():.0f} vph**")
            st.write(f"Low: **{df[sb_vol_col].min():.0f} vph**")
        with col3:
            st.metric("**📊 Combined**", "", "")
            total_avg = (df[nb_vol_col].mean() + df[sb_vol_col].mean())
            total_peak = (df[nb_vol_col].max() + df[sb_vol_col].max())
            st.write(f"Total Average: **{total_avg:.0f} vph**")
            st.write(f"Total Peak: **{total_peak:.0f} vph**")
            st.write(f"Daily Total: **{df[[nb_vol_col, sb_vol_col]].sum().sum():.0f} vehicles**")
    else:
        st.warning("⚠️ Could not find Northbound and Southbound volume columns in the data.")
        st.info("Available columns: " + ", ".join(df.columns))

    # Add note about cycle recommendations
    if 'Date' in df.columns and len(df['Date'].unique()) == 1:
        st.info(
            "💡 **Tip:** Click 'Get Cycle Length Recommendations' above to see hourly cycle length analysis for this day.")


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
        kpi_options = ["Average Speed", "Total Volume", "Peak Congestion Time", "Suggested Cycle Length Table - Hourly"]
        if nb_speed_col and sb_speed_col:
            kpi_options = ["Average Speed", "Peak Speed", "Total Volume", "Peak Congestion Time",
                           "Suggested Cycle Length Table - Hourly"]

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
                    elif kpi_type == "Suggested Cycle Length Table - Hourly":
                        # Functions for cycle length calculations

                        if direction_choice == "Both":
                            # Show combined table for both directions
                            if nb_vol_col in period_df.columns and sb_vol_col in period_df.columns:
                                hourly_df = period_df.copy()
                                hourly_df["Hour"] = hourly_df[time_col].dt.strftime("%H:%M")

                                # Create the combined table
                                table_df = pd.DataFrame({
                                    "Hour": hourly_df["Hour"],
                                    "NB Volume": hourly_df[nb_vol_col],
                                    "NB Existing": hourly_df[nb_vol_col].apply(get_existing_cycle_length),
                                    "NB Rec": hourly_df[nb_vol_col].apply(get_hourly_cycle_length),
                                    "SB Volume": hourly_df[sb_vol_col],
                                    "SB Existing": hourly_df[sb_vol_col].apply(get_existing_cycle_length),
                                    "SB Rec": hourly_df[sb_vol_col].apply(get_hourly_cycle_length)
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
                            vol_col = nb_vol_col if direction_choice == "NB" else sb_vol_col
                            if vol_col and vol_col in period_df.columns:
                                hourly_df = period_df.copy()
                                hourly_df["Hour"] = hourly_df[time_col].dt.strftime("%H:%M")

                                # Create the single direction table with renamed columns
                                table_df = pd.DataFrame({
                                    "Hour": hourly_df["Hour"],
                                    "Vehicle Volume": hourly_df[vol_col],
                                    "Existing Cycle Length": hourly_df[vol_col].apply(get_existing_cycle_length),
                                    "Recommended Cycle Length": hourly_df[vol_col].apply(get_hourly_cycle_length)
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
                        st.write("KPI not available for this direction or period.")
                else:
                    st.write("No data for selected period")
    else:
        st.warning("Could not find NB/SB columns in this dataset.")
