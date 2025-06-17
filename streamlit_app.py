import streamlit as st
import pandas as pd
import plotly.express as px

# === Sidebar Selections ===
st.sidebar.title("🚦 CVAG Dashboard Filters")

# Step 1: Pick variable type
variable = st.sidebar.selectbox("Select Variable", ["Speed", "Travel Time", "Vehicle Volume"])

# Step 2: Pick direction
direction = st.sidebar.radio("Direction", ["NB", "SB"])

# Step 3: Pick date range
date_range = st.sidebar.selectbox(
    "Select Date Range",
    ["April 11–20, 2025", "May 9–18, 2025"] if variable != "Vehicle Volume" else ["April 10, 2025", "Feb 13, 2025"]
)

# === Filepath Mapping Logic ===
base_url = "https://raw.githubusercontent.com/chrquija/Advantec-Dashboard-app/main/hwy111_to_ave52/"
corridor_segment = "Washington St: Highway 111 to Avenue 52"

path_map = {
    # === SPEED ===
    ("Speed", "NB", "April 11–20, 2025"): base_url + "SPEED/Weeks_04112025_to_04202025/NB_Washington_Avenue_52_to_Hwy_111_SPEED_1hr_0411_04202025.csv",
    ("Speed", "SB", "April 11–20, 2025"): base_url + "SPEED/Weeks_04112025_to_04202025/SB_Washington_Hwy_111_to_Avenue_52_SPEED_1hr_0411_04202025.csv",
    ("Speed", "NB", "May 9–18, 2025"): base_url + "SPEED/Weeks_05092025_to_05182025/NB_Washington_Avenue_52_to_Hwy_111_SPEED_1hr_0509_05182025.csv",
    ("Speed", "SB", "May 9–18, 2025"): base_url + "SPEED/Weeks_05092025_to_05182025/SB_Washington_Hwy_111_to_Avenue_52_SPEED_1hr_0509_05182025.csv",

    # === TRAVEL TIME ===
    ("Travel Time", "NB", "April 11–20, 2025"): base_url + "TRAVEL_TIME/Weeks_04112025_to_04202025/NB_Washington_Avenue_52_to_Hwy_111_TRAVEL_TIME_1hr_0411_04202025.csv",
    ("Travel Time", "SB", "April 11–20, 2025"): base_url + "TRAVEL_TIME/Weeks_04112025_to_04202025/SB_Washington_Hwy_111_to_Avenue_52_TRAVEL_TIME_1hr_0411_04202025.csv",
    ("Travel Time", "NB", "May 9–18, 2025"): base_url + "TRAVEL_TIME/Weeks_05092025_to_05182025/NB_Washington_Avenue_52_to_Hwy_111_TRAVEL_TIME_1_hr_0509_05182025.csv",
    ("Travel Time", "SB", "May 9–18, 2025"): base_url + "TRAVEL_TIME/Weeks_05092025_to_05182025/SB_Washington_Hwy_111_to_Avenue_52_TRAVEL_TIME_1_hr_0509_05182025.csv",

    # === VEHICLE VOLUME (April 10) ===
    ("Vehicle Volume", "NB", "April 10, 2025"): base_url + "VOLUME/Thursday_April_10/Washington_and_Ave_52_NB_and_SB_VolumeDATA_THURSDAY_APRIL_10.csv",
    ("Vehicle Volume", "SB", "April 10, 2025"): base_url + "VOLUME/Thursday_April_10/Washington_and_Ave_52_NB_and_SB_VolumeDATA_THURSDAY_APRIL_10.csv",

    # === VEHICLE VOLUME (Feb 13) ===
    ("Vehicle Volume", "NB", "Feb 13, 2025"): base_url + "VOLUME/Thursday_Feb_13/Washington_and_Ave_52_NB_and_SB_VolumeDATA_Thursday_Feb_13.csv",
    ("Vehicle Volume", "SB", "Feb 13, 2025"): base_url + "VOLUME/Thursday_Feb_13/Washington_and_Ave_52_NB_and_SB_VolumeDATA_Thursday_Feb_13.csv",
}

selected_path = path_map.get((variable, direction, date_range), "No path available for selection.")

# === Display UI selections ===
st.title("📊 Active Transportation & Operations Management Dashboard")
st.write("**Selected Variable:**", variable)
st.write("**Direction:**", direction)
st.write("**Date Range:**", date_range)
st.write("**Corridor Segment:**", corridor_segment)
st.write("**GitHub CSV File Path:**", selected_path)


# === Chart Type Selector ===
chart_type = st.selectbox("Choose chart type", ["Line", "Bar", "Scatter", "Box", "Heatmap"])

# === Load and Render Chart ===
try:
    df = pd.read_csv(selected_path)

    # Handle time
    time_col = "Datetime" if "Datetime" in df.columns else "Time"
    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
    df.dropna(subset=[time_col], inplace=True)
    df.set_index(time_col, inplace=True)

    # Use first numeric column
    numeric_cols = df.select_dtypes(include='number').columns
    y_col = numeric_cols[0] if len(numeric_cols) > 0 else None

    if y_col:
        if chart_type == "Line":
            fig = px.line(df, x=df.index, y=y_col, title=f"{y_col} Over Time")
        elif chart_type == "Bar":
            fig = px.bar(df, x=df.index, y=y_col, title=f"{y_col} Over Time")
        elif chart_type == "Scatter":
            fig = px.scatter(df, x=df.index, y=y_col, title=f"{y_col} Over Time")
        elif chart_type == "Box":
            fig = px.box(df.reset_index(), x=time_col, y=y_col, title=f"{y_col} Distribution")
        elif chart_type == "Heatmap":
            df['hour'] = df.index.hour
            df['day'] = df.index.date
            pivot = df.pivot_table(values=y_col, index='day', columns='hour')
            fig = px.imshow(pivot, aspect='auto', title=f"{y_col} Heatmap (Hour vs Day)")

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No numeric columns found to visualize.")

except Exception as e:
    st.error(f"❌ Failed to load chart: {e}")
