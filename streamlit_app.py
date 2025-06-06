import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import matplotlib.pyplot as plt
from PIL import Image
import matplotlib.gridspec as gridspec

# --- Load Data ---
file_path = r"Z:\PROJECTS\CVAG\Data Analysis\Visualization_Testing_(.py,.xlsx,.xlsb,.word)\NB Washington -Ave 52 to Hwy 111 - Resources\NB Washington - Avenue 52 to Hwy 111 - SPEED - 1hr - 0411-04202025.csv"
df = pd.read_csv(file_path)

# --- Parse datetime ---
if 'Datetime' in df.columns:
    df['Datetime'] = pd.to_datetime(df['Datetime'])
elif 'Time' in df.columns:
    df['Datetime'] = pd.to_datetime(df['Time'])

# --- Clean Strength column ---
df['Strength'] = pd.to_numeric(df['Strength'], errors='coerce')
df = df.dropna(subset=['Strength'])

# --- Resample every 2 hours (only numeric columns) ---
df.set_index('Datetime', inplace=True)
df_2hr = df[['Strength']].resample('2h').mean().reset_index()

# --- Stats ---
mean_strength = df['Strength'].mean()
max_strength = df['Strength'].max()
min_strength = df['Strength'].min()
std_strength = df['Strength'].std()

# --- Plotly Line Chart ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_2hr['Datetime'], y=df_2hr['Strength'], mode='lines+markers', name='Strength'))

# Stats annotation
fig.add_annotation(
    x=df_2hr['Datetime'].iloc[-1], y=mean_strength,
    text=f"<b>Stats (Strength)</b><br>Mean: {mean_strength:.2f}<br>Max: {max_strength:.2f}<br>Min: {min_strength:.2f}<br>Std: {std_strength:.2f}",
    showarrow=False, align='left', bordercolor='gray', borderwidth=1, bgcolor='white', opacity=0.9
)

# Layout
fig.update_layout(
    title="AVG SPEED - NB Washington - Avenue 52 to Hwy 111 - (Strength, Apr 11–20, 2025)",
    xaxis_title="Time (every 2 hrs)",
    yaxis_title="Strength (mph)",
    xaxis=dict(tickformat="%b %d %H:%M", tickangle=45),
    template="plotly_white"
)

# --- Show Logo using matplotlib ---
logo_path = r"Z:\PROJECTS\CVAG\Data Analysis\Logos\ACE-logo-HiRes.jpg"
img = Image.open(logo_path)

fig_logo, axs = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [1, 4]})
axs[0].imshow(img)
axs[0].axis('off')
axs[1].axis('off')
plt.tight_layout()
plt.show()

# Show Plotly Chart
fig.show()




