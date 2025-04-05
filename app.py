import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from datetime import datetime
from distance_mapping import find_optimal_field_for_data
import ssl
import certifi
import time
import os
import random
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import geopy.geocoders
import io

# ─────────────────────────────────────────────────────────────────────────────
# Title and header
# ─────────────────────────────────────────────────────────────────────────────
st.title("Welcome to DC Soccer Club Maps")

# ─────────────────────────────────────────────────────────────────────────────
# Geocoding Function
# ─────────────────────────────────────────────────────────────────────────────
def geocode_new_file(temp_df):
    """
    Geocodes the addresses within temp_df using Nominatim (geopy).
    Returns a new DataFrame with columns ["player_first_name", "player_last_name", "address",
    "city", "state", "zip", "birhtdate", "grade", "program", "team_id", "latitude", "longitude"].
    """
    # Create SSL context for geopy
    ctx = ssl._create_unverified_context(cafile=certifi.where())
    geopy.geocoders.options.default_ssl_context = ctx
    
    # Drop irrelevant columns
    columns_to_keep = ["player_first_name", "player_last_name", "address",
                       "city", "state", "zip", "birhtdate", "grade", "program", "team_id"]
    temp_df = temp_df[[col for col in temp_df.columns if col in columns_to_keep]].copy()

    # Define a list of user agents to rotate through
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0)",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)",
        "Mozilla/5.0 (Linux; Android 10; SM-G973F)",
        "Trying Something New w/ it",
        "John pork is calling",
        "This should be enough I think? Inshallah?"
    ]

    # Initialize geolocator with an initial user agent
    geolocator = Nominatim(user_agent="DCSoccerClub", scheme="http")

    def get_lat_lon(address):
        # Sleep 1s before calling geocode to avoid potential rate-limit
        time.sleep(1)
        try:
            location = geolocator.geocode(address)
            if location:
                return location.latitude, location.longitude
            else:
                return None, None
        except GeocoderTimedOut:
            return None, None

    # Clean up the address columns
    temp_df["address"] = temp_df["address"].astype(str).str.replace(",", "", regex=False)
    temp_df["city"] = temp_df["city"].astype(str).str.replace(",", "", regex=False)

    # Create full address column
    temp_df["full_address"] = (
        temp_df["address"].str.replace(r"(unit|#|apt).*", "", regex=True, case=False).astype(str)
        + ", " + temp_df["city"].astype(str)
        + ", " + temp_df["state"].astype(str)
        + " " + temp_df["zip"].astype(str)
    )

    # Initialize latitude/longitude columns
    temp_df["latitude"] = None
    temp_df["longitude"] = None

    #Print the first 10 rows of the DataFrame
    print(temp_df.head(10))

    #Print the size of the DataFrame
    print(temp_df.shape)

    # Loop through rows, geocoding addresses
    for index, row in temp_df.iterrows():
        # Optionally, one could switch user agent every X rows, e.g.:
        # if index > 0 and index % 200 == 0:
        #     new_user_agent = random.choice(user_agents)
        #     geolocator = Nominatim(user_agent=new_user_agent, scheme="http")

        lat, lon = get_lat_lon(row["full_address"])
        temp_df.at[index, "latitude"] = lat
        temp_df.at[index, "longitude"] = lon
        # Optional: print progress
        print(f"Geocoded {index + 1} addresses...")
        # Print the current row
        print(row)
        # Sleep 3s to further reduce chance of rate-limiting
        time.sleep(3)


    # Clean up
    temp_df.drop(columns=["full_address"], inplace=True)
    return temp_df

# ─────────────────────────────────────────────────────────────────────────────
# File Upload & Geocoding
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("Upload Your CSV File to Geocode")
uploaded_file = st.file_uploader("Drag and drop your .csv file here", type=["csv"])

new_data_df = None  # We'll store the geocoded dataframe here if there's an upload

if uploaded_file is not None:
    # Display an instruction
    st.write("Once geocoding completes, a download button will appear with the geocoded CSV.")
    # Convert the uploaded file to a DataFrame
    df_temp = pd.read_csv(uploaded_file)
    
    # We'll store the geocoded DataFrame in memory
    geocoded_df = geocode_new_file(df_temp)
    
    st.success("Geocoding complete! You can now download the cleaned CSV below.")
    
    # Provide a download button for the new, cleaned CSV
    csv_buffer = io.StringIO()
    geocoded_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download Geocoded CSV",
        data=csv_buffer.getvalue(),
        file_name="geocoded_data.csv",
        mime="text/csv"
    )
    
    # Keep a copy for adding into the pipeline below
    new_data_df = geocoded_df.copy()

# ─────────────────────────────────────────────────────────────────────────────
# Load Existing Data
# ─────────────────────────────────────────────────────────────────────────────
df_fields = pd.read_csv("./new_cleaned_fields_data.csv")
df_travel = pd.read_csv("./new_cleaned_travel_data_base.csv")
df_pta_fall = pd.read_csv("./new_cleaned_PTA_fall.csv")
df_players_2017 = pd.read_csv("./new_cleaned_2017_Players_Data.csv")
df_rec_fall_24 = pd.read_csv("./new_cleaned_rec_fall24.csv")
df_adp_fall = pd.read_csv("./cleaned_ADPFallData.csv")

# IMPORTANT: the user code repeated the same path for df_adp_fall, so comment out the second reference.
# df_adp_fall = pd.read_csv("./Data_Cleaned.csv")  # <--- remove or rename if needed

# ─────────────────────────────────────────────────────────────────────────────
# Standardize column names across loaded data
# ─────────────────────────────────────────────────────────────────────────────
for df in [df_fields, df_travel, df_pta_fall, df_players_2017, df_rec_fall_24, df_adp_fall]:
    df.rename(columns={
        "latitude": "Latitude",
        "longitude": "Longitude",
        "zip": "Zip Code"
    }, inplace=True)

program_names = ["None", "Travel", "Pre-Travel Academy Fall", "2017 Players", "Rec Fall 2024", "Accelerated Development Program Fall"]
dfs = [df_fields, df_travel, df_pta_fall, df_players_2017, df_rec_fall_24, df_adp_fall]

for df, program_name in zip(dfs, program_names):
    df["Program"] = program_name

# Calculate age function
today = datetime.today()
def calculate_age(birth_date):
    if pd.notnull(birth_date):
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return None

# Convert birth_date to datetime in specific dataframes
for df in [df_travel, df_rec_fall_24, df_adp_fall]:
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
    df["Age"] = df["birth_date"].apply(calculate_age)

# Rename some columns for consistency
df_rec_fall_24.rename(columns={
    "gender": "Gender",
    "grade": "Grade",
    "Race (Check all that apply)": "Race",
    "School for the 2024-2025 School Year: School in Fall 2024": "School"
}, inplace=True)

df_adp_fall.rename(columns={"grade": "Grade"}, inplace=True)

# ─────────────────────────────────────────────────────────────────────────────
# Merge all known player datasets
# ─────────────────────────────────────────────────────────────────────────────
df_players = pd.concat([df_players_2017, df_rec_fall_24, df_pta_fall, df_adp_fall, df_travel], ignore_index=True)

# If there's newly uploaded data that has been geocoded, we incorporate it here too.
if new_data_df is not None:
    # Standardize columns to match the rest
    new_data_df.rename(columns={
        "latitude": "Latitude",
        "longitude": "Longitude",
        "zip": "Zip Code"
    }, inplace=True)
    
    # If "program" column isn't present, default to "New Program"
    if "program" not in new_data_df.columns:
        new_data_df["program"] = "New Program"
    
    # Let’s rename birthdate -> birth_date if needed
    if "birhtdate" in new_data_df.columns:
        new_data_df.rename(columns={"birhtdate": "birth_date"}, inplace=True)
    if "birthdate" in new_data_df.columns:
        new_data_df.rename(columns={"birthdate": "birth_date"}, inplace=True)
    
    # Convert birth_date to datetime, then compute Age if possible
    new_data_df["birth_date"] = pd.to_datetime(new_data_df["birth_date"], errors="coerce")
    new_data_df["Age"] = new_data_df["birth_date"].apply(calculate_age)
    
    # Standard column naming for the Program column
    if "program" in new_data_df.columns:
        # We'll store it in a single consistent name
        new_data_df["Program"] = new_data_df["program"]
    
    # Add it to the main df_players
    df_players = pd.concat([df_players, new_data_df], ignore_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# Heatmap and Pin Map creation
# ─────────────────────────────────────────────────────────────────────────────
def create_heatmap(df):
    map_obj = folium.Map(location=[38.893859, -77.0971477], zoom_start=12)
    heatmap_data = df[["Latitude", "Longitude"]].dropna().values.tolist()
    if heatmap_data:
        HeatMap(heatmap_data).add_to(map_obj)
    return map_obj

def create_pin_map(player_df, field_df):
    map_obj = folium.Map(location=[38.95, -77.0369], zoom_start=12)
    
    # Limit player markers to 500
    for _, row in player_df.head(500).iterrows():
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=f"{row.get('Program', 'N/A')} - {row.get('School', 'N/A')}, Zip: {row.get('Zip Code', 'N/A')}",
            icon=folium.Icon(color="red")
        ).add_to(map_obj)
    
    for _, row in field_df.iterrows():
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=f"{row.get('Name', 'N/A')}, {row.get('Capacity', 'N/A')}, {row.get('Surface', 'N/A')}",
            icon=folium.Icon(color="blue")
        ).add_to(map_obj)
    
    return map_obj

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar Filters
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.header("Player Filters")

df_players["Grade"] = df_players["Grade"].astype(str).str.strip().str.lower()
df_players["Race"] = df_players["Race"].astype(str).str.lower().str.strip()

# For race-based filtering, split multiple race entries by commas
df_players["Race List"] = df_players["Race"].apply(lambda x: x.split(",") if pd.notnull(x) else [])

def get_lowercase_unique_options(column):
    """Get sorted unique lowercase options."""
    return sorted(df_players[column].dropna().astype(str).str.lower().unique())

def get_numeric_sorted_options(column):
    """Get sorted unique numeric options."""
    return sorted(df_players[column].dropna().astype(int).unique())

def get_unique_race_options():
    """ Get unique race options. """
    unique_races = set()
    df_players["Race"].dropna().astype(str).str.lower().apply(
        lambda x: unique_races.update(x.split(", "))
    )
    return sorted(unique_races)

# Program
selected_programs = st.sidebar.multiselect("Select Program", get_lowercase_unique_options("Program"))

# Age
selected_ages = st.sidebar.multiselect("Select Age", get_numeric_sorted_options("Age"))

# Gender
selected_gender = st.sidebar.selectbox("Select Gender", [""] + get_lowercase_unique_options("Gender"))

# Grade
selected_grade = st.sidebar.multiselect("Select Grade", get_lowercase_unique_options("Grade"))

# Race
selected_race = st.sidebar.multiselect("Select Race", get_unique_race_options())

# School
selected_school = st.sidebar.multiselect("Select School", get_lowercase_unique_options("School"))

# Filter the df_players accordingly
filtered_players = df_players.copy()

if selected_grade:
    # Lower-case matching
    selected_grade = [g.lower().strip() for g in selected_grade]
    filtered_players = filtered_players[filtered_players["Grade"].isin(selected_grade)]

if any([selected_programs, selected_ages, selected_gender, selected_grade, selected_race, selected_school]):
    if selected_programs:
        filtered_players = filtered_players[filtered_players["Program"].str.lower().isin(selected_programs)]
    if selected_ages:
        filtered_players = filtered_players[filtered_players["Age"].isin(selected_ages)]
    if selected_gender:
        # single selectbox
        filtered_players = filtered_players[filtered_players["Gender"].str.lower().isin([selected_gender])]
    if selected_grade:
        filtered_players = filtered_players[filtered_players["Grade"].isin(selected_grade)]
    if selected_race:
        filtered_players = filtered_players[filtered_players["Race List"].apply(lambda races: any(race in races for race in selected_race))]
    if selected_school:
        filtered_players = filtered_players[filtered_players["School"].str.lower().isin(selected_school)]
else:
    # If no filters are selected at all, default to no players
    filtered_players = pd.DataFrame(columns=df_players.columns)

# ─────────────────────────────────────────────────────────────────────────────
# Field Filters
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.header("Field Filters")

def get_field_lowercase_options(column):
    """Get sorted unique lowercase options for fields."""
    return sorted(df_fields[column].dropna().astype(str).str.lower().unique())

def get_field_numeric_options(column):
    """Get sorted unique numeric options for fields."""
    return sorted(df_fields[column].dropna().astype(int).unique())

selected_capacity = st.sidebar.multiselect("Select Capacity", get_field_numeric_options("Capacity"))
selected_surface = st.sidebar.multiselect("Select Surface", get_field_lowercase_options("Surface"))
selected_size = st.sidebar.multiselect("Select Size", get_field_lowercase_options("Size"))
selected_game_size = st.sidebar.multiselect("Select Game Size", get_field_lowercase_options("Game Size"))
selected_lights = st.sidebar.selectbox("Select Lights", [""] + get_field_lowercase_options("Lights"))
selected_permanent_lines = st.sidebar.multiselect("Select Permanent Lines", get_field_lowercase_options("Permanent Lines"))
selected_goals = st.sidebar.selectbox("Select Goals", [""] + get_field_lowercase_options("Goals"))

filtered_fields = df_fields.copy()

if any([selected_capacity, selected_surface, selected_size, selected_game_size, selected_lights, selected_permanent_lines, selected_goals]):
    if selected_capacity:
        filtered_fields = filtered_fields[filtered_fields["Capacity"].isin(selected_capacity)]
    if selected_surface:
        filtered_fields = filtered_fields[filtered_fields["Surface"].str.lower().isin(selected_surface)]
    if selected_size:
        filtered_fields = filtered_fields[filtered_fields["Size"].str.lower().isin(selected_size)]
    if selected_game_size:
        filtered_fields = filtered_fields[filtered_fields["Game Size"].str.lower().isin(selected_game_size)]
    if selected_lights:
        filtered_fields = filtered_fields[filtered_fields["Lights"].str.lower() == selected_lights]
    if selected_permanent_lines:
        filtered_fields = filtered_fields[filtered_fields["Permanent Lines"].str.lower().isin(selected_permanent_lines)]
    if selected_goals:
        filtered_fields = filtered_fields[filtered_fields["Goals"].str.lower() == selected_goals]
else:
    # If no field filters are selected at all, default to no fields
    filtered_fields = pd.DataFrame(columns=df_fields.columns)

# ─────────────────────────────────────────────────────────────────────────────
# Display the Maps
# ─────────────────────────────────────────────────────────────────────────────
st.header("Heat Map")
st_folium(create_heatmap(filtered_players), width=700, height=500)

st.header("Pin Map")
st_folium(create_pin_map(filtered_players, filtered_fields), width=700, height=500)

# ─────────────────────────────────────────────────────────────────────────────
# Distance Mapping – find_optimal_field_for_data usage
# (Assuming you have a function called find_optimal_field_for_data)
# ─────────────────────────────────────────────────────────────────────────────


st.header("Optimal Distance in Streamlit")
if st.button("Submit"):
    best_field, avg_dist = find_optimal_field_for_data(filtered_players, filtered_fields)
    if best_field is not None:
        st.write(f"The optimal field is {best_field}, with average distance {avg_dist:.2f} miles.")
    else:
        st.write("No best field found (no players or no fields).")
else:
    st.write("Please select an option and click Submit.")
