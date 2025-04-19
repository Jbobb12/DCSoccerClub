import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
from datetime import datetime

def get_lat_lon(address):
    geolocator = Nominatim(user_agent="http")
    try:
        location = geolocator.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude
        return None, None
    except GeocoderTimedOut:
        return None, None

def clean_uploaded_csv(df, program_name):
    required_columns = ["address", "city", "state", "zip", "birth_date", "Race"]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    try:
        # Address
        df["Address"] = df["address"].astype(str).str.strip() + ", " + df["city"].astype(str).str.strip() + ", " + df["state"].astype(str).str.strip()

        # Rename zip to Zip Code
        df.rename(columns={"zip": "Zip Code"}, inplace=True)

        # Age        
        df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
        today = datetime.today()
        df["Age"] = df["birth_date"].apply(
            lambda d: today.year - d.year - ((today.month, today.day) < (d.month, d.day)) if pd.notnull(d) else None
        )

        df["birth_date"] = df["birth_date"].dt.strftime("%Y-%m-%d")
        
        # Race List
        df["Race List"] = df["Race"].astype(str).apply(
            lambda x: [race.strip().lower() for race in x.split(",") if race.strip()] if pd.notnull(x) else []
        )

        df.drop(columns=["address", "city", "state", "Race"], inplace=True, errors="ignore")

        # Latitude and Longitude from Address
        latitudes = []
        longitudes = []
        for addr in df["Address"]:
            lat, lon = get_lat_lon(addr)
            latitudes.append(lat)
            longitudes.append(lon)
        df["Latitude"] = latitudes
        df["Longitude"] = longitudes

        # Final cleaning
        df["Program"] = program_name
        df = df.where(pd.notnull(df), None)

        return df

    except Exception as e:
        raise ValueError(f"Failed to clean CSV: {str(e)}")
