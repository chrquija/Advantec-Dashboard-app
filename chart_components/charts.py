import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
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
    """Create an enhanced line chart with day shading, time period shading, and peak/low annotations"""

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
        start_date = df[x_col].min().date()
        end_date = df[x_col].max().date()

        current_date = start_date
        shade_toggle = True

        while current_date <= end_date:
            if shade_toggle:
                fig.add_vrect(
                    x0=current_date,
                    x1=current_date + timedelta(days=1),
                    fillcolor="gray",
                    opacity=0.08,
                    layer="below",
                    line_width=0,
                )
            shade_toggle = not shade_toggle
            current_date += timedelta(days=1)

        # Add time period shading for single days worth of data
        start_datetime = df[x_col].min()
        end_datetime = df[x_col].max()

        # Define time periods: AM (5:00-10:00), MD (11:00-15:00), PM (16:00-20:00)
        time_periods = [
            {"name": "AM", "start": 5, "end": 10, "color": "orange", "opacity": 0.12},
            {"name": "MD", "start": 11, "end": 15, "color": "green", "opacity": 0.08},
            {"name": "PM", "start": 16, "end": 20, "color": "red", "opacity": 0.12}
        ]

        # Iterate through each day in the date range
        current_date = start_datetime.date()
        end_date = end_datetime.date()

        while current_date <= end_date:
            for period in time_periods:
                period_start = pd.Timestamp.combine(current_date, pd.Time(period["start"], 0))
                period_end = pd.Timestamp.combine(current_date, pd.Time(period["end"], 0))

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

                    # Add period label only on the first day
                    if current_date == start_datetime.date():
                        midpoint = period_start + (period_end - period_start) / 2
                        fig.add_annotation(
                            x=midpoint,
                            y=df[y_col].max() * 0.95,
                            text=period["name"],
                            showarrow=False,
                            font=dict(size=10, color=period["color"]),
                            bgcolor="rgba(255,255,255,0.8)",
                            bordercolor=period["color"],
                            borderwidth=1,
                        )

            current_date += timedelta(days=1)

    # Find top 5 highest and lowest points
    if len(df) >= 5:
        highest_indices = df[y_col].nlargest(5).index
        lowest_indices = df[y_col].nsmallest(5).index

        # Add annotations for highest points with improved contrast
        for i, idx in enumerate(highest_indices):
            fig.add_annotation(
                x=df.loc[idx, x_col],
                y=df.loc[idx, y_col],
                text=f"▲ {df.loc[idx, y_col]:.2f}",
                showarrow=True,
                arrowhead=3,
                arrowsize=1.5,
                arrowwidth=3,
                arrowcolor="orange",
                ax=0,
                ay=-35 - (i * 12),
                bgcolor="rgba(255,255,255,0.95)",
                bordercolor="orange",
                borderwidth=2,
                font=dict(color="darkorange", size=12, family="Arial Black"),
                opacity=0.95
            )

        # Add annotations for lowest points with improved contrast
        for i, idx in enumerate(lowest_indices):
            fig.add_annotation(
                x=df.loc[idx, x_col],
                y=df.loc[idx, y_col],
                text=f"▼ {df.loc[idx, y_col]:.2f}",
                showarrow=True,
                arrowhead=3,
                arrowsize=1.5,
                arrowwidth=3,
                arrowcolor="hotpink",
                ax=0,
                ay=35 + (i * 12),
                bgcolor="rgba(255,255,255,0.95)",
                bordercolor="hotpink",
                borderwidth=2,
                font=dict(color="mediumvioletred", size=12, family="Arial Black"),
                opacity=0.95
            )

    # Update layout - removed hardcoded colors for theme responsiveness
    fig.update_layout(
        title=dict(
            text=chart_title,
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=18, family="Arial Black")
        ),
        xaxis_title="Time",
        yaxis_title="Vehicle Volume" if "Vehicle Volume" in chart_title else y_col,
        hovermode='x unified',
        showlegend=True,
        margin=dict(t=80, b=50, l=50, r=50),
        height=500
    )

    # Update axes - removed hardcoded colors for theme responsiveness
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        showline=True,
        linewidth=1,
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        showline=True,
        linewidth=1,
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
                    fillcolor="gray",
                    opacity=0.08,
                    layer="below",
                    line_width=0,
                )
            shade_toggle = not shade_toggle
            current_date += timedelta(days=1)

        # Add time period shading for single days worth of data
        start_datetime = df[x_col].min()
        end_datetime = df[x_col].max()

        # Define time periods: AM (5:00-10:00), MD (11:00-15:00), PM (16:00-20:00)
        time_periods = [
            {"name": "AM", "start": 5, "end": 10, "color": "orange", "opacity": 0.12},
            {"name": "MD", "start": 11, "end": 15, "color": "green", "opacity": 0.08},
            {"name": "PM", "start": 16, "end": 20, "color": "red", "opacity": 0.12}
        ]

        # Iterate through each day in the date range
        current_date = start_datetime.date()
        end_date = end_datetime.date()

        while current_date <= end_date:
            for period in time_periods:
                period_start = pd.Timestamp.combine(current_date, pd.Time(period["start"], 0))
                period_end = pd.Timestamp.combine(current_date, pd.Time(period["end"], 0))

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

                    # Add period label only on the first day
                    if current_date == start_datetime.date():
                        # Get max value from both columns for positioning
                        max_y = max(df[y_cols[0]].max(), df[y_cols[1]].max())
                        midpoint = period_start + (period_end - period_start) / 2
                        fig.add_annotation(
                            x=midpoint,
                            y=max_y * 0.95,
                            text=period["name"],
                            showarrow=False,
                            font=dict(size=10, color=period["color"]),
                            bgcolor="rgba(255,255,255,0.8)",
                            bordercolor=period["color"],
                            borderwidth=1,
                        )

            current_date += timedelta(days=1)

    # Add annotations for each line's peaks and lows with improved contrast
    for i, col in enumerate(y_cols):
        if len(df) >= 3:
            highest_indices = df[col].nlargest(3).index
            lowest_indices = df[col].nsmallest(3).index

            # Peaks with improved contrast
            for j, idx in enumerate(highest_indices):
                fig.add_annotation(
                    x=df.loc[idx, x_col],
                    y=df.loc[idx, col],
                    text=f"▲ {df.loc[idx, col]:.2f}",
                    showarrow=True,
                    arrowhead=3,
                    arrowsize=1.3,
                    arrowwidth=2.5,
                    arrowcolor=colors[i],
                    ax=0,
                    ay=-30 - (j * 10),
                    bgcolor="rgba(255,255,255,0.95)",
                    bordercolor=colors[i],
                    borderwidth=2,
                    font=dict(color=colors[i], size=11, family="Arial Black"),
                    opacity=0.95
                )

            # Lows with improved contrast
            for j, idx in enumerate(lowest_indices):
                fig.add_annotation(
                    x=df.loc[idx, x_col],
                    y=df.loc[idx, col],
                    text=f"▼ {df.loc[idx, col]:.2f}",
                    showarrow=True,
                    arrowhead=3,
                    arrowsize=1.3,
                    arrowwidth=2.5,
                    arrowcolor=colors[i],
                    ax=0,
                    ay=30 + (j * 10),
                    bgcolor="rgba(255,255,255,0.95)",
                    bordercolor=colors[i],
                    borderwidth=2,
                    font=dict(color=colors[i], size=11, family="Arial Black"),
                    opacity=0.95
                )

    # Update layout - removed hardcoded colors for theme responsiveness
    fig.update_layout(
        title=dict(
            text=chart_title,
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=18, family="Arial Black")
        ),
        xaxis_title="Time",
        yaxis_title="Vehicle Volume" if "Vehicle Volume" in chart_title else "Value",
        hovermode='x unified',
        showlegend=True,
        margin=dict(t=80, b=50, l=50, r=50),
        height=500
    )

    # Update axes - removed hardcoded colors for theme responsiveness
    fig.update_xaxes(showgrid=True, gridwidth=1)
    fig.update_yaxes(showgrid=True, gridwidth=1)

    # Store chart in session state
    st.session_state['current_chart'] = fig

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


