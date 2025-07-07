
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

# === Sidebar Selections ===
st.sidebar.image("Logos/ACE-logo-HiRes.jpg", width=200)
st.sidebar.title("⚙️ Dashboard Filters")

# Step 1: Pick variable type
variable = st.sidebar.selectbox("SELECT CATEGORY", ["Speed", "Travel Time", "Vehicle Volume"])

# Step 2: Pick direction
direction = st.sidebar.radio("Direction", ["NB", "SB", "Both"])

# Step 3: Pick date range
date_range = st.sidebar.selectbox(
    "Select Date Range",
    ["April 11–20, 2025", "May 9–18, 2025"] if variable != "Vehicle Volume" else ["April 10, 2025", "Feb 13, 2025"]
)

# === Filepath Mapping Logic ===
base_url = "https://raw.githubusercontent.com/chrquija/Advantec-Dashboard-app/refs/heads/main/hwy111_to_ave52/"
corridor_segment = "Washington St: Highway 111 to Avenue 52"

path_map = {
    # === SPEED ===
    ("Speed", "NB", "April 11–20, 2025"): base_url + "SPEED/Weeks_04112025_to_04202025/NB_Washington_Avenue_52_to_Hwy_111_SPEED_1hr_0411_04202025.csv",
    ("Speed", "SB", "April 11–20, 2025"): base_url + "SPEED/Weeks_04112025_to_04202025/SB_Washington_Hwy_111_to_Avenue_52_SPEED_1hr_0411_04202025.csv",
    ("Speed", "Both", "April 11–20, 2025"): "BOTH",

    ("Speed", "NB", "May 9–18, 2025"): base_url + "SPEED/Weeks_05092025_to_05182025/NB_Washington_Avenue_52_to_Hwy_111_%20SPEED_1hr_0509_05182025.csv",
    ("Speed", "SB", "May 9–18, 2025"): base_url + "SPEED/Weeks_05092025_to_05182025/SB_Washington_Hwy_111_to_Avenue_52_SPEED_1hr_0509_05182025.csv",
    ("Speed", "Both", "May 9–18, 2025"): "BOTH",
    
    # === TRAVEL TIME ===
    ("Travel Time", "NB", "April 11–20, 2025"): base_url + "TRAVEL_TIME/Weeks_04112025_to_04202025/NB_Washington_Avenue_52_to_Hwy_111_TRAVEL_TIME_1hr_0411_04202025.csv",
    ("Travel Time", "SB", "April 11–20, 2025"): base_url + "TRAVEL_TIME/Weeks_04112025_to_04202025/SB_Washington_Hwy_111_to_Avenue_52_TRAVEL_TIME_1hr_0411_04202025.csv",
    ("Travel Time", "Both", "April 11–20, 2025"): "BOTH",

    ("Travel Time", "NB", "May 9–18, 2025"): base_url + "TRAVEL_TIME/Weeks_05092025_to_05182025/NB_Washington_Avenue_52_to_Hwy_111_TRAVEL_TIME_1_hr_0509_05182025.csv",
    ("Travel Time", "SB", "May 9–18, 2025"): base_url + "TRAVEL_TIME/Weeks_05092025_to_05182025/SB_Washington_Hwy_111_to_Avenue_52_TRAVEL_TIME_1_hr_0509_05182025.csv",
    ("Travel Time", "Both", "May 9–18, 2025"): "BOTH",

    # === VEHICLE VOLUME (April 10) — All 3 use same file ===
    ("Vehicle Volume", "NB", "April 10, 2025"): base_url + "VOLUME/Thursday_April_10/Washington_and_Ave_52_NB_and_SB_VolumeDATA_THURSDAY_APRIL_10.csv",
    ("Vehicle Volume", "SB", "April 10, 2025"): base_url + "VOLUME/Thursday_April_10/Washington_and_Ave_52_NB_and_SB_VolumeDATA_THURSDAY_APRIL_10.csv",
    ("Vehicle Volume", "Both", "April 10, 2025"): base_url + "VOLUME/Thursday_April_10/Washington_and_Ave_52_NB_and_SB_VolumeDATA_THURSDAY_APRIL_10.csv",

    # === VEHICLE VOLUME (Feb 13) — All 3 use same file ===
    ("Vehicle Volume", "NB", "Feb 13, 2025"): base_url + "VOLUME/Thursday_Feb_13/Washington_and_Ave_52_NB_and_SB_VolumeDATA_Thursday_Feb_13.csv",
    ("Vehicle Volume", "SB", "Feb 13, 2025"): base_url + "VOLUME/Thursday_Feb_13/Washington_and_Ave_52_NB_and_SB_VolumeDATA_Thursday_Feb_13.csv",
    ("Vehicle Volume", "Both", "Feb 13, 2025"): base_url + "VOLUME/Thursday_Feb_13/Washington_and_Ave_52_NB_and_SB_VolumeDATA_Thursday_Feb_13.csv",
}

selected_path = path_map.get((variable, direction, date_range), "No path available for selection.")

# === Display UI selections ===
st.write("**Date Range:**", date_range)
st.write("**Corridor Segment:**", corridor_segment)
st.write("**Selected Variable:**", variable)
st.write("**Direction:**", direction)
st.write("**GitHub CSV File Path:**", selected_path)

# === Chart Type Selector ===
chart_type = st.selectbox("Choose chart type", ["Line", "Bar", "Scatter", "Box", "Heatmap"])

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
        yaxis_title=y_col,
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
        yaxis_title="Value",
        hovermode='x unified',
        showlegend=True,
        plot_bgcolor='white',
        margin=dict(t=80, b=50, l=50, r=50),
        height=500
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
    
    return fig

# === 2x2 Chart Grid Layout ===
st.markdown("## 📊 Interactive Chart Panels")

# Create 2 rows with 2 columns each
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)
chart_cols = [row1_col1, row1_col2, row2_col1, row2_col2]

panel_titles = ["Panel 1", "Panel 2", "Panel 3", "Panel 4"]
chart_options = ["Speed", "Travel Time", "Vehicle Volume"]
direction_options = ["NB", "SB", "Both"]
chart_types = ["Line", "Bar", "Scatter", "Box", "Heatmap"]

for i, col in enumerate(chart_cols):
    with col:
        st.markdown(f"### {panel_titles[i]}")
        # Panel-specific filters (can use sidebar values if you want everything synced)
        panel_variable = st.selectbox(f"Variable ({panel_titles[i]})", chart_options, key=f"var_{i}")
        panel_direction = st.radio(f"Direction ({panel_titles[i]})", direction_options, key=f"dir_{i}")
        panel_chart_type = st.selectbox(f"Chart Type ({panel_titles[i]})", chart_types, key=f"chart_{i}")

        # Get the correct file path for this panel
        panel_path = path_map.get((panel_variable, panel_direction, date_range), None)
        if panel_path and "No path" not in panel_path:
            try:
                panel_df = pd.read_csv(panel_path)
                # Standardize 'Time'
                if "Time" in panel_df.columns:
                    panel_df["Time"] = pd.to_datetime(panel_df["Time"], errors="coerce")
                    panel_df = panel_df.dropna(subset=["Time"])
                    # Find y_col
                    y_col = None
                    if panel_variable == "Speed":
                        y_col = "Firsts" if "Firsts" in panel_df.columns else panel_df.columns[1]
                    elif panel_variable == "Travel Time":
                        y_col = "Firsts" if "Firsts" in panel_df.columns else panel_df.columns[1]
                    elif panel_variable == "Vehicle Volume":
                        if panel_direction == "NB":
                            y_col = [col for col in panel_df.columns if "northbound" in col.lower()]
                            y_col = y_col[0] if y_col else panel_df.columns[1]
                        elif panel_direction == "SB":
                            y_col = [col for col in panel_df.columns if "southbound" in col.lower()]
                            y_col = y_col[0] if y_col else panel_df.columns[1]
                        else:
                            y_col = panel_df.columns[1]

                    if y_col and y_col in panel_df.columns:
                        if panel_chart_type == "Line":
                            fig = px.line(panel_df, x="Time", y=y_col, title=f"{panel_variable} - {panel_direction}")
                            st.plotly_chart(fig, use_container_width=True)
                        elif panel_chart_type == "Bar":
                            fig = px.bar(panel_df, x="Time", y=y_col, title=f"{panel_variable} - {panel_direction}")
                            st.plotly_chart(fig, use_container_width=True)
                        elif panel_chart_type == "Scatter":
                            fig = px.scatter(panel_df, x="Time", y=y_col, title=f"{panel_variable} - {panel_direction}")
                            st.plotly_chart(fig, use_container_width=True)
                        elif panel_chart_type == "Box":
                            fig = px.box(panel_df, y=y_col, title=f"{panel_variable} - {panel_direction}")
                            st.plotly_chart(fig, use_container_width=True)
                        elif panel_chart_type == "Heatmap":
                            panel_df['hour'] = panel_df["Time"].dt.hour
                            pivot = panel_df.pivot_table(values=y_col, index=panel_df["Time"].dt.date, columns='hour')
                            fig = px.imshow(pivot, aspect='auto', title=f"{panel_variable} Heatmap")
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Chart type not available.")
                    else:
                        st.info("No valid data columns for this variable/direction.")
                else:
                    st.info("No 'Time' column in file.")
            except Exception as e:
                st.warning(f"Error loading chart: {e}")
        else:
            st.info("No data found for this selection.")


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
        if v >= 2405:
            return "140 sec"
        elif v >= 1505:
            cycle = "130 sec"
        elif v >= 605:
            if cycle not in ["130 sec", "140 sec"]:
                cycle = "120 sec"
        elif v >= 305:
            if cycle not in ["120 sec", "130 sec", "140 sec"]:
                cycle = "110 sec"
    return cycle


# Helper function to filter data by time period
def filter_by_period(df, time_col, period):
    """Filter dataframe by time period"""
    df_copy = df.copy()
    df_copy['hour'] = df_copy[time_col].dt.hour
    
    if period == "AM":
        return df_copy[(df_copy['hour'] >= 5) & (df_copy['hour'] < 10)]
    elif period == "MD":
        return df_copy[(df_copy['hour'] >= 11) & (df_copy['hour'] < 15)]
    elif period == "PM":
        return df_copy[(df_copy['hour'] >= 16) & (df_copy['hour'] < 20)]
    return df_copy


# Only show KPI panels for Vehicle Volume data
if variable == "Vehicle Volume":
    st.markdown("---")
    st.subheader("📈 Key Performance Indicators")

    # Create 4 columns for KPI panels
    col1, col2, col3, col4 = st.columns(4)

    # Time period selector (shared across all KPIs)
    time_period = st.selectbox("Select Time Period:", ["AM (5:00-10:00)", "MD (11:00-15:00)", "PM (16:00-20:00)"])
    period_key = time_period.split(" ")[0]  # Extract AM/MD/PM

    # Prepare data for KPIs
    kpi_df = df.copy()
    time_col = "Time"

    # Ensure 'Time' is datetime
    if not np.issubdtype(kpi_df[time_col].dtype, np.datetime64):
        kpi_df[time_col] = pd.to_datetime(kpi_df[time_col], errors='coerce')

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
            st.markdown("### 🚦 Suggested Cycle Length")

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

                    # Calculate volume for consecutive hours period
                    consecutive_df = period_df[period_df[time_col].isin(consecutive_hours)]
                    consecutive_volume = consecutive_df[peak_vol_col].sum()

                    # Get the hourly volumes for each hour in the consecutive period
                    hourly_volumes = consecutive_df[peak_vol_col].tolist()
                    cycle_rec = get_cycle_length_recommendation(hourly_volumes)  # Pass the list!

                    st.metric("Peak Direction", peak_direction)
                    st.metric("Peak Period", hours_str)
                    st.metric("Total Period Volume", f"{consecutive_volume:,.0f} vph")
                    st.metric("Cycle Length Recommendation", cycle_rec)
                else:
                    st.metric("Peak Direction", peak_direction)
                    st.metric("Peak Period", "Free mode")
                    st.metric("Total Period Volume", "Free mode")
                    st.metric("Cycle Length Recommendation", "Free mode")
            else:
                st.write("No data for selected period")

        # === KPI 2-4: Dynamic KPIs ===
        kpi_options = ["Average Speed", "Total Volume", "Peak Congestion Time", "Hourly Cycle Length Table"]
        if nb_speed_col and sb_speed_col:
            kpi_options = ["Average Speed", "Peak Speed", "Total Volume", "Peak Congestion Time",
                           "Hourly Cycle Length Table"]

        for i, col in enumerate([col2, col3, col4]):
            with col:
                kpi_type = st.selectbox(f"KPI {i + 2}:", kpi_options, key=f"kpi_{i + 2}")
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
                    elif kpi_type == "Hourly Cycle Length Table":
                        vol_col = nb_vol_col if direction_choice == "NB" else sb_vol_col
                        if vol_col in period_df:
                            hourly_df = period_df.copy()
                            hourly_df["Hour"] = hourly_df[time_col].dt.strftime("%H:%M")
                            hourly_df["Volume"] = hourly_df[vol_col]


                            # Function for each hour
                            def get_hourly_cycle_length(volume):
                                if volume >= 2405:
                                    return "140 sec"
                                elif volume >= 1505:
                                    return "130 sec"
                                elif volume >= 605:
                                    return "120 sec"
                                elif volume >= 305:
                                    return "110 sec"
                                else:
                                    return "Free mode"


                            hourly_df["Cycle Length"] = hourly_df["Volume"].apply(get_hourly_cycle_length)
                            table_df = hourly_df[["Hour", "Volume", "Cycle Length"]].reset_index(drop=True)
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
