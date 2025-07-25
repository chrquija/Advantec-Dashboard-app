import streamlit as st
import pandas as pd
import plotly.express as px
import io
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import numpy as np
import requests




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

@st.cache_data
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

    # SMART DATE RANGE SELECTION (GitHub only, API will have different logic)
    if data_source == "GitHub Repository":



        if variable == "Speed" or variable == "Travel Time":
            min_date = datetime(2024, 9, 1)
            max_date = datetime(2025, 6, 24)
            data_source_name = "Iteris ClearGuide"
            total_days = (max_date - min_date).days + 1
        elif variable == "Vehicle Volume":
            min_date = datetime(2024, 10, 30)
            max_date = datetime(2025, 6, 15)
            data_source_name = "Kinetic Mobility"
            total_days = (max_date - min_date).days + 1
        else:
            min_date = datetime(2024, 9, 1)
            max_date = datetime(2025, 6, 24)
            data_source_name = "Iteris ClearGuide"
            total_days = (max_date - min_date).days + 1

        # Show data availability info
        st.info(
            f"📊 **{data_source_name}** data available: {min_date.strftime('%b %d, %Y')} - {max_date.strftime('%b %d, %Y')} ({total_days:,} days)")

        # Smart date range selector with validation
        date_range = st.date_input(
            "📅 Select Date Range",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date(),
            format="MM/DD/YYYY",
            help=f"Select any date range within the available {data_source_name} data period",
            key="smart_date_range"
        )

        # Handle single date vs date range
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            days_selected = (end_date - start_date).days + 1

            # Show selection summary
            if days_selected == 1:
                st.success(f"✅ Selected: **{start_date.strftime('%b %d, %Y')}** (1 day)")
            else:
                st.success(
                    f"✅ Selected: **{start_date.strftime('%b %d, %Y')}** to **{end_date.strftime('%b %d, %Y')}** ({days_selected:,} days)")
        else:
            # Handle single date selection
            if isinstance(date_range, date):
                start_date = end_date = date_range
                st.success(f"✅ Selected: **{start_date.strftime('%b %d, %Y')}** (1 day)")

    # SMART GRANULARITY SELECTOR
    if data_source == "GitHub Repository":

        # Determine available granularities based on selected date range
        if isinstance(date_range, tuple) and len(date_range) == 2:
            days_span = (date_range[1] - date_range[0]).days + 1
        elif isinstance(date_range, date):
            days_span = 1
        else:
            days_span = 1

        # Smart granularity options based on date range
        if days_span == 1:
            # Single day - offer hourly options
            granularity_options = [
                "1 Hour",
                "2 Hours",
                "4 Hours",
                "6 Hours",
                "12 Hours",
                "1 Day"
            ]
            default_granularity = "1 Hour"
            help_text = "For single day: Hourly granularity recommended"

        elif days_span <= 7:
            # Week or less - offer hourly to daily
            granularity_options = [
                "1 Hour",
                "2 Hours",
                "4 Hours",
                "6 Hours",
                "12 Hours",
                "1 Day"
            ]
            default_granularity = "6 Hours"
            help_text = "For week or less: 6-hour intervals recommended"

        elif days_span <= 31:
            # Month or less - offer daily to weekly
            granularity_options = [
                "6 Hours",
                "12 Hours",
                "1 Day",
                "2 Days",
                "3 Days",
                "1 Week"
            ]
            default_granularity = "1 Day"
            help_text = "For month or less: Daily aggregation recommended"

        else:
            # More than a month - offer daily to monthly
            granularity_options = [
                "1 Day",
                "2 Days",
                "3 Days",
                "1 Week",
                "2 Weeks",
                "1 Month"
            ]
            default_granularity = "1 Week"
            help_text = "For long periods: Weekly aggregation recommended"

        # Granularity selector
        granularity = st.selectbox(
            "⏱️ Data Granularity",
            granularity_options,
            index=granularity_options.index(default_granularity) if default_granularity in granularity_options else 0,
            help=help_text,
            key="smart_granularity"
        )

        # Show granularity impact
        if granularity in ["1 Hour", "2 Hours", "4 Hours", "6 Hours", "12 Hours"]:
            hours = int(granularity.split()[0]) if granularity != "12 Hours" else 12
            total_points = (days_span * 24) // hours
            st.caption(f"📈 This will show ~{total_points:,} data points on your chart")
        elif granularity == "1 Day":
            st.caption(f"📈 This will show ~{days_span:,} data points on your chart")
        elif "Week" in granularity:
            weeks = int(granularity.split()[0]) if granularity != "1 Week" else 1
            total_points = days_span // (weeks * 7)
            st.caption(f"📈 This will show ~{total_points:,} data points on your chart")

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


# === UPDATED Filepath Mapping Logic ===
@st.cache_data
def get_washington_st_data_paths():
    """Return paths for Washington St Corridor full datasets"""
    base_url = "https://raw.githubusercontent.com/chrquija/Advantec-Dashboard-app/refs/heads/main/hwy111_to_ave52/"

    return {
        # === SPEED DATA (9/1/2024 - 6/24/2025) ===
        "speed_full_dataset": {
            "url": base_url + "SPEED/Iteris/september_to_june/NSB_WashingtonCorridor_Ave52_to_HWY111_1hr_SPEED_090124to062325.csv",
            "columns": {
                "datetime": "local_datetime",
                "nb_speed": "NB_avg_speed",
                "sb_speed": "SB_avg_speed"
            },
            "date_range": "2024-09-01 to 2025-06-24",
            "source": "Iteris ClearGuide",
            "units": "mph"
        },

        # === TRAVEL TIME DATA (9/1/2024 - 6/24/2025) ===
        "travel_time_full_dataset": {
            "url": base_url + "TRAVEL_TIME/Iteris/september_to_june/TrvltimeNSB_WashingtonCorr_Ave52_to_HWY111_1hr_901to0623.csv",
            "columns": {
                "datetime": "local_datetime",
                "nb_travel_time": "NB_avg_travel_time",
                "sb_travel_time": "SB_avg_travel_time"
            },
            "date_range": "2024-09-01 to 2025-06-24",
            "source": "Iteris ClearGuide",
            "units": "minutes"
        },

        # === VOLUME DATA (10/30/2024 - 6/15/2025) ===
        "volume_full_dataset": {
            "url": base_url + "VOLUME/KMOB/September2024_to_June2025/ALL_MELTED_Washington_Ave52TOAve47__1hr_SUM_NS_VOLUME_OctoberTOJune.csv",
            "columns": {
                "datetime": "local_datetime",
                "nb_volume": "NB_total_volume",
                "sb_volume": "SB_total_volume"
            },
            "date_range": "2024-10-30 to 2025-06-15",
            "source": "Kinetic Mobility",
            "units": "vehicles"
        }
    }

@st.cache_data
def load_washington_st_data(variable, direction):
    """Load the appropriate full dataset"""
    data_paths = get_washington_st_data_paths()

    # Map variable to dataset key
    dataset_map = {
        "Speed": "speed_full_dataset",
        "Travel Time": "travel_time_full_dataset",
        "Vehicle Volume": "volume_full_dataset"
    }

    dataset_key = dataset_map.get(variable)
    if not dataset_key:
        return None

    dataset_info = data_paths[dataset_key]

    try:
        # Load the full dataset
        df = pd.read_csv(dataset_info["url"])

        # Convert datetime column
        datetime_col = dataset_info["columns"]["datetime"]
        df[datetime_col] = pd.to_datetime(df[datetime_col])

        # Filter by direction if needed
        if direction == "NB":
            if variable == "Speed":
                df = df[[datetime_col, dataset_info["columns"]["nb_speed"]]].copy()
                df.columns = ['datetime', 'value']
            elif variable == "Travel Time":
                df = df[[datetime_col, dataset_info["columns"]["nb_travel_time"]]].copy()
                df.columns = ['datetime', 'value']
            elif variable == "Vehicle Volume":
                df = df[[datetime_col, dataset_info["columns"]["nb_volume"]]].copy()
                df.columns = ['datetime', 'value']

        elif direction == "SB":
            if variable == "Speed":
                df = df[[datetime_col, dataset_info["columns"]["sb_speed"]]].copy()
                df.columns = ['datetime', 'value']
            elif variable == "Travel Time":
                df = df[[datetime_col, dataset_info["columns"]["sb_travel_time"]]].copy()
                df.columns = ['datetime', 'value']
            elif variable == "Vehicle Volume":
                df = df[[datetime_col, dataset_info["columns"]["sb_volume"]]].copy()
                df.columns = ['datetime', 'value']

        elif direction == "Both":
            # Keep both directions
            if variable == "Speed":
                df = df[[datetime_col, dataset_info["columns"]["nb_speed"], dataset_info["columns"]["sb_speed"]]].copy()
                df.columns = ['datetime', 'NB_value', 'SB_value']
            elif variable == "Travel Time":
                df = df[[datetime_col, dataset_info["columns"]["nb_travel_time"],
                         dataset_info["columns"]["sb_travel_time"]]].copy()
                df.columns = ['datetime', 'NB_value', 'SB_value']
            elif variable == "Vehicle Volume":
                df = df[
                    [datetime_col, dataset_info["columns"]["nb_volume"], dataset_info["columns"]["sb_volume"]]].copy()
                df.columns = ['datetime', 'NB_value', 'SB_value']

        return df, dataset_info

    except Exception:
        return None, None

# === EXTENSIBLE DATA LOADING SYSTEM (helps the sidebar do its job) ===

class DataLoader:
    """Centralized data loading system supporting multiple sources"""

# Pure cached function (outside class)
@st.cache_data
def load_github_data_cached(url):
    """Cached GitHub data loading"""
    try:
        if url == "BOTH":
            return None
        return pd.read_csv(url)
    except Exception:
        return None

# Class with clean static method
class DataLoader:
    @staticmethod
    def load_github_data(url):
        """Load data from GitHub repository"""
        return load_github_data_cached(url)

@st.cache_data
def process_uploaded_data(file_content, date_col, direction_col, variable_col, data_format="Long format",
                          nb_col=None, sb_col=None):
    """Process uploaded CSV data - NO UI elements"""
    try:
        # Create DataFrame from file content
        df = pd.read_csv(io.StringIO(file_content))

        # Check if dataframe is empty
        if df.empty:
            return None, "empty_data"

        # Check if required columns exist
        if data_format == "Wide format (NB/SB columns)":
            if nb_col is None or sb_col is None:
                return None, "missing_nb_sb_cols"

            missing_cols = []
            for col in [date_col, nb_col, sb_col]:
                if col not in df.columns:
                    missing_cols.append(col)

            if missing_cols:
                return None, f"missing_columns:{','.join(missing_cols)}"

            # Keep only the required columns
            df = df[[date_col, nb_col, sb_col]]
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
                return None, f"missing_columns:{','.join(missing_cols)}"

            df = df.rename(columns={
                date_col: 'Date',
                direction_col: 'Direction',
                variable_col: 'Value'
            })

        # Convert date column to datetime
        try:
            df['Date'] = pd.to_datetime(df['Date'])
        except Exception:
            return None, "date_conversion_error"

        return df, "success"

    except pd.errors.EmptyDataError:
        return None, "empty_file"
    except pd.errors.ParserError:
        return None, "parser_error"
    except Exception:
        return None, "general_error"

def load_uploaded_data_with_ui(file_obj, date_col, direction_col, variable_col, data_format="Long format",
                               nb_col=None, sb_col=None):
    """Load uploaded data with UI feedback"""

    # Reset file pointer and read content
    file_obj.seek(0)
    file_content = file_obj.read().decode('utf-8')

    # Process data (this part is cached!)
    df, status = process_uploaded_data(file_content, date_col, direction_col, variable_col, data_format, nb_col,
                                       sb_col)

    # Handle UI based on status
    if status == "success":
        # ✅ SUCCESS - Show preview
        st.success("✅ File uploaded successfully!")
        st.write("**First few rows of uploaded data:**")
        st.dataframe(df.head())
        return df

    elif status == "empty_data":
        st.error("The uploaded file contains no data rows")
        return None

    elif status == "missing_nb_sb_cols":
        st.error("NB and SB columns must be specified for wide format")
        return None

    elif status.startswith("missing_columns:"):
        missing_cols = status.split(":")[1].split(",")
        st.error(f"Missing columns in uploaded file: {missing_cols}")
        # Show available columns by re-reading file
        file_obj.seek(0)
        temp_df = pd.read_csv(file_obj)
        st.write(f"Available columns: {list(temp_df.columns)}")
        return None

    elif status == "date_conversion_error":
        st.error("Error converting date column to datetime format")
        st.info("💡 Make sure your date column contains valid dates (e.g., 2023-01-01, 01/01/2023)")
        return None

    elif status == "empty_file":
        st.error("The uploaded file is empty or contains no data")
        return None

    elif status == "parser_error":
        st.error("Error parsing CSV file - please check file format")
        st.info("💡 Make sure your file is a valid CSV with proper formatting")
        return None

    else:  # general_error
        st.error("Error processing uploaded file - please try again")
        st.info("💡 Try refreshing the page or check your file format")
        return None

    # == END OF PROCESS UPLOAD DATA LOGIC AND UI CODE ==

    @st.cache_data
    def load_api_data_cached(api_config):
        """Cached data loading"""
        try:
            if api_config.get('type') == 'REST API':
                data = DataLoader._load_rest_api(api_config)
                return data, "success"
            elif api_config.get('type') == 'Database API':
                data = DataLoader._load_database_api(api_config)
                return data, "success"
            else:
                return None, "unsupported_api_type"
        except Exception as e:
            return None, f"error: {str(e)}"

    def load_api_data_with_ui(api_config):
        """UI function with error handling"""
        data, status = load_api_data_cached(api_config)

        if status == "success":
            st.success("✅ API data loaded successfully!")
            return data
        elif status == "unsupported_api_type":
            st.error("❌ Unsupported API type")
            return None
        else:
            st.error(f"❌ Error loading API data: {status.replace('error: ', '')}")
            return None

    class DataLoader:
        @staticmethod
        def load_api_data(api_config):
            """Clean static method"""
            return load_api_data_with_ui(api_config)

    # Pure cached function - NO UI messages
    @st.cache_data
    def _load_rest_api_cached(config):
        """Load data from REST API - cached version"""
        try:
            headers = {}
            if config.get('auth_method') == 'API Key':
                headers[config.get('key_header')] = config.get('api_key')
            elif config.get('auth_method') == 'Bearer Token':
                headers['Authorization'] = f"Bearer {config.get('bearer_token')}"

            response = requests.get(config.get('url'), headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            if 'data' in data:
                return pd.DataFrame(data['data']), "success"
            else:
                return pd.DataFrame(data if isinstance(data, list) else [data]), "success"

        except requests.exceptions.RequestException as e:
            return None, f"request_error: {str(e)}"
        except ValueError as e:
            return None, f"json_error: {str(e)}"
        except Exception as e:
            return None, f"unknown_error: {str(e)}"

    # UI function handles messages
    def load_rest_api_with_ui(config):
        """Load REST API data with UI feedback"""
        data, status = _load_rest_api_cached(config)

        if status == "success":
            st.success("✅ API data loaded successfully!")
            return data
        elif status.startswith("request_error"):
            st.error(f"❌ API Request failed: {status.replace('request_error: ', '')}")
            return None
        elif status.startswith("json_error"):
            st.error(f"❌ Invalid JSON response: {status.replace('json_error: ', '')}")
            return None
        else:
            st.error(f"❌ Unexpected error: {status.replace('unknown_error: ', '')}")
            return None

    # Pure cached function (outside class)
    @st.cache_data
    def _load_database_api_cached(config):
        """Load data from database - cached version"""
        try:
            # Future implementation with SQLAlchemy
            import sqlalchemy
            engine = sqlalchemy.create_engine(config.get('connection_string'))

            # Execute query and return DataFrame
            df = pd.read_sql(config.get('query'), engine)
            engine.dispose()  # Clean up connection

            return df, "success"

        except sqlalchemy.exc.SQLAlchemyError as e:
            return None, f"database_error: {str(e)}"
        except Exception as e:
            return None, f"unknown_error: {str(e)}"

    # Class method (clean interface)
    class DataLoader:
        @staticmethod
        def _load_database_api(config):
            """Load data from database"""
            return _load_database_api_cached(config)


# === MAIN DATA LOADING WITH ROUTER ===
# Pure cached functions for each data source
@st.cache_data
def _load_github_data_cached(url):
    """Cached GitHub data loading"""
    try:
        if url == "BOTH":
            return None, "both_selected"
        df = pd.read_csv(url)
        return df, "success"
    except Exception as e:
        return None, f"error: {str(e)}"


@st.cache_data
def _load_api_data_cached(api_config):
    """Cached API data loading"""
    try:
        if api_config.get('type') == 'REST API':
            # REST API logic inline
            headers = {}
            if api_config.get('auth_method') == 'API Key':
                headers[api_config.get('key_header')] = api_config.get('api_key')
            elif api_config.get('auth_method') == 'Bearer Token':
                headers['Authorization'] = f"Bearer {api_config.get('bearer_token')}"

            response = requests.get(api_config.get('url'), headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            if 'data' in data:
                return pd.DataFrame(data['data']), "success"
            else:
                return pd.DataFrame(data if isinstance(data, list) else [data]), "success"

        elif api_config.get('type') == 'Database API':
            # Database logic inline
            import sqlalchemy
            engine = sqlalchemy.create_engine(api_config.get('connection_string'))
            df = pd.read_sql(api_config.get('query'), engine)
            engine.dispose()
            return df, "success"
        else:
            return None, "unsupported_api_type"
    except Exception as e:
        return None, f"error: {str(e)}"



# Non-cached function for uploaded files (can't cache file objects)
def _load_uploaded_data(file_obj, date_col, direction_col, variable_col,
                        data_format, nb_col, sb_col):
    """Load uploaded data (not cached due to file objects)"""
    try:
        # Your uploaded data logic here
        return df, "success"
    except Exception as e:
        return None, f"error: {str(e)}"


# Router function with UI handling
def load_data_by_source(data_source, **kwargs):
    """Load data based on selected source with UI feedback"""

    if data_source == "GitHub Repository":
        data, status = _load_github_data_cached(kwargs.get('url'))

    elif data_source == "Uploaded CSV":
        data, status = _load_uploaded_data(
            kwargs.get('file_obj'),
            kwargs.get('date_col'),
            kwargs.get('direction_col'),
            kwargs.get('variable_col'),
            kwargs.get('data_format', 'Long format'),
            kwargs.get('nb_col'),
            kwargs.get('sb_col')
        )

    elif data_source == "API Connection":
        data, status = _load_api_data_cached(kwargs.get('api_config'))

    else:
        st.error(f"❌ Unknown data source: {data_source}")
        return None

    # Handle status and show UI messages
    if status == "success":
        st.success("✅ Data loaded successfully!")
        return data
    elif status == "both_selected":
        st.info("ℹ️ Please select a specific repository")
        return None
    elif status.startswith("error"):
        st.error(f"❌ Loading failed: {status.replace('error: ', '')}")
        return None
    else:
        st.error(f"❌ {status}")
        return None


# === USAGE IN MAIN APP ===
if data_source == "GitHub Repository":
    # NEW: Load data using the new function
    df, dataset_info = load_washington_st_data(variable, direction)

    if df is None:
        st.error("No data available for the selected combination.")
        st.stop()

    # Set selected_path for compatibility (optional)
    selected_path = dataset_info["url"] if dataset_info else "New data loading system"

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
    # ==BOTH DIRECTION LOGIC== If "Both", load two files or one with two columns
    if direction == "Both":
        if variable == "Vehicle Volume":
            # KINETIC MOBILITY: Single file contains both directions
            df = pd.read_csv(selected_path)

            # Check if Time column exists, if not find it
            time_col = find_time_column(df)
            if not time_col:
                st.error("No time column found. Please ensure your data has a time-related column.")
                st.stop()

            # For Vehicle Volume data - combine date with time if needed
            if variable == "Vehicle Volume":
                # Check if the time column contains only time (no date)
                sample_time = str(df[time_col].iloc[0]) if not df.empty else ""
                if len(sample_time.split()) == 1 and ":" in sample_time:
                    # Only time found, need to extract date from date_range
                    date_range_str = str(date_range).lower()

                    # Try to extract date from various formats
                    import re

                    # Look for YYYY-MM-DD format
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', str(date_range))
                    if date_match:
                        base_date = date_match.group(1)
                    else:
                        # Try other formats like MM/DD/YYYY or DD/MM/YYYY
                        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', str(date_range))
                        if date_match:
                            month, day, year = date_match.groups()
                            base_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        else:
                            # Fallback - try to parse the entire date_range
                            try:
                                parsed_date = pd.to_datetime(str(date_range)).strftime('%Y-%m-%d')
                                base_date = parsed_date
                            except:
                                base_date = "2025-04-10"  # ultimate fallback

                    df[time_col] = pd.to_datetime(base_date + " " + df[time_col].astype(str), errors="coerce")
                else:
                    # Full datetime already present
                    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
            else:
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
                    fig.update_layout(yaxis_title="Vehicle Volume")
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Scatter":
                    fig = px.scatter(combined, x=time_col, y=["Northbound", "Southbound"],
                                     title=clean_title)
                    fig.update_layout(yaxis_title="Vehicle Volume")
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Box":
                    # Melt the dataframe for box plot
                    melted = combined.melt(id_vars=[time_col], value_vars=["Northbound", "Southbound"],
                                           var_name="Direction", value_name="Volume")
                    fig = px.box(melted, x="Direction", y="Volume",
                                 title=f"{clean_title} - Distribution Analysis")
                    fig.update_layout(yaxis_title="Vehicle Volume")
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Heatmap":


                    # Create side-by-side heatmaps
                    st.subheader("📊 Hourly Traffic Pattern Analysis")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**🔵 Northbound Traffic**")
                        df_nb = combined[[time_col, "Northbound"]].copy()
                        df_nb['hour'] = df_nb[time_col].dt.hour
                        # Sort by date first, then format for display
                        df_nb = df_nb.sort_values(time_col)
                        df_nb['day'] = df_nb[time_col].dt.strftime('%a %m/%d')
                        pivot_nb = df_nb.pivot_table(values="Northbound", index='day', columns='hour')
                        fig_nb = px.imshow(pivot_nb, aspect='auto', title="Northbound Pattern")
                        fig_nb.update_layout(coloraxis_colorbar_title="Vehicle Volume")

                        # EDIT X-AXIS AND Y-AXIS TITLES - BEFORE displaying chart
                        fig_nb.update_xaxes(title="Time (24-Hour)")
                        fig_nb.update_yaxes(title="Date")

                        st.plotly_chart(fig_nb, use_container_width=True)

                    with col2:
                        st.markdown("**🔴 Southbound Traffic**")
                        df_sb = combined[[time_col, "Southbound"]].copy()
                        df_sb['hour'] = df_sb[time_col].dt.hour
                        df_sb = df_sb.sort_values(time_col)
                        df_sb['day'] = df_sb[time_col].dt.strftime('%a %m/%d')
                        pivot_sb = df_sb.pivot_table(values="Southbound", index='day', columns='hour')
                        fig_sb = px.imshow(pivot_sb, aspect='auto', title="Southbound Pattern")
                        fig_sb.update_layout(coloraxis_colorbar_title="Vehicle Volume")

                        # EDIT X-AXIS AND Y-AXIS TITLES - BEFORE displaying chart
                        fig_sb.update_xaxes(title="Time (24-Hour)")
                        fig_sb.update_yaxes(title="Date")

                        st.plotly_chart(fig_sb, use_container_width=True)

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
                    df_nb_heat = df_nb_heat.sort_values(time_col)
                    df_nb_heat['day'] = df_nb_heat[time_col].dt.strftime('%a %m/%d')
                    pivot_nb = df_nb_heat.pivot_table(values="Northbound", index='day', columns='hour')
                    pivot_nb = pivot_nb.reindex(sorted(pivot_nb.index, key=lambda x: pd.to_datetime(x, format='%a %m/%d')))
                    fig_nb = px.imshow(pivot_nb, aspect='auto', title="Northbound Pattern")
                    unit = "mph" if variable == "Speed" else "min"
                    fig_nb.update_layout(coloraxis_colorbar_title=f"{variable} ({unit})")
                    st.plotly_chart(fig_nb, use_container_width=True)

                with col2:
                    st.markdown("**🔴 Southbound**")
                    df_sb_heat = combined[[time_col, "Southbound"]].copy()
                    df_sb_heat['hour'] = df_sb_heat[time_col].dt.hour
                    df_sb_heat = df_sb_heat.sort_values(time_col)
                    df_sb_heat['day'] = df_sb_heat[time_col].dt.strftime('%a %m/%d')
                    pivot_sb = df_sb_heat.pivot_table(values="Southbound", index='day', columns='hour')
                    pivot_sb = pivot_sb.reindex(sorted(pivot_sb.index, key=lambda x: pd.to_datetime(x, format='%a %m/%d')))
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

        # For Vehicle Volume data - combine date with time if needed
        if variable == "Vehicle Volume":
            # Check if the time column contains only time (no date)
            sample_time = str(df[time_col].iloc[0]) if not df.empty else ""
            if len(sample_time.split()) == 1 and ":" in sample_time:
                # Only time found, need to extract date from date_range
                date_range_str = str(date_range).lower()

                # Try to extract date from various formats
                import re

                # Look for YYYY-MM-DD format
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', str(date_range))
                if date_match:
                    base_date = date_match.group(1)
                else:
                    # Try other formats like MM/DD/YYYY or DD/MM/YYYY
                    date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', str(date_range))
                    if date_match:
                        month, day, year = date_match.groups()
                        base_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:
                        # Fallback - try to parse the entire date_range
                        try:
                            parsed_date = pd.to_datetime(str(date_range)).strftime('%Y-%m-%d')
                            base_date = parsed_date
                        except:
                            base_date = "2025-04-10"  # ultimate fallback

                df[time_col] = pd.to_datetime(base_date + " " + df[time_col].astype(str), errors="coerce")
            else:
                # Full datetime already present
                df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
        else:
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
                    fig.update_layout(yaxis_title="Vehicle Volume")
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Scatter":
                    fig = px.scatter(df, x=time_col, y=y_col, title=clean_title)
                    fig.update_layout(yaxis_title="Vehicle Volume")
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Box":
                    fig = px.box(df, y=y_col, title=f"{clean_title} - Distribution Analysis")
                    fig.update_layout(yaxis_title="Vehicle Volume")
                    st.plotly_chart(fig, use_container_width=True)
                elif chart_type == "Heatmap":
                    df_heat = df.copy()
                    df_heat['hour'] = df_heat[time_col].dt.hour
                    df_heat = df_heat.sort_values(time_col)
                    df_heat['day'] = df_heat[time_col].dt.strftime('%a %m/%d')
                    pivot_table = df_heat.pivot_table(values=y_col, index='day', columns='hour')
                    pivot_table = pivot_table.reindex(sorted(pivot_table.index, key=lambda x: pd.to_datetime(x, format='%a %m/%d')))
                    fig = px.imshow(pivot_table, aspect='auto', title=f"{clean_title} - Hourly Pattern")
                    fig.update_layout(coloraxis_colorbar_title="Vehicle Volume")

                    # Add axis titles BEFORE displaying chart
                    fig.update_xaxes(title="Time (24-Hour)")
                    fig.update_yaxes(title="Date")

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
                df_heat = df_heat.sort_values(time_col)
                df_heat['day'] = df_heat[time_col].dt.strftime('%a %m/%d')
                pivot_table = df_heat.pivot_table(values=y_col, index='day', columns='hour')
                fig = px.imshow(pivot_table, aspect='auto', title=f"{clean_title} - Hourly Pattern")
                unit = "mph" if variable == "Speed" else "min"
                fig.update_layout(coloraxis_colorbar_title=f"{variable} ({unit})")

                # Add axis titles BEFORE displaying chart
                fig.update_xaxes(title="Time (24-Hour)")
                fig.update_yaxes(title="Date")

                st.plotly_chart(fig, use_container_width=True)


except Exception as e:
    st.error(f"❌ Failed to load chart: {e}")
    st.write("Debug info - Available columns:", list(df.columns) if 'df' in locals() else "DataFrame not loaded")


# --- Robust find_column function ---
@st.cache_data
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


# == CYCLE LENGTH TOGGLE IMPORT ==
from Analysis.CycleLength_Recommendations import render_volume_analysis

# === TRAFFIC VOLUME ANALYSIS ===
render_volume_analysis(df, time_period, direction)


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
@st.cache_data
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
                        st.metric("Total Volume", f"{total_volume:,.0f} Vehicles")
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
