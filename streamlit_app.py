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
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Scatter":
                fig = px.scatter(df, x=time_col, y=y_col, title=chart_title)
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Box":
                fig = px.box(df, y=y_col, title=f"{chart_title} Distribution")
                st.plotly_chart(fig, use_container_width=True)
            elif chart_type == "Heatmap":
                df['hour'] = df[time_col].dt.hour
                df['day'] = df[time_col].dt.date
                pivot = df.pivot_table(values=y_col, index='day', columns='hour')
                fig = px.imshow(pivot, aspect='auto', title=f"{chart_title} Heatmap")
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