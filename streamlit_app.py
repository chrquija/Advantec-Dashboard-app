
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# === Set up the app ===
st.set_page_config(
    page_title="Transportation Dashboard",
    page_icon="📊",
    layout="wide"
)

# App title
st.title("📊 Active Transportation & Operations Management Dashboard")

# === SIDEBAR ===
with st.sidebar:
    st.image("Logos/ACE-logo-HiRes.jpg", width=200)

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

            # Load the selected file
            df = pd.read_csv(st.session_state.uploaded_files[selected_file])

            # Column mapping dropdowns
            date_column = st.selectbox(
                "Select column for date:",
                ["Select column..."] + list(df.columns),
                key="date_column"
            )

            direction_column = st.selectbox(
                "Select column for direction:",
                ["Select column..."] + list(df.columns),
                key="direction_column"
            )

            variable_column = st.selectbox(
                "Select column for variable:",
                ["Select column..."] + list(df.columns),
                key="variable_column"
            )

            # Validation
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
     "May 9–18, 2025"): base_url + "SPEED/Weeks_05092025_to_05182025/SB_Washington_Hwy_111_to_Avenue_52_SPEED_1hr_0509_05182025.csv",
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
    def load_uploaded_data(file_obj, date_col, direction_col, variable_col):
        """Load and process uploaded CSV data"""
        try:
            df = pd.read_csv(file_obj)

            # Rename columns to match expected format
            df = df.rename(columns={
                date_col: 'Date',
                direction_col: 'Direction',
                variable_col: 'Value'
            })

            # Convert date column to datetime
            df['Date'] = pd.to_datetime(df['Date'])

            return df
        except Exception as e:
            st.error(f"Error processing uploaded file: {e}")
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
    """Route data loading based on selected source"""

    if data_source == "GitHub Repository":
        return DataLoader.load_github_data(kwargs.get('url'))

    elif data_source == "Uploaded CSV":
        return DataLoader.load_uploaded_data(
            kwargs.get('file_obj'),
            kwargs.get('date_col'),
            kwargs.get('direction_col'),
            kwargs.get('variable_col')
        )

    elif data_source == "API Connection":
        return DataLoader.load_api_data(kwargs.get('api_config'))

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
    df = load_data_by_source(
        "Uploaded CSV",
        file_obj=st.session_state.uploaded_files[selected_file],
        date_col=date_column,
        direction_col=direction_column,
        variable_col=variable_column
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

# === Display UI selections ===
st.write("**Date Range:**", date_range)
st.write("**Corridor Segment:**", corridor_segment)
st.write("**Selected Variable:**", variable)
st.write("**Direction:**", direction)
st.write("**GitHub CSV File Path:**", selected_path)

# === Chart Type Selector ===
chart_type = st.selectbox("Choose chart type", ["Line", "Bar", "Scatter", "Box", "Heatmap"])

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
    
    return fig

# === Load and Render Chart ===
try:
    # If "Both", load two files or one with two columns
    if direction == "Both":
        if variable == "Vehicle Volume":
            # KINETIC MOBILITY: Single file contains both directions
            df = pd.read_csv(selected_path)
            time_col = "Time"
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
            df.dropna(subset=[time_col], inplace=True)
            df.set_index(time_col, inplace=True)

            # Find both direction columns
            nb_cols = [col for col in df.columns if "northbound" in col.lower()]
            sb_cols = [col for col in df.columns if "southbound" in col.lower()]

            if nb_cols and sb_cols:
                nb_col = nb_cols[0]
                sb_col = sb_cols[0]

                df[nb_col] = pd.to_numeric(df[nb_col], errors='coerce')
                df[sb_col] = pd.to_numeric(df[sb_col], errors='coerce')

                # Rename for cleaner display
                df = df.rename(columns={nb_col: "Northbound", sb_col: "Southbound"})

                combined = df[["Northbound", "Southbound"]].copy()
                combined.dropna(inplace=True)
                combined.reset_index(inplace=True)

                fig = create_enhanced_multi_line_chart(combined, time_col, ["Northbound", "Southbound"], "Vehicle Volume - Both Directions")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Could not find both direction columns in volume data")

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

            # Use "Firsts" column for the main metric
            y_col = "Firsts"
            df_nb[y_col] = pd.to_numeric(df_nb[y_col], errors='coerce')
            df_sb[y_col] = pd.to_numeric(df_sb[y_col], errors='coerce')

            df_nb = df_nb.rename(columns={y_col: "NB"})
            df_sb = df_sb.rename(columns={y_col: "SB"})

            combined = pd.concat([df_nb["NB"], df_sb["SB"]], axis=1)
            combined.dropna(inplace=True)
            combined.reset_index(inplace=True)

            fig = create_enhanced_multi_line_chart(combined, time_col, ["NB", "SB"], f"{variable} NB & SB Over Time")
            st.plotly_chart(fig, use_container_width=True)

    else:
        # Single-direction logic - handle different data sources
        df = pd.read_csv(selected_path)

        # Determine data source based on columns
        if variable == "Vehicle Volume":
            # KINETIC MOBILITY FORMAT: Time, [Date] Northbound, [Date] Southbound
            time_col = "Time"
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
            df.dropna(subset=[time_col], inplace=True)
            df.set_index(time_col, inplace=True)

            # Find the correct column based on direction
            if direction == "NB":
                nb_cols = [col for col in df.columns if "northbound" in col.lower()]
                if nb_cols:
                    y_col = nb_cols[0]
                else:
                    st.error("Northbound column not found")
                    st.stop()
            elif direction == "SB":
                sb_cols = [col for col in df.columns if "southbound" in col.lower()]
                if sb_cols:
                    y_col = sb_cols[0]
                else:
                    st.error("Southbound column not found")
                    st.stop()

            df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
            chart_title = f"Vehicle Volume - {direction}"

        else:
            # FLIR ACYCLICA FORMAT: Time, Strength, Firsts, Lasts, Minimum, Maximum
            time_col = "Time"
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
            df.dropna(subset=[time_col], inplace=True)
            df.set_index(time_col, inplace=True)

            # Use "Firsts" column for Speed and Travel Time
            y_col = "Firsts"
            df[y_col] = pd.to_numeric(df[y_col], errors='coerce')

            if variable == "Speed":
                chart_title = f"Speed (mph) - {direction}"
            elif variable == "Travel Time":
                chart_title = f"Travel Time - {direction}"

        # Remove NaN values after conversion
        df.dropna(subset=[y_col], inplace=True)
        df.reset_index(inplace=True)

        # Generate enhanced charts
        if not df.empty and y_col in df.columns:
            if chart_type == "Line":
                fig = create_enhanced_line_chart(df, time_col, y_col, chart_title)
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Bar":
                fig = px.bar(df, x=time_col, y=y_col, title=chart_title)
                fig.update_layout(yaxis_title="Vehicle Volume" if variable == "Vehicle Volume" else y_col)
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Scatter":
                fig = px.scatter(df, x=time_col, y=y_col, title=chart_title)
                fig.update_layout(yaxis_title="Vehicle Volume" if variable == "Vehicle Volume" else y_col)
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Box":
                fig = px.box(df, y=y_col, title=f"{chart_title} Distribution")
                fig.update_layout(yaxis_title="Vehicle Volume" if variable == "Vehicle Volume" else y_col)
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Heatmap":
                df['hour'] = df[time_col].dt.hour
                df['day'] = df[time_col].dt.date
                pivot = df.pivot_table(values=y_col, index='day', columns='hour')
                fig = px.imshow(pivot, aspect='auto', title=f"{chart_title} Heatmap")
                fig.update_layout(yaxis_title="Date", coloraxis_colorbar_title="Vehicle Volume" if variable == "Vehicle Volume" else y_col)
                st.plotly_chart(fig, use_container_width=True)

            # Show stats with proper units
            if variable == "Travel Time":
                # Check if Travel_time_units column exists
                if 'Travel_time_units' in df.columns:
                    units = df['Travel_time_units'].iloc[0] if not df['Travel_time_units'].empty else "min"
                else:
                    units = "min"  # default assumption

                st.write(f"**Average {variable}:** {df[y_col].mean():.2f} {units}")
                st.write(f"**Min {variable}:** {df[y_col].min():.2f} {units}")
                st.write(f"**Max {variable}:** {df[y_col].max():.2f} {units}")
            elif variable == "Speed":
                st.write(f"**Average {variable}:** {df[y_col].mean():.2f} mph")
                st.write(f"**Min {variable}:** {df[y_col].min():.2f} mph")
                st.write(f"**Max {variable}:** {df[y_col].max():.2f} mph")
            else:
                st.write(f"**Average {variable}:** {df[y_col].mean():.2f}")
                st.write(f"**Min {variable}:** {df[y_col].min():.2f}")
                st.write(f"**Max {variable}:** {df[y_col].max():.2f}")
        else:
            st.warning(f"No valid data found in {y_col} column.")

except Exception as e:
    st.error(f"❌ Failed to load chart: {e}")

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

    # Prepare data for KPIs
    kpi_df = df.copy()
    time_col = "Time"

    # Ensure 'Time' is datetime
    # Replace the problematic line with this safer version:
    if time_col and time_col in kpi_df.columns and not np.issubdtype(kpi_df[time_col].dtype, np.datetime64):
        kpi_df[time_col] = pd.to_datetime(kpi_df[time_col])

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
                    st.metric("Recommended Cycle Length Activation Period (24-Hour)", hours_str)
                    st.metric("Total Activation Period Vehicle Volume", f"{consecutive_volume:,.0f} Vehicles")
                    st.metric("Total (direction) Vehicle Volume", f"{total_peak_direction_volume:,.0f} Vehicles")
                else:

                    st.metric("Busiest Direction (NB or SB)", peak_direction)
                    st.metric("Recommended Cycle Length Activation Period (24-Hour)", "Free mode")
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


                        if direction_choice == "Both":
                            # Show combined table for both directions
                            if nb_vol_col in period_df and sb_vol_col in period_df:
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
                            if vol_col in period_df:
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
