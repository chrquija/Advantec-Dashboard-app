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
    """Create an enhanced line chart with day shading and peak/low annotations"""

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
                    fillcolor="lightgray",
                    opacity=0.1,
                    layer="below",
                    line_width=0,
                )
            shade_toggle = not shade_toggle
            current_date += timedelta(days=1)

    # Find top 5 highest and lowest points
    if len(df) >= 5:
        highest_indices = df[y_col].nlargest(5).index
        lowest_indices = df[y_col].nsmallest(5).index

        # Add annotations for highest points (orange with up arrow)
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
                bgcolor="rgba(0,0,0,0.9)",
                bordercolor="orange",
                borderwidth=3,
                font=dict(color="orange", size=14),
                opacity=0.95
            )

        # Add annotations for lowest points (pink with down arrow)
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
                bgcolor="rgba(0,0,0,0.9)",
                bordercolor="hotpink",
                borderwidth=3,
                font=dict(color="hotpink", size=14),
                opacity=0.95
            )

    # Update layout with prominent title
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
        yaxis_title="Vehicle Volume" if "Vehicle Volume" in chart_title else y_col,
        hovermode='x unified',
        showlegend=True,
        plot_bgcolor='white',
        margin=dict(t=80, b=50, l=50, r=50),
        height=500
    )

    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="lightgray",
        showline=True,
        linewidth=1,
        linecolor="black"
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="lightgray",
        showline=True,
        linewidth=1,
        linecolor="black"
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
                    fillcolor="lightgray",
                    opacity=0.1,
                    layer="below",
                    line_width=0,
                )
            shade_toggle = not shade_toggle
            current_date += timedelta(days=1)

    # Add annotations for each line's peaks and lows
    for i, col in enumerate(y_cols):
        if len(df) >= 3:
            highest_indices = df[col].nlargest(3).index
            lowest_indices = df[col].nsmallest(3).index

            # Peaks
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
                    bgcolor="rgba(0,0,0,0.9)",
                    bordercolor=colors[i],
                    borderwidth=2,
                    font=dict(color=colors[i], size=12),
                    opacity=0.9
                )

            # Lows
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
                    bgcolor="rgba(0,0,0,0.9)",
                    bordercolor=colors[i],
                    borderwidth=2,
                    font=dict(color=colors[i], size=12),
                    opacity=0.9
                )

    # Update layout
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
        yaxis_title="Vehicle Volume" if "Vehicle Volume" in chart_title else "Value",
        hovermode='x unified',
        showlegend=True,
        plot_bgcolor='white',
        margin=dict(t=80, b=50, l=50, r=50),
        height=500
    )

    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")

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


def create_heatmap(df, x_col, y_col, values_col, chart_title):
    """Create a heatmap with customizations"""
    pivot_table = df.pivot_table(values=values_col, index=y_col, columns=x_col, aggfunc='mean')

    fig = px.imshow(pivot_table,
                    title=chart_title,
                    labels=dict(x=x_col, y=y_col, color=values_col),
                    color_continuous_scale='Viridis')

    fig.update_layout(
        title=dict(
            text=chart_title,
            x=0.5,
            y=0.95,
            xanchor='center',
            yanchor='top',
            font=dict(size=18, color="darkblue", family="Arial Black")
        ),
        plot_bgcolor='white',
        margin=dict(t=80, b=50, l=50, r=50),
        height=500
    )

    return fig