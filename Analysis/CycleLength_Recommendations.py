import streamlit as st
import pandas as pd
from chart_components.title_section import find_column
from helpers.reporting import get_hourly_cycle_length, get_existing_cycle_length, filter_by_period


def render_volume_analysis(df, time_period, direction):
    """Render the complete volume analysis section"""
    show_cycle_length = st.toggle("🚦 Get Cycle Length Recommendations", value=False)

    if show_cycle_length:
        render_cycle_length_analysis(df, time_period, direction)
    else:
        render_volume_summary(df)


def render_cycle_length_analysis(df, time_period, direction):
    """Render cycle length analysis section"""
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
                '<span style="color: #51CF66; font-weight: bold;">✅ OPTIMAL</span> - No Changes To Cycle Length Needed',
                unsafe_allow_html=True)
        with col2:
            st.markdown(
                '<span style="color: #FF6B6B; font-weight: bold;">⬇️ REDUCE</span> - Lower Cycle Length Needed',
                unsafe_allow_html=True)
        with col3:
            st.markdown(
                '<span style="color: #4ECDC4; font-weight: bold;">⬆️ INCREASE</span> - Higher Cycle Length Needed',
                unsafe_allow_html=True)
        with col4:
            st.markdown(
                '<span style="color: #FFE66D; font-weight: bold;">⚠️ ADJUST</span> - Cycle Length Needs Reevalation',
                unsafe_allow_html=True)

        # --- Analysis period info ---
        period_info = {
            "AM": "5:00 - 10:00 (6 hours)",
            "MD": "11:00 - 15:00 (5 hours)",
            "PM": "16:00 - 20:00 (5 hours)"
        }
        st.info(
            f"📅 **Analysis Period:** {period_info.get(period_key, 'Full Day')} | **Direction:** {direction}")


def render_volume_summary(df):
    """Render volume summary section"""
    st.subheader("📈 Traffic Volume Summary")

    # Find the correct volume columns using the existing helper function
    nb_vol_col = find_column(df, ['north', 'nb'])
    sb_vol_col = find_column(df, ['south', 'sb'])

    if nb_vol_col and sb_vol_col:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("**🔵 Northbound**", "", "")
            st.write(f"Average: **{df[nb_vol_col].mean():.0f} Vehicles Per Hour**")
            st.write(f"Peak: **{df[nb_vol_col].max():.0f} Vehicles**")
            st.write(f"Low: **{df[nb_vol_col].min():.0f} Vehicles**")
        with col2:
            st.metric("**🔴 Southbound**", "", "")
            st.write(f"Average: **{df[sb_vol_col].mean():.0f} Vehicles Per Hour**")
            st.write(f"Peak: **{df[sb_vol_col].max():.0f} Vehicles**")
            st.write(f"Low: **{df[sb_vol_col].min():.0f} Vehicles**")
        with col3:
            st.metric("**📊 Combined**", "", "")
            total_avg = (df[nb_vol_col].mean() + df[sb_vol_col].mean())
            total_peak = (df[nb_vol_col].max() + df[sb_vol_col].max())
            st.write(f"Total Average: **{total_avg:.0f} Vehicles Per Hour**")
            st.write(f"Total Peak: **{total_peak:.0f} Vehicles**")
            st.write(f"Daily Total: **{df[[nb_vol_col, sb_vol_col]].sum().sum():.0f} Vehicles**")
    else:
        st.warning("⚠️ Could not find Northbound and Southbound volume columns in the data.")
        st.info("Available columns: " + ", ".join(df.columns))

    # Add note about cycle recommendations
    if 'Date' in df.columns and len(df['Date'].unique()) == 1:
        st.info(
            "💡 **Tip:** Click 'Get Cycle Length Recommendations' above to see hourly cycle length analysis for this day.")