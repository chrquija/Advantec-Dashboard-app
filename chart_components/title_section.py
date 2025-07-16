import streamlit as st


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


def render_chart_title_section(variable, date_range, direction, data_source):
    """Render the complete chart title section"""
    st.markdown("---")

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

    return chart_type