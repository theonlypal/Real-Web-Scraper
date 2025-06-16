# Real Web Scraper

A simple Streamlit app that finds businesses listed in OpenStreetMap around a given ZIP or place. The app uses the Overpass API and OpenStreetMap geocoding (Nominatim). It highlights businesses that do not have a website listed, displays phone numbers when available, and keeps track of previously seen businesses.

## Setup

```bash
pip install -r requirements.txt
```

## Running

```bash
streamlit run scraper_app.py
```

The first run will create `known_osm_ids.csv` to store seen OSM node IDs.
