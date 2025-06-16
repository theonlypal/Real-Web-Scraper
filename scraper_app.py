import os
import requests
import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim

# File to persist known OSM node IDs
KNOWN_IDS_FILE = "known_osm_ids.csv"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def geocode_location(place: str):
    """Geocode a place or ZIP using Nominatim."""
    geolocator = Nominatim(user_agent="web-scraper-app")
    location = geolocator.geocode(place)
    if location:
        return location.latitude, location.longitude
    return None, None


def query_businesses(lat: float, lon: float, radius_miles: int):
    """Query OSM for business nodes within radius around lat/lon."""
    radius_m = radius_miles * 1609.34  # convert miles to meters
    # search for nodes with a 'shop' or 'amenity' tag and a name
    query = f"""
    [out:json][timeout:25];
    node(around:{radius_m},{lat},{lon})[name][shop];
    node(around:{radius_m},{lat},{lon})[name][amenity];
    out body;
    """
    response = requests.get(OVERPASS_URL, params={"data": query}, headers={"User-Agent": "web-scraper-app"})
    response.raise_for_status()
    data = response.json()
    return data.get("elements", [])


def filter_without_website(nodes):
    """Return nodes without a website tag."""
    return [n for n in nodes if "website" not in n.get("tags", {})]


def load_known_ids():
    """Load previously seen OSM node IDs."""
    if os.path.exists(KNOWN_IDS_FILE):
        df = pd.read_csv(KNOWN_IDS_FILE)
        return set(df["id"].astype(int))
    return set()


def save_known_ids(id_set):
    """Persist the set of known IDs to disk."""
    pd.DataFrame({"id": list(id_set)}).to_csv(KNOWN_IDS_FILE, index=False)


def find_new_nodes(nodes, known_ids):
    """Return nodes whose IDs are not in the known set."""
    new_nodes = [n for n in nodes if n["id"] not in known_ids]
    return new_nodes, {n["id"] for n in new_nodes}


def nodes_to_dataframe(nodes):
    """Convert Overpass nodes to a DataFrame for display."""
    rows = []
    for n in nodes:
        tags = n.get("tags", {})
        rows.append({
            "OSM_ID": n.get("id"),
            "Name": tags.get("name", ""),
            "Type": tags.get("shop") or tags.get("amenity", ""),
            "Website": tags.get("website", ""),
            "Phone": tags.get("phone") or tags.get("contact:phone", ""),
            "Latitude": n.get("lat"),
            "Longitude": n.get("lon"),
        })
    return pd.DataFrame(rows)


def main():
    st.title("Business Finder")

    place = st.text_input("Enter ZIP or place")
    radius = st.selectbox("Radius (miles)", [15, 25, 35], index=0)

    if st.button("Find New Companies"):
        if not place:
            st.warning("Please enter a place to search.")
            return

        with st.spinner("Geocoding location..."):
            lat, lon = geocode_location(place)
        if lat is None:
            st.error("Location not found.")
            return

        with st.spinner("Querying Overpass API..."):
            nodes = query_businesses(lat, lon, radius)
        nodes = filter_without_website(nodes)

        known_ids = load_known_ids()
        new_nodes, new_ids = find_new_nodes(nodes, known_ids)

        df_new = nodes_to_dataframe(new_nodes)
        df_all = nodes_to_dataframe(nodes)

        if not df_new.empty:
            st.success(f"Found {len(df_new)} new companies without websites.")
            st.dataframe(df_new)
        else:
            st.info("No new companies found.")

        if st.checkbox("View Details"):
            st.dataframe(df_all)

        if not df_new.empty:
            csv = df_new.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "new_companies.csv", "text/csv")

        # update known ids with all fetched nodes
        known_ids.update({n["id"] for n in nodes})
        save_known_ids(known_ids)


if __name__ == "__main__":
    main()
