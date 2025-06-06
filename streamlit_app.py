import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Load CSV
df = pd.read_csv("nb_washington_speed_april11.csv")

# Parse datetime
df['Datetime'] = pd.to_datetime(df['Datetime'])
elif 'Time' in df.columns:
    df['Datetime'] = pd.to_datetime(df['Time'])

# Resample every 2 hours
df.set_index('Datetime', inplace=True)
df_2hr = df[['Strength']].resample('2h').mean().reset_index()

# Plot
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_2hr['Datetime'], 
    y=df_2hr['Strength'],
    mode='lines+markers',
    name='Strength',
    line=dict(color='royalblue')
))

# Show chart only
st.plotly_chart(fig, use_container_width=True)





