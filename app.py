import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from datetime import datetime

# Title and header
st.title("Welcome to DC Soccer Club Maps")


df_fields = pd.read_csv("./new_cleaned_fields_data.csv")
df_travel = pd.read_csv("./new_cleaned_travel_data_base.csv")
df_pta_fall = pd.read_csv("./new_cleaned_PTA_fall.csv")
df_players_2017 = pd.read_csv("./new_cleaned_2017_Players_Data.csv")
df_rec_fall_24 = pd.read_csv("./new_cleaned_rec_fall24.csv")
df_adp_fall = pd.read_csv("./cleaned_ADPFallData.csv")

for df in [df_fields, df_travel, df_pta_fall, df_players_2017, df_rec_fall_24, df_adp_fall]:
    df.rename(columns={"latitude": "Latitude", "longitude": "Longitude","zip": "Zip Code"}, inplace=True)

program_names = ["None", "Travel", "Pre-Travel Academy Fall", "2017 Players", "Rec Fall 2024", "Accelerated Development Program Fall"]
dfs = [df_fields, df_travel, df_pta_fall, df_players_2017, df_rec_fall_24, df_adp_fall]

for df, program_name in zip(dfs, program_names):
    df["Program"] = program_name

today = datetime.today()
def calculate_age(birth_date):
    if pd.notnull(birth_date):
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return None

for df in [df_travel, df_rec_fall_24, df_adp_fall]:
  df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
  df["Age"] = df["birth_date"].apply(calculate_age)

df_rec_fall_24.rename(columns={"gender": "Gender", "grade": "Grade", "Race (Check all that apply)": "Race", "School for the 2024-2025 School Year: School in Fall 2024": "School"}, inplace=True)
df_adp_fall.rename(columns={"grade": "Grade"}, inplace=True)


# Combine player datasets
df_players = pd.concat([df_players_2017, df_rec_fall_24, df_pta_fall, df_adp_fall, df_travel], ignore_index=True)


# Lowercase the options in filters for uniqueness
def get_unique_lowercase_options(column):
    # Convert the column to string and then apply .lower()
    return sorted(column.astype(str).str.lower().unique())


# Function to apply filters
def apply_filters(df, filters, column_names):
    for column, selected_values in filters.items():
        if selected_values:
            df = df[df[column].str.lower().isin([val.lower() for val in selected_values])]
    return df

# Map to display player data only
player_map = folium.Map(location=[38.893859, -77.0971477], zoom_start=12)

# Generate heatmap data (players only)
heatmap_data = [[row['Latitude'], row['Longitude']] for index, row in df_players.iterrows()]
HeatMap(heatmap_data).add_to(player_map)

# Render heatmap in Streamlit
st.header("Heat Map in Streamlit")
st_folium(player_map, width=700, height=500)

# FILTERS

# Player Filters
player_filters = {
    "Program": get_unique_lowercase_options(df_players['Program']),
    "Age": get_unique_lowercase_options(df_players['Age'].dropna()),
    "Gender": get_unique_lowercase_options(df_players['Gender']),
    "Grade": get_unique_lowercase_options(df_players['Grade'].dropna()),
    "Race": get_unique_lowercase_options(df_players['Race'].dropna()),
    "School": get_unique_lowercase_options(df_players['School'].dropna()),
}

# Field Filters
field_filters = {
    "Capacity": get_unique_lowercase_options(df_fields['Capacity'].dropna()),
    "Surface": get_unique_lowercase_options(df_fields['Surface'].dropna()),
    "Size": get_unique_lowercase_options(df_fields['Size'].dropna()),
    "Game Size": get_unique_lowercase_options(df_fields['Game Size'].dropna()),
    "Lights": get_unique_lowercase_options(df_fields['Lights'].dropna()),
    "Permanent Lines": get_unique_lowercase_options(df_fields['Permanent Lines'].dropna()),
    "Goals": get_unique_lowercase_options(df_fields['Goals'].dropna())
}

# Create player filter widgets
program = st.sidebar.multiselect("Select Program", [""] + player_filters["Program"])
age = st.sidebar.multiselect("Select Age(s)", [""] + player_filters["Age"])
gender = st.sidebar.selectbox("Select Gender", [""] + player_filters["Gender"])
grade = st.sidebar.selectbox("Select Grade", [""] + player_filters["Grade"])
race = st.sidebar.selectbox("Select Race", [""] + player_filters["Race"])
school = st.sidebar.selectbox("Select School", [""] + player_filters["School"])

# Create field filter widgets
capacity = st.sidebar.selectbox("Select Capacity", [""] + field_filters["Capacity"])
surface = st.sidebar.selectbox("Select Surface", [""] + field_filters["Surface"])
size = st.sidebar.selectbox("Select Size", [""] + field_filters["Size"])
game_size = st.sidebar.selectbox("Select Game Size", [""] + field_filters["Game Size"])
lights = st.sidebar.selectbox("Select Lights", [""] + field_filters["Lights"])
permanent_lines = st.sidebar.selectbox("Select Permanent Lines", [""] + field_filters["Permanent Lines"])
goals = st.sidebar.selectbox("Select Goals", [""] + field_filters["Goals"])

# Apply filters based on user input
filters = {
    "Program": program,
    "Age": age,
    "Gender": gender,
    "Grade": grade,
    "Race": race,
    "School": school,
}

# Filter player data
filtered_players = apply_filters(df_players, filters, list(filters.keys()))

# Filter field data
filtered_fields = df_fields
if capacity:
    filtered_fields = filtered_fields[filtered_fields['Capacity'].str.lower() == capacity[0].lower()]
if surface:
    filtered_fields = filtered_fields[filtered_fields['Surface'].str.lower() == surface[0].lower()]
if size:
    filtered_fields = filtered_fields[filtered_fields['Size'].str.lower() == size[0].lower()]
if game_size:
    filtered_fields = filtered_fields[filtered_fields['Game Size'].str.lower() == game_size[0].lower()]
if lights:
    filtered_fields = filtered_fields[filtered_fields['Lights'].str.lower() == lights[0].lower()]
if permanent_lines:
    filtered_fields = filtered_fields[filtered_fields['Permanent Lines'].str.lower() == permanent_lines[0].lower()]
if goals:
    filtered_fields = filtered_fields[filtered_fields['Goals'].str.lower() == goals[0].lower()]

# Map to display both players and fields
map_pin = folium.Map(location=[38.95, -77.0369], zoom_start=12)

# Pin for filtered players
for index, row in filtered_players.iterrows():
    folium.Marker(
        location=[row["Latitude"], row["Longitude"]],
        popup=f"{row.get('Program', 'N/A')} - {row.get('School', 'N/A')}, Zip: {row.get('Zip Code', 'N/A')}",
        icon=folium.Icon(color="red")
    ).add_to(map_pin)

# Pin for filtered fields
for index, row in filtered_fields.iterrows():
    folium.Marker(
        location=[row["Latitude"], row["Longitude"]],
        popup=f"{row.get('Name', 'N/A')}, {row.get('Capacity', 'N/A')}, {row.get('Surface', 'N/A')}",
        icon=folium.Icon(color="blue")
    ).add_to(map_pin)

# Render pin map in Streamlit
st.header("Pin Map in Streamlit")
st_folium(map_pin, width=700, height=500)

