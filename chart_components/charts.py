import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta, time  # Add 'time' import
import numpy as np


def get_smart_xaxis_title(x_col):
    """Generate intelligent X-axis titles based on column content"""
    col_lower = x_col.lower()

    # Specific mappings for your use case
    if col_lower == "local_datetime":
        return "Date & Time"
    elif col_lower in ["time"]:
        return "Date & Time"

    # Default: Clean up column name by replacing underscores and capitalizing
    else:
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

    # Volume variable mappings
    elif "vehicle volume" in title_lower:
        if ("total_volume" in col_lower or
                col_lower in ["04/10/2025 northbound", "04/10/2025 southbound",
                              "02/13/2025 northbound", "02/13/2025 southbound"]):
            return "Vehicle Volume"

    # Default: Clean up column name by replacing underscores and capitalizing
    return y_col.replace('_', ' ').replace('-', ' ').title()


def is_single_day_data(df, x_col):
    """Check if the data spans only a single day"""
    if df.empty:
        return True

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


def add_time_period_shading(fig, df, x_col, max_y_value):
    """Add time period shading to charts (only for ALL data, not just single day)"""
    if df.empty:
        return

    # Enhanced time period shading with beautiful blue-themed colors
    start_datetime = df[x_col].min()
    end_datetime = df[x_col].max()

    # Define time periods with modern blue-themed palette
    time_periods = [
        {"name": "AM Peak", "start": 5, "end": 10, "color": "#3498DB", "opacity": 0.15},  # Light blue
        {"name": "Midday", "start": 11, "end": 15, "color": "#85C1E9", "opacity": 0.12},  # Lighter blue
        {"name": "PM Peak", "start": 16, "end": 20, "color": "#5DADE2", "opacity": 0.18}  # Medium blue
    ]

    # Iterate through each day in the date range
    current_date = start_datetime.date()
    end_date = end_datetime.date()

    while current_date <= end_date:
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

                # Add elegant period labels ONLY for single day data
                if is_single_day_data(df, x_col) and current_date == start_datetime.date():
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

        current_date += timedelta(days=1)


def create_enhanced_line_chart(df, x_col, y_col, chart_title, color_name="blue"):
    """Create an enhanced single line chart with beautiful blue styling and smart time period handling"""

    # Create the base figure using Graph Objects for more control
    fig = go.Figure()

    # Add the main line trace with enhanced blue styling
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='lines+markers',
        name=color_name.title(),
        line=dict(color='#2E86C1', width=3, shape='spline'),  # Beautiful blue, thicker, smooth
        marker=dict(size=6, color='#1B4F72', line=dict(width=2, color='white'))  # Darker blue with white outline
    ))

    # Add time period shading for ALL data (not just single day)
    if not df.empty:
        add_time_period_shading(fig, df, x_col, df[y_col].max())

    # Enhanced peak/low annotations with blue theme
    if len(df) >= 5:
        highest_indices = df[y_col].nlargest(5).index
        lowest_indices = df[y_col].nsmallest(5).index

        # Enhanced annotations for highest points
        for i, idx in enumerate(highest_indices):
            fig.add_annotation(
                x=df.loc[idx, x_col],
                y=df.loc[idx, y_col],
                text=f" {df.loc[idx, y_col]:.1f}",
                showarrow=True,
                arrowhead=2,
                arrowsize=1.2,
                arrowwidth=2,
                arrowcolor="#1565C0",  # Deep blue
                ax=0,
                ay=-40 - (i * 15),
                bgcolor="rgba(255,255,255,0.95)",
                bordercolor="#1565C0",
                borderwidth=2,
                font=dict(color="#0D47A1", size=11, family="Arial", weight="bold"),
                opacity=0.95
            )

        # Enhanced annotations for lowest points
        for i, idx in enumerate(lowest_indices):
            fig.add_annotation(
                x=df.loc[idx, x_col],
                y=df.loc[idx, y_col],
                text=f" {df.loc[idx, y_col]:.1f}",
                showarrow=True,
                arrowhead=2,
                arrowsize=1.2,
                arrowwidth=2,
                arrowcolor="#42A5F5",  # Lighter blue
                ax=0,
                ay=40 + (i * 15),
                bgcolor="rgba(255,255,255,0.95)",
                bordercolor="#42A5F5",
                borderwidth=2,
                font=dict(color="#1976D2", size=11, family="Arial", weight="bold"),
                opacity=0.95
            )

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
        yaxis_title=get_smart_yaxis_title(y_col, chart_title),  # Smart Y-axis naming!
        hovermode='x unified',
        showlegend=True,
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
    """Create an enhanced multi-line chart for 'Both' direction data with beautiful blue styling"""

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

    # Add time period shading for ALL data (not just single day)
    if not df.empty:
        # Get max value from both columns for positioning
        max_y = max(df[y_cols[0]].max(), df[y_cols[1]].max())
        add_time_period_shading(fig, df, x_col, max_y)

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


