import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import time
import os

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & NATURE-INSPIRED THEME STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="The Avian Flyway Atlas",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root {
    --parchment: #FAF6EE;
    --linen: #F2ECE0;
    --forest: #1F3629;
    --moss: #2F6F4E;
    --terracotta: #C86D3B;
    --sky: #3B7A9E;
    --border-sand: #DDD3C0;
}

.stApp {
    background-color: var(--parchment);
    color: var(--forest);
    font-family: 'Plus Jakarta Sans', sans-serif;
}

h1, h2, h3, .serif-title {
    font-family: 'Fraunces', serif !important;
    color: var(--forest) !important;
}

section[data-testid="stSidebar"] {
    background-color: var(--linen);
    border-right: 1px solid var(--border-sand);
}

div[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid var(--border-sand);
    border-radius: 12px;
    padding: 14px 18px;
    box-shadow: 0 2px 8px rgba(31, 54, 41, 0.04);
}

div[data-testid="stMetric"] label {
    color: #546A5D !important;
    font-weight: 600;
}

div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: var(--forest) !important;
    font-family: 'Fraunces', serif;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: var(--linen);
    padding: 6px;
    border-radius: 12px;
    border: 1px solid var(--border-sand);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 18px;
    color: var(--forest);
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background-color: var(--moss) !important;
    color: #FFFFFF !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# DATA LOADING & FALLBACK GENERATOR
# -----------------------------------------------------------------------------
@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    elif os.path.exists("Bird_Migration_Data_with_Origin.csv"):
        df = pd.read_csv("Bird_Migration_Data_with_Origin.csv")
    else:
        # Fallback synthetic dataset matching exact schema if CSV isn't in working directory
        rng = np.random.default_rng(42)
        n = 1000
        species_list = ['Hawk', 'Stork', 'Warbler', 'Goose', 'Eagle', 'Swallow', 'Crane']
        regions = ['South America', 'North America', 'Europe', 'Africa', 'Asia', 'Australia']
        habitats = ['Wetland', 'Grassland', 'Mountain', 'Urban', 'Forest', 'Coastal']
        weathers = ['Clear', 'Foggy', 'Rainy', 'Stormy', 'Windy']
        reasons = ['Feeding', 'Breeding', 'Climate Change', 'Avoid Predators']
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Sep', 'Oct', 'Nov']
        df = pd.DataFrame({
            'Bird_ID': [f'B{1000+i}' for i in range(n)],
            'Species': rng.choice(species_list, n),
            'Region': rng.choice(regions, n),
            'Habitat': rng.choice(habitats, n),
            'Weather_Condition': rng.choice(weathers, n),
            'Migration_Reason': rng.choice(reasons, n),
            'Start_Latitude': rng.uniform(-75, 75, n),
            'Start_Longitude': rng.uniform(-170, 170, n),
            'End_Latitude': rng.uniform(-75, 75, n),
            'End_Longitude': rng.uniform(-170, 170, n),
            'Flight_Distance_km': rng.normal(2500, 500, n).clip(500, 4500),
            'Flight_Duration_hours': rng.normal(50, 10, n).clip(12, 95),
            'Average_Speed_kmph': rng.normal(50, 5, n).clip(30, 70),
            'Max_Altitude_m': rng.integers(1000, 10000, n),
            'Temperature_C': rng.uniform(-10, 35, n),
            'Wind_Speed_kmph': rng.uniform(0, 60, n),
            'Migration_Start_Month': rng.choice(months, n),
            'Flock_Size': rng.integers(1, 500, n),
            'Rest_Stops': rng.integers(1, 15, n),
            'Interrupted_Reason': rng.choice(['Storm', 'Injury', 'Predator', 'Lost Signal', None], n),
            'Migration_Success': rng.choice(['Successful', 'Failed'], n, p=[0.51, 0.49])
        })
    return df

# -----------------------------------------------------------------------------
# HEADER & SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
st.markdown("# 🌿 The Avian Flyway Atlas")
st.caption("An Audubon-inspired ornithological field guide & interactive migration telemetry explorer")

with st.sidebar:
    st.markdown("### 📂 Field Dataset")
    uploaded = st.file_uploader("Upload Bird_Migration_Data_with_Origin.csv", type=["csv"])
    df = load_data(uploaded)
    st.success(f"Loaded **{len(df):,}** telemetry tracks across **{df['Species'].nunique()}** species.")

    st.markdown("---")
    st.markdown("### 🪶 Global Atlas Filters")
    selected_regions = st.multiselect(
        "Flyway Regions",
        options=sorted(df['Region'].unique()),
        default=sorted(df['Region'].unique())
    )
    selected_weather = st.multiselect(
        "Weather Conditions",
        options=sorted(df['Weather_Condition'].unique()),
        default=sorted(df['Weather_Condition'].unique())
    )

filtered_df = df[
    (df['Region'].isin(selected_regions)) &
    (df['Weather_Condition'].isin(selected_weather))
].copy()

if filtered_df.empty:
    st.warning("No migration records match your current sidebar filters. Please select at least one Region and Weather condition.")
    st.stop()

# Top KPI Row
k1, k2, k3, k4 = st.columns(4)
success_pct = (filtered_df['Migration_Success'] == 'Successful').mean() * 100
k1.metric("Tracked Journeys", f"{len(filtered_df):,}")
k2.metric("Flyway Survival Rate", f"{success_pct:.1f}%")
k3.metric("Mean Flight Distance", f"{filtered_df['Flight_Distance_km'].mean():,.0f} km")
k4.metric("Mean Cruising Altitude", f"{filtered_df['Max_Altitude_m'].mean():,.0f} m")

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# MAIN TABS
# -----------------------------------------------------------------------------
tab_studio, tab_map, tab_ledger = st.tabs([
    "🕊️ Species Flight Studio (Animated)",
    "🗺️ Cartographic Flyway Map",
    "📒 Field Guide & Ecological Ledger"
])

# =============================================================================
# TAB 1: SPECIES FLIGHT STUDIO (TOP 10 SPECIES + ANIMATED BIRD ON LINE GRAPH)
# =============================================================================
with tab_studio:
    st.markdown("### Species Flight Studio")
    st.write("Select one of the **Top 10 Most Observed Species** and choose your X and Y flight axes to watch the bird soar across its telemetry profile.")

    # Rank Top 10 most common species
    top_10_counts = filtered_df['Species'].value_counts().head(10)
    top_10_species = top_10_counts.index.tolist()

    species_icons = {
        'Hawk': '🦅', 'Eagle': '🦅', 'Stork': '🦩', 'Crane': '🦢',
        'Goose': '🦆', 'Swallow': '🕊️', 'Warbler': '🐦'
    }

    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1.2, 1.2, 1.2])
    with col_ctrl1:
        selected_species = st.selectbox(
            "1. Select Species (Top 10 Ranked)",
            options=top_10_species,
            format_func=lambda s: f"#{top_10_species.index(s)+1} {species_icons.get(s, '🐦')} {s} ({top_10_counts[s]:,} tracks)"
        )

    x_axis_options = {
        "Migration Month": "Migration_Start_Month",
        "Flight Distance Bracket": "Distance_Bracket",
        "Wind Speed Band": "Wind_Bracket",
        "Ambient Temperature Band": "Temp_Bracket"
    }
    y_axis_options = {
        "Cruising Altitude (m)": ("Max_Altitude_m", "mean", "m"),
        "Average Airspeed (km/h)": ("Average_Speed_kmph", "mean", "km/h"),
        "Flight Distance (km)": ("Flight_Distance_km", "mean", "km"),
        "Survival Rate (%)": ("Success_Num", "mean", "%"),
        "Average Flock Size (birds)": ("Flock_Size", "mean", "birds")
    }

    with col_ctrl2:
        x_label = st.selectbox("2. Horizontal Axis (X)", list(x_axis_options.keys()), index=0)
    with col_ctrl3:
        y_label = st.selectbox("3. Vertical Axis (Y)", list(y_axis_options.keys()), index=0)

    # Prepare binned columns for X-axis grouping
    work_df = filtered_df.copy()
    work_df['Success_Num'] = (work_df['Migration_Success'] == 'Successful').astype(float) * 100.0

    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    work_df['Distance_Bracket'] = pd.cut(
        work_df['Flight_Distance_km'],
        bins=[0, 1500, 2000, 2400, 2800, 3200, 5000],
        labels=['<1,500 km', '1.5k–2.0k km', '2.0k–2.4k km', '2.4k–2.8k km', '2.8k–3.2k km', '3,200+ km']
    )
    work_df['Wind_Bracket'] = pd.cut(
        work_df['Wind_Speed_kmph'],
        bins=[-1, 10, 20, 30, 40, 50, 70],
        labels=['0–10 km/h', '10–20 km/h', '20–30 km/h', '30–40 km/h', '40–50 km/h', '50+ km/h']
    )
    work_df['Temp_Bracket'] = pd.cut(
        work_df['Temperature_C'],
        bins=[-20, -2, 6, 14, 22, 29, 45],
        labels=['< -2°C', '-2° to 6°C', '6° to 14°C', '14° to 22°C', '22° to 29°C', '29°C+']
    )

    x_col = x_axis_options[x_label]
    y_col, _, y_unit = y_axis_options[y_label]

    sp_df = work_df[work_df['Species'] == selected_species]

    if x_col == "Migration_Start_Month":
        present_months = [m for m in month_order if m in sp_df[x_col].unique()]
        sp_grouped = sp_df.groupby(x_col, observed=False)[y_col].mean().reindex(present_months).dropna().reset_index()
        all_grouped = work_df.groupby(x_col, observed=False)[y_col].mean().reindex(present_months).dropna().reset_index()
    else:
        sp_grouped = sp_df.groupby(x_col, observed=False)[y_col].mean().dropna().reset_index()
        all_grouped = work_df.groupby(x_col, observed=False)[y_col].mean().dropna().reset_index()

    sp_grouped.columns = ['X', 'Y']
    all_grouped.columns = ['X', 'Y']

    # Animation & Baseline Controls
    c_anim1, c_anim2, c_anim3 = st.columns([1, 1, 2])
    with c_anim1:
        show_baseline = st.checkbox("Show All-Species Baseline", value=True)
    with c_anim2:
        animate_now = st.button("▶️ Animate Bird Flight", use_container_width=True)
    with c_anim3:
        point_idx = st.slider(
            "Or Scrub Flight Waypoint Manually",
            min_value=0,
            max_value=max(0, len(sp_grouped) - 1),
            value=len(sp_grouped) - 1
        )

    bird_emoji = species_icons.get(selected_species, '🐦')

    def build_flight_figure(active_idx):
        fig = go.Figure()

        # All-species baseline curve
        if show_baseline and not all_grouped.empty:
            fig.add_trace(go.Scatter(
                x=all_grouped['X'].astype(str),
                y=all_grouped['Y'],
                mode='lines+markers',
                name='All Species Baseline',
                line=dict(color='#9AA89E', width=2, dash='dash'),
                marker=dict(size=6, color='#9AA89E')
            ))

        # Full planned trajectory (faint guide)
        fig.add_trace(go.Scatter(
            x=sp_grouped['X'].astype(str),
            y=sp_grouped['Y'],
            mode='lines',
            name=f'{selected_species} Projected Path',
            line=dict(color='rgba(47, 111, 78, 0.25)', width=3, shape='spline')
        ))

        # Flown trajectory up to active_idx
        flown = sp_grouped.iloc[:active_idx + 1]
        fig.add_trace(go.Scatter(
            x=flown['X'].astype(str),
            y=flown['Y'],
            mode='lines+markers',
            name=f'{selected_species} Flown Trajectory',
            fill='tozeroy',
            fillcolor='rgba(47, 111, 78, 0.12)',
            line=dict(color='#2F6F4E', width=4, shape='spline'),
            marker=dict(size=9, color='#C86D3B', line=dict(width=2, color='#FFFFFF'))
        ))

        # Animated Bird Icon at current waypoint
        curr = sp_grouped.iloc[active_idx]
        y_span = max(1.0, sp_grouped['Y'].max() - sp_grouped['Y'].min())
        fig.add_trace(go.Scatter(
            x=[str(curr['X'])],
            y=[curr['Y']],
            mode='text+markers',
            name=f'Active {selected_species}',
            text=[f"  {bird_emoji} {curr['Y']:.1f} {y_unit}"],
            textposition='top center',
            textfont=dict(size=16, color='#1F3629', family='Fraunces'),
            marker=dict(size=20, color='rgba(200, 109, 59, 0.25)', line=dict(width=2, color='#C86D3B'))
        ))

        y_min = min(sp_grouped['Y'].min(), all_grouped['Y'].min() if show_baseline else sp_grouped['Y'].min())
        y_max = max(sp_grouped['Y'].max(), all_grouped['Y'].max() if show_baseline else sp_grouped['Y'].max())
        pad = max(1.0, (y_max - y_min) * 0.22)

        fig.update_layout(
            title=dict(
                text=f"{bird_emoji} {selected_species} Migration Curve — {y_label} vs. {x_label}",
                font=dict(family='Fraunces', size=20, color='#1F3629')
            ),
            xaxis=dict(title=x_label, showgrid=True, gridcolor='#E6DEC8', linecolor='#C5B9A3'),
            yaxis=dict(
                title=y_label,
                range=[max(0, y_min - pad), y_max + pad],
                showgrid=True,
                gridcolor='#E6DEC8',
                linecolor='#C5B9A3'
            ),
            plot_bgcolor='#FAF6EE',
            paper_bgcolor='#FFFFFF',
            hovermode='x unified',
            height=460,
            margin=dict(l=40, r=40, t=70, b=50),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        return fig

    chart_placeholder = st.empty()

    if animate_now and len(sp_grouped) > 1:
        # Smooth multi-step interpolation frames for fluid flying animation
        for idx in range(len(sp_grouped)):
            chart_placeholder.plotly_chart(build_flight_figure(idx), use_container_width=True)
            time.sleep(0.35)
    else:
        chart_placeholder.plotly_chart(build_flight_figure(point_idx), use_container_width=True)

# =============================================================================
# TAB 2: CARTOGRAPHIC FLYWAY MAP
# =============================================================================
with tab_map:
    st.markdown("### Global Flyway Corridors")
    st.write("Displaying sampled great-circle migration paths colored by journey outcome.")

    map_species = st.selectbox("Filter Map by Species", ["All Species"] + top_10_species, key="map_sp")
    map_df = filtered_df if map_species == "All Species" else filtered_df[filtered_df['Species'] == map_species]
    sample_map = map_df.sample(min(120, len(map_df)), random_state=42)

    fig_map = go.Figure()

    for _, row in sample_map.iterrows():
        is_ok = row['Migration_Success'] == 'Successful'
        line_color = 'rgba(47, 111, 78, 0.45)' if is_ok else 'rgba(200, 109, 59, 0.45)'
        fig_map.add_trace(go.Scattergeo(
            lon=[row['Start_Longitude'], row['End_Longitude']],
            lat=[row['Start_Latitude'], row['End_Latitude']],
            mode='lines',
            line=dict(width=1.4, color=line_color),
            hoverinfo='text',
            text=(
                f"<b>{row['Bird_ID']} ({row['Species']})</b><br>"
                f"Region: {row['Region']} ({row['Habitat']})<br>"
                f"Distance: {row['Flight_Distance_km']:.0f} km | Alt: {row['Max_Altitude_m']:,} m<br>"
                f"Outcome: {row['Migration_Success']}"
            ),
            showlegend=False
        ))

    # Endpoint markers
    fig_map.add_trace(go.Scattergeo(
        lon=sample_map['End_Longitude'],
        lat=sample_map['End_Latitude'],
        mode='markers',
        marker=dict(
            size=6,
            color=['#2F6F4E' if s == 'Successful' else '#C86D3B' for s in sample_map['Migration_Success']],
            line=dict(width=1, color='#FFFFFF')
        ),
        name='Arrival / Recovery Coordinates',
        hoverinfo='skip'
    ))

    fig_map.update_geos(
        projection_type="natural earth",
        showland=True,
        landcolor="#EFE8D8",
        showocean=True,
        oceancolor="#DCE8EC",
        showcountries=True,
        countrycolor="#C8BEA9",
        showcoastlines=True,
        coastlinecolor="#A99E88",
        bgcolor="#FAF6EE"
    )
    fig_map.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=20, b=0),
        paper_bgcolor="#FAF6EE"
    )
    st.plotly_chart(fig_map, use_container_width=True)

# =============================================================================
# TAB 3: FIELD GUIDE & ECOLOGICAL LEDGER
# =============================================================================
with tab_ledger:
    st.markdown("### Species & Interruption Breakdown")
    c_left, c_right = st.columns(2)

    with c_left:
        sp_summary = filtered_df.groupby('Species').agg(
            Count=('Bird_ID', 'count'),
            Survival_Rate=('Migration_Success', lambda x: (x == 'Successful').mean() * 100),
            Avg_Distance=('Flight_Distance_km', 'mean')
        ).reset_index().sort_values('Count', ascending=False)

        fig_bar = px.bar(
            sp_summary,
            x='Species',
            y='Survival_Rate',
            color='Species',
            text=sp_summary['Survival_Rate'].map(lambda v: f"{v:.1f}%"),
            color_discrete_sequence=['#2F6F4E', '#3B7A9E', '#C86D3B', '#6A8D73', '#D49A6A', '#4A6B82', '#8C6239'],
            title="Migration Survival Rate by Species"
        )
        fig_bar.update_layout(
            plot_bgcolor='#FAF6EE',
            paper_bgcolor='#FFFFFF',
            showlegend=False,
            yaxis_title="Survival Rate (%)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with c_right:
        int_counts = filtered_df['Interrupted_Reason'].fillna('Uninterrupted').value_counts().reset_index()
        int_counts.columns = ['Cause', 'Records']
        fig_pie = px.pie(
            int_counts,
            names='Cause',
            values='Records',
            hole=0.45,
            color_discrete_sequence=['#C86D3B', '#3B7A9E', '#2F6F4E', '#D4A359', '#7D8F85'],
            title="Recorded Flight Interruption Causes"
        )
        fig_pie.update_layout(paper_bgcolor='#FFFFFF')
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("### Raw Field Telemetry Ledger")
    st.dataframe(
        filtered_df[[
            'Bird_ID', 'Species', 'Region', 'Habitat', 'Weather_Condition',
            'Flight_Distance_km', 'Max_Altitude_m', 'Average_Speed_kmph',
            'Migration_Start_Month', 'Interrupted_Reason', 'Migration_Success'
        ]].head(250),
        use_container_width=True
    )
