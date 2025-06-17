import streamlit as st
import pandas as pd
import plotly.express as px

# === Sidebar Selections ===
st.sidebar.title("🚦 CVAG Dashboard Filters")

# Step 1: Pick variable type
variable = st.sidebar.selectbox("Select Variable", ["Speed", "Travel Time", "Vehicle Volume"])

# Step 2: Pick direction
direction = st.sidebar.radio("Direction", ["NB", "SB", "Both"])


# Step 3: Pick date range
date_range = st.sidebar.selectbox(
    "Select Date Range",
    ["April 11–20, 2025", "May 9–18, 2025"] if variable != "Vehicle Volume" else ["April 10, 2025", "Feb 13, 2025"]
)

# === Filepath Mapping Logic ===
# Update your base_url to match the actual GitHub structure
base_url = "https://raw.githubusercontent.com/chrquija/Advantec-Dashboard-app/refs/heads/main/hwy111_to_ave52/"
corridor_segment = "Washington St: Highway 111 to Avenue 52"

# And update the specific URL that has the extra space:
path_map = {
    # === SPEED ===
    ("Speed", "NB", "April 11–20, 2025"): base_url + "SPEED/Weeks_04112025_to_04202025/NB_Washington_Avenue_52_to_Hwy_111_SPEED_1hr_0411_04202025.csv",
    ("Speed", "SB", "April 11–20, 2025"): base_url + "SPEED/Weeks_04112025_to_04202025/SB_Washington_Hwy_111_to_Avenue_52_SPEED_1hr_0411_04202025.csv",
    ("Speed", "Both", "April 11–20, 2025"): "BOTH",

    # Fix this URL with the extra space:
    ("Speed", "NB", "May 9–18, 2025"): base_url + "SPEED/Weeks_05092025_to_05182025/NB_Washington_Avenue_52_to_Hwy_111_%20SPEED_1hr_0509_05182025.csv",
    ("Speed", "SB", "May 9–18, 2025"): base_url + "SPEED/Weeks_05092025_to_05182025/SB_Washington_Hwy_111_to_Avenue_52_SPEED_1hr_0509_05182025.csv",
    ("Speed", "Both", "May 9–18, 2025"): "BOTH",
    
    # Continue with your other paths...
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
st.title("📊 Active Transportation & Operations Management Dashboard")
st.write("**Date Range:**", date_range)
st.write("**Corridor Segment:**", corridor_segment)
st.write("**Selected Variable:**", variable)
st.write("**Direction:**", direction)
st.write("**GitHub CSV File Path:**", selected_path)


# === Chart Type Selector ===
chart_type = st.selectbox("Choose chart type", ["Line", "Bar", "Scatter", "Box", "Heatmap"])

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
                
                combined = df[["Northbound", "Southbound"]]
                combined.dropna(inplace=True)

                fig = px.line(combined, y=["Northbound", "Southbound"], 
                             title="Vehicle Volume - Both Directions")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Could not find both direction columns in volume data")
            
        else:
            # FLIR ACYCLICA: Load both NB and SB files separately (existing logic)
            # ... your existing "Both" logic for Speed/Travel Time
            # Load both NB and SB separately using path_map
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

            fig = px.line(combined, y=["NB", "SB"], title=f"{variable} NB & SB Over Time")
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
                # Find column with "Northbound" in the name
                nb_cols = [col for col in df.columns if "northbound" in col.lower()]
                if nb_cols:
                    y_col = nb_cols[0]
                else:
                    st.error("Northbound column not found")
                    st.stop()
            elif direction == "SB":
                # Find column with "Southbound" in the name
                sb_cols = [col for col in df.columns if "southbound" in col.lower()]
                if sb_cols:
                    y_col = sb_cols[0]
                else:
                    st.error("Southbound column not found")
                    st.stop()
        
            df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
            chart_title = f"Vehicle Volume - {direction}"
        
        else:  # This should be properly aligned with the "if variable == 'Vehicle Volume':" above
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
    
        # Remove NaN values after conversion (this should be at the same level as the if/else above)
        df.dropna(subset=[y_col], inplace=True)
    
        # Generate charts
        if not df.empty and y_col in df.columns:
            if chart_type == "Line":
                fig = px.line(df, x=df.index, y=y_col, title=chart_title)
            elif chart_type == "Bar":
                fig = px.bar(df, x=df.index, y=y_col, title=chart_title)
            elif chart_type == "Scatter":
                fig = px.scatter(df, x=df.index, y=y_col, title=chart_title)
            elif chart_type == "Box":
                fig = px.box(df.reset_index(), y=y_col, title=f"{chart_title} Distribution")
            elif chart_type == "Heatmap":
                df['hour'] = df.index.hour
                df['day'] = df.index.date
                pivot = df.pivot_table(values=y_col, index='day', columns='hour')
                fig = px.imshow(pivot, aspect='auto', title=f"{chart_title} Heatmap")

            st.plotly_chart(fig, use_container_width=True)
        
            # Show stats
            st.write(f"**Average {variable}:** {df[y_col].mean():.2f}")
            st.write(f"**Min {variable}:** {df[y_col].min():.2f}")
            st.write(f"**Max {variable}:** {df[y_col].max():.2f}")
        else:
            st.warning(f"No valid data found in {y_col} column.")

except Exception as e:
    st.error(f"❌ Failed to load chart: {e}")
# Update your get_file_path function to handle the corrected URLs
def get_file_path(variable, date_range, direction):
    base_url = "https://raw.githubusercontent.com/chrquija/Advantec-Dashboard-app/refs/heads/main/hwy111_to_ave52"
    
    if variable == "Vehicle Volume":
        if date_range == "April 11-20, 2025":
            return f"{base_url}/VOLUME/Weeks_04112025_to_04202025/volume_hwy111_to_ave52_0410_04202025.csv"
        elif date_range == "May 9-18, 2025":
            return f"{base_url}/VOLUME/Weeks_0509_to_05182025/volume_hwy111_to_ave52_0509_05182025.csv"
    
    elif variable == "Speed":
        if date_range == "April 11-20, 2025":
            nb_url = f"{base_url}/SPEED/Weeks_04112025_to_04202025/NB_Washington_Avenue_52_to_Hwy_111_SPEED_1hr_0411_04202025.csv"
            sb_url = f"{base_url}/SPEED/Weeks_04112025_to_04202025/SB_Washington_Hwy_111_to_Avenue%2052_SPEED_1hr_0411_04202025.csv"
        elif date_range == "May 9-18, 2025":
            nb_url = f"{base_url}/SPEED/Weeks_05092025_to_05182025/NB_Washington_Avenue_52_to_Hwy_111_SPEED_1%20hr_0509_05182025.csv"
            sb_url = f"{base_url}/SPEED/Weeks_05092025_to_05182025/SB_Washington_Hwy_111_to_Avenue_52_SPEED_1_hr_0509_05182025.csv"
        
        return nb_url if direction == "NB" else sb_url
    
    elif variable == "Travel Time":
        if date_range == "April 11-20, 2025":
            nb_url = f"{base_url}/TRAVEL_TIME/Weeks_04112025_to_04202025/NB_Washington_Avenue_52_to_Hwy_111_TRAVEL%20TIME_1hr_0411_04202025.csv"
            sb_url = f"{base_url}/TRAVEL_TIME/Weeks_04112025_to_04202025/SB_Washington_Hwy_111_to_Avenue%2052_TRAVEL%20TIME_1hr_0411_04202025.csv"
        elif date_range == "May 9-18, 2025":
            nb_url = f"{base_url}/TRAVEL_TIME/Weeks_05092025_to_05182025/NB_Washington_Avenue_52_to_Hwy_111_TRAVEL_TIME_1%20hr_0509_05182025.csv"
            sb_url = f"{base_url}/TRAVEL_TIME/Weeks_05092025_to_05182025/SB_Washington_Hwy_111_to_Avenue_52_TRAVEL_TIME_1_hr_0509_05182025.csv"
        
        return nb_url if direction == "NB" else sb_url
    
    return None