import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta, time  # Add 'time' import
import numpy as np


def is_single_day_data(df, x_col):
    """Check if data spans only a single day"""
    if df.empty:
        return False

    start_date = df[x_col].min().date()
    end_date = df[x_col].max().date()
    return start_date == end_date


def get_data_span_days(df, x_col):
    """Get the number of days the data spans"""
    if df.empty:
        return 0

    start_date = df[x_col].min().date()
    end_date = df[x_col].max().date()
    return (end_date - start_date).days + 1


def get_smart_xaxis_title(x_col):
    """Generate intelligent X-axis titles based on column content"""
    col_lower = x_col.lower()

    # Check for common datetime patterns
    if any(term in col_lower for term in ['date', 'time', 'timestamp', 'datetime']):
        return "Date & Time"

    # Check for hour patterns
    if any(term in col_lower for term in ['hour', 'hr']):
        return "Hour"

    # Default: Clean up column name by replacing underscores and capitalizing
    return x_col.replace('_', ' ').replace('-', ' ').title()


def get_smart_yaxis_title(y_col, chart_title):
    """Generate intelligent Y-axis titles based on column content and variable selection"""
    col_lower = y_col.lower()

    # Check what variable is selected based on chart title
    title_lower = chart_title.lower()

    # Travel Time variable mappings
    if "travel time" in title_lower:
        if col_lower == "strength" or "avg_travel_time" in col_lower:
            return "Travel Time (minutes)"

    # Speed variable mappings
    elif "speed" in title_lower:
        if col_lower == "strength" or "avg_speed" in col_lower:
            return "Speed (mph)"

    # Volume variable mappings - Enhanced with better pattern matching
    elif "vehicle volume" in title_lower or "volume" in title_lower:
        # Check for common volume patterns
        if ("total_volume" in col_lower or
                "volume" in col_lower or
                "northbound" in col_lower or
                "southbound" in col_lower or
                # Date-based column patterns (MM/DD/YYYY format)
                any(date_pattern in col_lower for date_pattern in [
                    "04/10/2025", "02/13/2025", "/2024", "/2025", "/2026"
                ]) or
                # Any column that looks like a date with direction
                ("/" in col_lower and ("north" in col_lower or "south" in col_lower))):
            return "Vehicle Volume"

    # Default: Clean up column name by replacing underscores and capitalizing
    return y_col.replace('_', ' ').replace('-', ' ').title()


def add_time_period_shading(fig, df, x_col, max_y_value):
    """Add time period shading ONLY for single day data"""
    if df.empty:
        return

    # Only add time period shading for single day data
    if not is_single_day_data(df, x_col):
        return

    # Enhanced time period shading with beautiful blue-themed colors (SINGLE DAY ONLY)
    start_datetime = df[x_col].min()
    end_datetime = df[x_col].max()

    # Define time periods with modern blue-themed palette
    time_periods = [
        {"name": "AM Peak", "start": 5, "end": 10, "color": "#3498DB", "opacity": 0.15},  # Light blue
        {"name": "Midday", "start": 11, "end": 15, "color": "#85C1E9", "opacity": 0.12},  # Lighter blue
        {"name": "PM Peak", "start": 16, "end": 20, "color": "#5DADE2", "opacity": 0.18}  # Medium blue
    ]

    # Get the date (since it's single day)
    current_date = start_datetime.date()

    for period in time_periods:
        period_start = pd.Timestamp.combine(current_date, time(period["start"], 0))
        period_end = pd.Timestamp.combine(current_date, time(period["end"], 0))

        # Only add shading if the period overlaps with our data range
        if period_start <= end_datetime and period_end >= start_datetime:
            fig.add_vrect(
                x0=max(period_start, start_datetime),
                x1=min(period_end, end_datetime),
                fillcolor=period["color"],
                opacity=period["opacity"],
                layer="below",
                line_width=0,
            )

            # Add elegant period labels
            midpoint = period_start + (period_end - period_start) / 2
            fig.add_annotation(
                x=midpoint,
                y=max_y_value * 0.95,
                text=period["name"],
                showarrow=False,
                font=dict(size=11, color="#1B4F72", family="Arial", weight="bold"),
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor=period["color"],
                borderwidth=2,
            )


def add_alternating_day_shading(fig, df, x_col):
    """Add alternating day shading for multi-day data"""
    if df.empty or is_single_day_data(df, x_col):
        return

    # Get date range
    start_datetime = df[x_col].min()
    end_datetime = df[x_col].max()

    # Colors for alternating days
    day_colors = ["rgba(52, 152, 219, 0.08)", "rgba(155, 186, 227, 0.08)"]  # Very light blue shades

    # Iterate through each day and add alternating shading
    current_date = start_datetime.date()
    end_date = end_datetime.date()
    day_index = 0

    while current_date <= end_date:
        day_start = pd.Timestamp.combine(current_date, time(0, 0))
        day_end = pd.Timestamp.combine(current_date, time(23, 59, 59))

        # Only add shading if the day overlaps with our data range
        if day_start <= end_datetime and day_end >= start_datetime:
            fig.add_vrect(
                x0=max(day_start, start_datetime),
                x1=min(day_end, end_datetime),
                fillcolor=day_colors[day_index % 2],
                opacity=1.0,
                layer="below",
                line_width=0,
            )

        current_date += timedelta(days=1)
        day_index += 1


def create_enhanced_line_chart(df, x_col, y_col, chart_title):
    """Create an enhanced line chart with beautiful blue styling and smart shading"""

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='lines+markers',
        name=y_col,
        line=dict(
            color='#2E86C1',
            width=3,
            shape='spline'
        ),
        marker=dict(
            size=6,
            color='#2E86C1',
            line=dict(width=2, color='white')
        )
    ))

    # Smart shading: Time periods for single day, alternating days for multi-day
    if not df.empty:
        if is_single_day_data(df, x_col):
            # Single day: Add time period shading
            max_y = df[y_col].max()
            add_time_period_shading(fig, df, x_col, max_y)
        else:
            # Multi-day: Add alternating day shading
            add_alternating_day_shading(fig, df, x_col)

    # Enhanced annotations for peaks and lows
    if len(df) >= 3:
        highest_indices = df[y_col].nlargest(3).index
        lowest_indices = df[y_col].nsmallest(3).index

        # Enhanced peaks with improved styling
        for i, idx in enumerate(highest_indices):
            fig.add_annotation(
                x=df.loc[idx, x_col],
                y=df.loc[idx, y_col],
                text=f" {df.loc[idx, y_col]:.1f}",
                showarrow=True,
                arrowhead=2,
                arrowsize=1.2,
                arrowwidth=2,
                arrowcolor='#2E86C1',
                ax=0,
                ay=-35 - (i * 12),
                bgcolor="rgba(255,255,255,0.95)",
                bordercolor='#2E86C1',
                borderwidth=2,
                font=dict(color='#2E86C1', size=10, family="Arial", weight="bold"),
                opacity=0.95
            )

        # Enhanced lows with improved styling
        for i, idx in enumerate(lowest_indices):
            fig.add_annotation(
                x=df.loc[idx, x_col],
                y=df.loc[idx, y_col],
                text=f" {df.loc[idx, y_col]:.1f}",
                showarrow=True,
                arrowhead=2,
                arrowsize=1.2,
                arrowwidth=2,
                arrowcolor='#2E86C1',
                ax=0,
                ay=35 + (i * 12),
                bgcolor="rgba(255,255,255,0.95)",
                bordercolor='#2E86C1',
                borderwidth=2,
                font=dict(color='#2E86C1', size=10, family="Arial", weight="bold"),
                opacity=0.95
            )

    # Get smart axis titles
    smart_yaxis_title = get_smart_yaxis_title(y_col, chart_title)

    # Enhanced layout with beautiful styling and smart axis naming
    fig.update_layout(
        title=dict(
            text=chart_title,
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=20, family="Arial", weight="bold", color="#1B4F72")
        ),
        xaxis_title=get_smart_xaxis_title(x_col),  # Smart X-axis naming!
        yaxis_title=smart_yaxis_title,  # Smart Y-axis naming!
        hovermode='x unified',
        showlegend=False,
        margin=dict(t=80, b=50, l=50, r=50),
        height=520,
        plot_bgcolor='rgba(248,251,255,0.8)',  # Very light blue background
    )

    # Smart X-axis tick configuration based on data span
    data_span = get_data_span_days(df, x_col)

    if data_span == 1:
        # Single day - show every hour (00:00, 01:00, 02:00, etc.)
        fig.update_xaxes(dtick=3600000)  # 1 hour in milliseconds
    elif data_span <= 31:
        # Up to a month - show every day
        fig.update_xaxes(dtick="D1")
    else:
        # More than a month - show every month
        fig.update_xaxes(dtick="M1")

    # Enhanced axes styling
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(52, 152, 219, 0.2)',  # Light blue grid
        showline=True,
        linewidth=2,
        linecolor='#5DADE2',
        title_font=dict(size=14, color="#1B4F72", family="Arial", weight="bold"),
        tickangle=45  # Angle labels for better readability
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(52, 152, 219, 0.2)',  # Light blue grid
        showline=True,
        linewidth=2,
        linecolor='#5DADE2',
        title_font=dict(size=14, color="#1B4F72", family="Arial", weight="bold")
    )

    return fig


def create_enhanced_multi_line_chart(df, x_col, y_cols, chart_title):
    """Create an enhanced multi-line chart for 'Both' direction data with smart shading"""

    fig = go.Figure()

    # Enhanced blue color palette for multiple lines
    colors = ["#2E86C1", "#C0392B"]  # Primary blue and complementary red
    line_styles = ['solid', 'dash']  # Different line styles for distinction

    # Add traces for each direction with enhanced styling
    for i, col in enumerate(y_cols):
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[col],
            mode='lines+markers',
            name=col,
            line=dict(
                color=colors[i],
                width=3,
                shape='spline',
                dash=line_styles[i]
            ),
            marker=dict(
                size=6,
                color=colors[i],
                line=dict(width=2, color='white')
            )
        ))

    # Smart shading: Time periods for single day, alternating days for multi-day
    if not df.empty:
        if is_single_day_data(df, x_col):
            # Single day: Add time period shading
            max_y = max(df[y_cols[0]].max(), df[y_cols[1]].max())
            add_time_period_shading(fig, df, x_col, max_y)
        else:
            # Multi-day: Add alternating day shading
            add_alternating_day_shading(fig, df, x_col)

    # Enhanced annotations for each line's peaks and lows
    for i, col in enumerate(y_cols):
        if len(df) >= 3:
            highest_indices = df[col].nlargest(3).index
            lowest_indices = df[col].nsmallest(3).index

            # Enhanced peaks with improved styling
            for j, idx in enumerate(highest_indices):
                fig.add_annotation(
                    x=df.loc[idx, x_col],
                    y=df.loc[idx, col],
                    text=f" {df.loc[idx, col]:.1f}",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1.2,
                    arrowwidth=2,
                    arrowcolor=colors[i],
                    ax=0,
                    ay=-35 - (j * 12),
                    bgcolor="rgba(255,255,255,0.95)",
                    bordercolor=colors[i],
                    borderwidth=2,
                    font=dict(color=colors[i], size=10, family="Arial", weight="bold"),
                    opacity=0.95
                )

            # Enhanced lows with improved styling
            for j, idx in enumerate(lowest_indices):
                fig.add_annotation(
                    x=df.loc[idx, x_col],
                    y=df.loc[idx, col],
                    text=f" {df.loc[idx, col]:.1f}",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1.2,
                    arrowwidth=2,
                    arrowcolor=colors[i],
                    ax=0,
                    ay=35 + (j * 12),
                    bgcolor="rgba(255,255,255,0.95)",
                    bordercolor=colors[i],
                    borderwidth=2,
                    font=dict(color=colors[i], size=10, family="Arial", weight="bold"),
                    opacity=0.95
                )

    # Determine smart Y-axis title (use first column as representative)
    smart_yaxis_title = get_smart_yaxis_title(y_cols[0], chart_title)

    # Enhanced layout with beautiful styling and smart axis naming
    fig.update_layout(
        title=dict(
            text=chart_title,
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=20, family="Arial", weight="bold", color="#1B4F72")
        ),
        xaxis_title=get_smart_xaxis_title(x_col),  # Smart X-axis naming!
        yaxis_title=smart_yaxis_title,  # Smart Y-axis naming!
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#5DADE2",
            borderwidth=2,
            font=dict(color="#1B4F72", size=12)
        ),
        margin=dict(t=80, b=50, l=50, r=50),
        height=520,
        plot_bgcolor='rgba(248,251,255,0.8)',  # Very light blue background
    )

    # Smart X-axis tick configuration based on data span
    data_span = get_data_span_days(df, x_col)

    if data_span == 1:
        # Single day - show every hour (00:00, 01:00, 02:00, etc.)
        fig.update_xaxes(dtick=3600000)  # 1 hour in milliseconds
    elif data_span <= 31:
        # Up to a month - show every day
        fig.update_xaxes(dtick="D1")
    else:
        # More than a month - show every month
        fig.update_xaxes(dtick="M1")

    # Enhanced axes styling
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(52, 152, 219, 0.2)',  # Light blue grid
        showline=True,
        linewidth=2,
        linecolor='#5DADE2',
        title_font=dict(size=14, color="#1B4F72", family="Arial", weight="bold"),
        tickangle=45  # Angle labels for better readability
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(52, 152, 219, 0.2)',  # Light blue grid
        showline=True,
        linewidth=2,
        linecolor='#5DADE2',
        title_font=dict(size=14, color="#1B4F72", family="Arial", weight="bold")
    )

    return fig


def create_bar_chart(df, x_col, y_col, chart_title, color_name="blue"):
    """Create a bar chart with customizations"""
    fig = px.bar(df, x=x_col, y=y_col, title=chart_title, color_discrete_sequence=[color_name])

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
        plot_bgcolor='white',
        margin=dict(t=80, b=50, l=50, r=50),
        height=500
    )

    return fig


def create_scatter_plot(df, x_col, y_col, chart_title, color_name="blue"):
    """Create a scatter plot with customizations"""
    fig = px.scatter(df, x=x_col, y=y_col, title=chart_title, color_discrete_sequence=[color_name])

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
        plot_bgcolor='white',
        margin=dict(t=80, b=50, l=50, r=50),
        height=500
    )

    return fig


def create_box_plot(df, x_col, y_col, chart_title):
    """Create a box plot with customizations"""
    fig = px.box(df, x=x_col, y=y_col, title=chart_title)

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
        plot_bgcolor='white',
        margin=dict(t=80, b=50, l=50, r=50),
        height=500
    )

    return fig


