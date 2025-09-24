import streamlit as st
import plotly.express as px
from streamlit_folium import st_folium
import folium
import pandas as pd
from src.data_fetch import get_species_tvk, fetch_occurrences_by_tvk
from src.processing import occurrences_to_gdf

# Streamlit page setup
st.set_page_config(layout="wide", page_title="UK Amphibian & Reptile Explorer")

st.sidebar.title("Filters")
species_name = st.sidebar.text_input("Species (common or scientific)", "Smooth newt")
year_from = st.sidebar.number_input("From year", min_value=1600, max_value=2100, value=2000)
page_size = st.sidebar.slider("Page size (API chunk)", 100, 1000, 500, step=100)

if "results" not in st.session_state:
    st.session_state.results = None  # will hold the gdf

# Button triggers fetch
if st.sidebar.button("Fetch & show"):
    with st.spinner("Looking up species..."):
        tvk = get_species_tvk(species_name)

    if not tvk:
        st.error("Species not found on NBN Atlas.")
        st.session_state.results = None
    else:
        st.success(f"Found TVK: {tvk}")
        with st.spinner("Fetching occurrences_to_gdf (this may take a moment)..."):
            try:
                df = fetch_occurrences_by_tvk(tvk, year_from=year_from, page_size=page_size)
            except Exception as e:
                st.error(f"Error fetching data: {e}")
                df = pd.DataFrame()

        if df.empty:
            st.warning("No occurrence records returned.")
            st.session_state.results = None
        else:
            st.session_state.results = occurrences_to_gdf(df)

# Render results if present
if st.session_state.results is not None:
    gdf = st.session_state.results

    st.success(f"Showing results for: {species_name}")

    # Folium map
    m = folium.Map(
        location=[gdf.geometry.y.median(), gdf.geometry.x.median()],
        zoom_start=6
    )
    for _, row in gdf.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=3,
            popup=str(row.get("eventDate", "")),
            fill=True
        ).add_to(m)

    st.write("### Map")
    st_folium(m, width=700, height=500)

    # Trend plot
    gdf["year"] = pd.to_datetime(gdf["eventDate"], errors="coerce").dt.year
    yearly = gdf.groupby("year").size().reset_index(name="counts")
    fig = px.line(yearly, x="year", y="counts", title=f"Records per year - {species_name}")
    st.plotly_chart(fig, use_container_width=True)
