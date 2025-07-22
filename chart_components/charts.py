import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta, time  # Add 'time' import
import numpy as np


def get_units(variable):
    """Get the units for a given variable"""
    if variable == "Vehicle Volume":
        return "vehicles"
    elif variable == "Speed":
        return "mph"
    elif variable == "Travel Time":
        return "seconds"
    else:
        return ""


def format_value_with_units(value, variable):
    """Format value with appropriate units"""
    unit = get_units(variable)
    if unit:
        return f"{value:.1f} {unit}"
    return f"{value:.1f}"


def create_enhanced_line_chart(df, x_col, y_col, chart_title, color_name="blue"):
    """Create an enhanced single line chart with beautiful blue styling and time period shading"""

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

    # Add alternating day shading with subtle blue tones
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
                    fillcolor="#E8F6F3",  # Very light blue-green
                    opacity=0.3,
                    layer="below",
                    line_width=0,
                )
            shade_toggle = not shade_toggle
            current_date += timedelta(days=1)

        # Enhanced time period shading with beautiful blue-themed colors
        start_datetime = df[x_col].min()
        end_datetime = df[x_col].max()

        # Define time periods with modern blue-themed palette
        time_periods = [
            {"name": "AM (5:00 - 10:00)", "start": 5, "end": 10, "color": "#3498DB", "opacity": 0.15},  # Light blue
            {"name": "MD (11:00 - 15:00)", "start": 11, "end": 15, "color": "#85C1E9", "opacity": 0.12},  # Lighter blue
            {"name": "PM (16:00 - 20:00)", "start": 16, "end": 20, "color": "#5DADE2", "opacity": 0.18}  # Medium blue
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

                    # Add elegant period labels (removed borderrad - not supported)
                    if current_date == start_datetime.date():
                        midpoint = period_start + (period_end - period_start) / 2
                        fig.add_annotation(
                            x=midpoint,
                            y=df[y_col].max() * 0.95,
                            text=period["name"],
                            showarrow=False,
                            font=dict(size=11, color="#1B4F72", family="Arial", weight="bold"),
                            bgcolor="rgba(255,255,255,0.9)",
                            bordercolor=period["color"],
                            borderwidth=2,
                        )

            current_date += timedelta(days=1)

    # Enhanced peak/low annotations with blue theme
    if len(df) >= 5:
        highest_indices = df[y_col].nlargest(5).index
        lowest_indices = df[y_col].nsmallest(5).index

        # Enhanced annotations for highest points (removed borderrad)
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

        # Enhanced annotations for lowest points (removed borderrad)
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

    # Enhanced layout with beautiful styling
    fig.update_layout(
        title=dict(
            text=chart_title,
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=20, family="Arial", weight="bold", color="#1B4F72")
        ),
        xaxis_title="Time",
        yaxis_title="Vehicle Volume" if "Vehicle Volume" in chart_title else y_col,
        hovermode='x unified',
        showlegend=True,
        margin=dict(t=80, b=50, l=50, r=50),
        height=520,
        plot_bgcolor='rgba(248,251,255,0.8)',  # Very light blue background
    )

    # Enhanced axes styling
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(52, 152, 219, 0.2)',  # Light blue grid
        showline=True,
        linewidth=2,
        linecolor='#5DADE2',
        title_font=dict(size=14, color="#1B4F72", family="Arial", weight="bold")
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

    # Add alternating day shading with subtle blue tones
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
                    fillcolor="#E8F6F3",  # Very light blue-green
                    opacity=0.25,
                    layer="below",
                    line_width=0,
                )
            shade_toggle = not shade_toggle
            current_date += timedelta(days=1)

        # Enhanced time period shading with beautiful blue-themed colors
        start_datetime = df[x_col].min()
        end_datetime = df[x_col].max()

        # Define time periods with modern blue-themed palette
        time_periods = [
            {"name": "AM (5:00-10:00)", "start": 5, "end": 10, "color": "#3498DB", "opacity": 0.15},  # Light blue
            {"name": "MD (11:00-15:00)", "start": 11, "end": 15, "color": "#85C1E9", "opacity": 0.12},  # Lighter blue
            {"name": "PM (16:00-20:00)", "start": 16, "end": 20, "color": "#5DADE2", "opacity": 0.18}  # Medium blue
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

                    # Add elegant period labels (removed borderrad)
                    if current_date == start_datetime.date():
                        # Get max value from both columns for positioning
                        max_y = max(df[y_cols[0]].max(), df[y_cols[1]].max())
                        midpoint = period_start + (period_end - period_start) / 2
                        fig.add_annotation(
                            x=midpoint,
                            y=max_y * 0.95,
                            text=period["name"],
                            showarrow=False,
                            font=dict(size=11, color="#1B4F72", family="Arial", weight="bold"),
                            bgcolor="rgba(255,255,255,0.9)",
                            bordercolor=period["color"],
                            borderwidth=2,
                        )

            current_date += timedelta(days=1)

    # Enhanced annotations for each line's peaks and lows
    for i, col in enumerate(y_cols):
        if len(df) >= 3:
            highest_indices = df[col].nlargest(3).index
            lowest_indices = df[col].nsmallest(3).index

            # Enhanced peaks with improved styling (removed borderrad)
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

            # Enhanced lows with improved styling (removed borderrad)
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

    # Enhanced layout with beautiful styling
    fig.update_layout(
        title=dict(
            text=chart_title,
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=20, family="Arial", weight="bold", color="#1B4F72")
        ),
        xaxis_title="Time",
        yaxis_title="Vehicle Volume" if "Vehicle Volume" in chart_title else "Value",
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

    # Enhanced axes styling
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(52, 152, 219, 0.2)',  # Light blue grid
        showline=True,
        linewidth=2,
        linecolor='#5DADE2',
        title_font=dict(size=14, color="#1B4F72", family="Arial", weight="bold")
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


