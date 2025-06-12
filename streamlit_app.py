import streamlit as st

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
base_url = "https://raw.githubusercontent.com/chrquija/hwy111_to_ave52/main/"

path_map = {
    # SPEED
    ("Speed", "NB", "April 11–20, 2025"): base_url + "SPEED/Weeks 04112025 to 04202025/NB Washington - Avenue 52 to Hwy 111 - SPEED - 1hr - 0411-04202025.csv",
    ("Speed", "SB", "April 11–20, 2025"): base_url + "SPEED/Weeks 04112025 to 04202025/SB Washington - Hwy 111 to Avenue 52 - SPEED - 1hr - 0411-04202025.csv",
    ("Speed", "NB", "May 9–18, 2025"): base_url + "SPEED/Weeks 05092025 to 05182025/NB Washington - Avenue 52 to Hwy 111 - SPEED - 1hr - 0509 - 05182025.csv",
    ("Speed", "SB", "May 9–18, 2025"): base_url + "SPEED/Weeks 05092025 to 05182025/SB Washington - Hwy 111 to Avenue 52 - SPEED - 1hr - 0509 - 05182025.csv",

    # TRAVEL TIME
    ("Travel Time", "NB", "April 11–20, 2025"): base_url + "TRAVEL TIME/Weeks 04112025 to 04202025/NB Washington - Avenue 52 to Hwy 111 - TRAVEL TIME - 1hr - 0411-04202025(1).csv",
    ("Travel Time", "SB", "April 11–20, 2025"): base_url + "TRAVEL TIME/Weeks 04112025 to 04202025/SB Washington - Hwy 111 to Avenue 52 - TRAVEL TIME - 1hr - 0411-04202025.csv",
    ("Travel Time", "NB", "May 9–18, 2025"): base_url + "TRAVEL TIME/Weeks 05092025 to 05182025/NB Washington - Avenue 52 to Hwy 111 - TRAVEL TIME - 1 hr - 0509-05182025.csv",
    ("Travel Time", "SB", "May 9–18, 2025"): base_url + "TRAVEL TIME/Weeks 05092025 to 05182025/SB Washington - Hwy 111 to Avenue 52 - TRAVEL TIME - 1 hr - 0509 - 05182025.csv",

    # VEHICLE VOLUME
    ("Vehicle Volume", "NB", "April 10, 2025"): base_url + "VOLUME/Thursday april 10/Iteris Wash & Ave 52_NB and SB_VolumeDATA_THURSDAY APRIL10.csv",
    ("Vehicle Volume", "SB", "April 10, 2025"): base_url + "VOLUME/Thursday april 10/Iteris Wash & Ave 52_NB and SB_VolumeDATA_THURSDAY APRIL10.csv",
    ("Vehicle Volume", "NB", "Feb 13, 2025"): base_url + "VOLUME/Thursday feb 13/Iteris Wash & Ave 52_NB and SB_VolumeDATA_Thursday Feb 13.csv",
    ("Vehicle Volume", "SB", "Feb 13, 2025"): base_url + "VOLUME/Thursday feb 13/Iteris Wash & Ave 52_NB and SB_VolumeDATA_Thursday Feb 13.csv"
}

selected_path = path_map.get((variable, direction, date_range), "No path available for selection.")

# === Display the selection and path ===
st.title("📊 CVAG Data Dashboard")
st.write("**Selected Variable:**", variable)
st.write("**Direction:**", direction)
st.write("**Date Range:**", date_range)
st.write("**GitHub CSV File Path:**", selected_path)
### Part 2 of generative Ai help
import pandas as pd
import plotly.express as px

# === Display the selection and path ===
st.title("📊 CVAG Data Dashboard")
st.write("**Selected Variable:**", variable)
st.write("**Direction:**", direction)
st.write("**Date Range:**", date_range)
st.write("**GitHub CSV File Path:**", selected_path)

# === Chart Style Picker ===
chart_type = st.selectbox("Choose chart type", ["Line", "Bar", "Scatter", "Box", "Heatmap"])

# === Load and process the data ===
try:
    df = pd.read_csv(selected_path)

    # Handle datetime parsing
    time_col = "Datetime" if "Datetime" in df.columns else "Time"
    df[time_col] = pd.to_datetime(df[time_col])
    df.set_index(time_col, inplace=True)

    # Auto-select numeric column to plot
    numeric_cols = df.select_dtypes(include='number').columns
    y_col = numeric_cols[0] if len(numeric_cols) > 0 else None

    if y_col:
        # Create chart based on type
        if chart_type == "Line":
            fig = px.line(df, x=df.index, y=y_col, title=f"{y_col} over Time")
        elif chart_type == "Bar":
            fig = px.bar(df, x=df.index, y=y_col, title=f"{y_col} over Time")
        elif chart_type == "Scatter":
            fig = px.scatter(df, x=df.index, y=y_col, title=f"{y_col} over Time")
        elif chart_type == "Box":
            fig = px.box(df.reset_index(), x=df.index.name, y=y_col, title=f"{y_col} Distribution")
        elif chart_type == "Heatmap":
            df_hour = df.copy()
            df_hour['hour'] = df_hour.index.hour
            df_hour['day'] = df_hour.index.date
            pivot = df_hour.pivot_table(values=y_col, index='day', columns='hour')
            fig = px.imshow(pivot, aspect='auto', title=f"{y_col} Heatmap (Hour vs Day)")

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No numeric column found in dataset.")

except Exception as e:
    st.error(f"Error loading file: {e}")









