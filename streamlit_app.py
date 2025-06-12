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










