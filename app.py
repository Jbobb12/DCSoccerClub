import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from datetime import datetime
from distance_mapping import find_optimal_field_for_data
from supabase import create_client, Client
import ast

supabase_url = st.secrets["supabase"]["url"]
supabase_key = st.secrets["supabase"]["api_key"]

supabase: Client = create_client(supabase_url, supabase_key)

# Title and header
st.title("Welcome to DC Soccer Club Maps")

# Custom Styling
st.markdown(
    """
    <style>
        /* Apply dark blue background */
        body {
            background-color: #ffffff; /* Dark Blue */
            color: white;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #0A1931; /* Dark Blue */
        }

        /* Primary button styling */
        .stButton>button {
            background-color: #D72638 !important; /* Red */
            color: white !important;
            border-radius: 8px;
            padding: 10px 20px;
            border: none;
        }
        

        h1 {
            margin-top: 20px !important;
            padding-top: 20px !important;
            color: black !important;
        }
        
        /* Headers styling */
        h1, h2, h3, h4 {
            color: black;
        }
        
        /* Change background of main content */
        .block-container {
            background-color: #ffffff !important; /* Dark Blue */
            padding-top: 30px;
            border-radius: 10px;
        }

        /* Change input text color */
        .stTextInput>div>div>input {
            color: black !important;
        }

        /* Sidebar text and filters */
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] label {
            color: white;
        }

        /* Make selection dropdowns match the theme */
        .stSelectbox>div>div>select {
            background-color: #D72638 !important; /* Red */
            color: white !important;
            border-radius: 5px;
        }
        
        /* Change table style */
        table {
            border-collapse: collapse;
            width: 100%;
        }

        th {
            background-color: #D72638; /* Red */
            color: white;
            padding: 10px;
        }

        td {
            padding: 8px;
            color: black;
        }

        /* Heatmap and Map Styling */
        .folium-map {
            border: 2px solid white;
            border-radius: 10px;
        }
        
    </style>
    """,
    unsafe_allow_html=True
)

# Add Logo to Sidebar
st.sidebar.image("./DC_Soccer_Logo.png", use_container_width=True)

def fetch_data(table_name):
    all_data = []
    page_size = 1000
    start = 0

    while True:
        response = supabase.table(table_name).select("*").range(start, start + page_size - 1).execute()
        data = response.data

        if not data:
            break  # No more rows to fetch

        all_data.extend(data)
        start += page_size

    return pd.DataFrame(all_data)


df_fields = fetch_data("Fields")
df_players = fetch_data("Players")



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

# Sidebar filters
st.sidebar.header("Player Filters")

def get_unique_options(column):
    """ Get sorted unique options """
    return sorted(df_players[column].unique())

def get_lowercase_unique_options(column):
    """ Get sorted unique lowercase options """
    return sorted(df_players[column].dropna().astype(str).str.lower().unique())

def get_numeric_sorted_options(column):
    """ Get sorted unique numeric options """
    return sorted(df_players[column].dropna().astype(int).unique())

def get_unique_race_options():
    """ Get unique race options from Race List column """
    unique_races = set()

    # Go through each race_list_str, convert to list, add to set
    df_players["Race List"].dropna().apply(
        lambda race_list_str: unique_races.update(ast.literal_eval(race_list_str))
    )

    return sorted(race.strip() for race in unique_races)  # Remove extra spaces just in case


selected_programs = st.sidebar.multiselect("Select Program", get_unique_options("Program"))
selected_ages = st.sidebar.multiselect("Select Age", get_numeric_sorted_options("Age"))
selected_gender = st.sidebar.selectbox("Select Gender", [""] + get_lowercase_unique_options("Gender"))
selected_grade = st.sidebar.multiselect("Select Grade", get_lowercase_unique_options("Grade"))
selected_race = st.sidebar.multiselect("Select Race", get_unique_race_options())
selected_school = st.sidebar.multiselect("Select School", get_lowercase_unique_options("School"))

# Field Filters
st.sidebar.header("Field Filters")

def get_field_lowercase_options(column):
    """ Get sorted unique lowercase options for fields """
    return sorted(df_fields[column].dropna().astype(str).str.lower().unique())

def get_field_numeric_options(column):
    """ Get sorted unique numeric options for fields """
    return sorted(df_fields[column].dropna().astype(int).unique())

selected_capacity = st.sidebar.multiselect("Select Capacity", get_field_numeric_options("Capacity"))
selected_surface = st.sidebar.multiselect("Select Surface", get_field_lowercase_options("Surface"))
selected_size = st.sidebar.multiselect("Select Size", get_field_lowercase_options("Size"))
selected_game_size = st.sidebar.multiselect("Select Game Size", get_field_lowercase_options("Game Size"))
selected_lights = st.sidebar.selectbox("Select Lights", [""] + get_field_lowercase_options("Lights"))
selected_permanent_lines = st.sidebar.multiselect("Select Permanent Lines", get_field_lowercase_options("Permanent Lines"))
selected_goals = st.sidebar.selectbox("Select Goals", [""] + get_field_lowercase_options("Goals"))

df_players["Grade"] = df_players["Grade"].astype(str).str.strip().str.lower()

# Apply Player Filters
filtered_players = df_players.copy()

if selected_grade:
    filtered_players = filtered_players[filtered_players["Grade"].isin([g.lower().strip() for g in selected_grade])]

if any([selected_programs, selected_ages, selected_gender, selected_grade, selected_race, selected_school]):
    if selected_programs:
        filtered_players = filtered_players[filtered_players["Program"].isin(selected_programs)]
    if selected_ages:
        filtered_players = filtered_players[filtered_players["Age"].isin(selected_ages)]
    if selected_gender:
        filtered_players = filtered_players[filtered_players["Gender"].str.lower().isin([selected_gender])]
    if selected_grade:
        filtered_players = filtered_players[filtered_players["Grade"].isin(selected_grade)]
    if selected_race:
        filtered_players = filtered_players[
            filtered_players["Race List"].apply(
                lambda race_list_str: any(
                    race in ast.literal_eval(race_list_str) for race in selected_race
                ) if pd.notnull(race_list_str) else False
            )
        ]
    if selected_school:
        filtered_players = filtered_players[filtered_players["School"].str.lower().isin(selected_school)]
else:
    filtered_players = pd.DataFrame(columns=df_players.columns)

# Apply Field Filters
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
    filtered_fields = pd.DataFrame(columns=df_fields.columns)

# Display updated maps
st.header("Heat Map")
st_folium(create_heatmap(filtered_players), width=700, height=500)

st.header("Pin Map")
st_folium(create_pin_map(filtered_players, filtered_fields), width=700, height=500)



#DISTANCING
st.header("Optimal Distance in Streamlit")
#selected_option = st.selectbox("Choose a Program",df_players["Program"].unique())
if st.button("Submit"):
    print(filtered_players)
    best_field, avg_dist = find_optimal_field_for_data(filtered_players, filtered_fields)
    if best_field is not None:
        st.write(f"The optimal field is {best_field}, with average distance {avg_dist:.2f} miles.")
    else:
        st.write("No best field found (no players or no fields).")
else:
    st.write("Please select an option and click Submit.")

