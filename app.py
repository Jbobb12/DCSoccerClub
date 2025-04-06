import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from datetime import datetime
from distance_mapping import find_optimal_field_for_data
from emails import ALLOWED_EMAILS

# Title and header
st.title("Welcome to DC Soccer Club Maps")

# Google OAuth
# User needs to do "pip install Authlib" before running this code
if not st.experimental_user.is_logged_in:
    if st.button("Login"):
        st.login("google")

elif st.experimental_user.email not in ALLOWED_EMAILS:
    st.write(f"Access denied: You are not authorized to view this page.")
    
    if st.button("Logout"):
        st.logout()
else:

    st.header(f"Hello, {st.experimental_user.name}!")
    st.image(st.experimental_user.picture)

    if st.button("Logout"):
        st.logout()

    # Load data
    df_fields = pd.read_csv("./new_cleaned_fields_data.csv")
    df_travel = pd.read_csv("./new_cleaned_travel_data_base.csv")
    df_pta_fall = pd.read_csv("./new_cleaned_PTA_fall.csv")
    df_players_2017 = pd.read_csv("./new_cleaned_2017_Players_Data.csv")
    df_rec_fall_24 = pd.read_csv("./new_cleaned_rec_fall24.csv")
    df_adp_fall = pd.read_csv("./cleaned_ADPFallData.csv")


    # Standardize column names
    for df in [df_fields, df_travel, df_pta_fall, df_players_2017, df_rec_fall_24, df_adp_fall]:
        df.rename(columns={"latitude": "Latitude", "longitude": "Longitude", "zip": "Zip Code"}, inplace=True)

    program_names = ["None", "Travel", "Pre-Travel Academy Fall", "2017 Players", "Rec Fall 2024", "Accelerated Development Program Fall"]
    dfs = [df_fields, df_travel, df_pta_fall, df_players_2017, df_rec_fall_24, df_adp_fall]

    for df, program_name in zip(dfs, program_names):
        df["Program"] = program_name

    # Calculate age
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

    # Merge player datasets
    df_players = pd.concat([df_players_2017, df_rec_fall_24, df_pta_fall, df_adp_fall, df_travel], ignore_index=True)

    def create_heatmap(df):
        # df = pd.concat([player_df, field_df], ignore_index=True)
        map_obj = folium.Map(location=[38.893859, -77.0971477], zoom_start=12)
        heatmap_data = df[["Latitude", "Longitude"]].dropna().values.tolist()
        if heatmap_data:
            HeatMap(heatmap_data).add_to(map_obj)
        return map_obj

    def create_pin_map(player_df, field_df):
        map_obj = folium.Map(location=[38.893858, -77.0971477], zoom_start=12)
        
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

    def get_lowercase_unique_options(column):
        """ Get sorted unique lowercase options """
        return sorted(df_players[column].dropna().astype(str).str.lower().unique())

    def get_numeric_sorted_options(column):
        """ Get sorted unique numeric options """
        return sorted(df_players[column].dropna().astype(int).unique())

    df_players["Race"] = df_players["Race"].astype(str).str.lower().str.strip()
    df_players["Race List"] = df_players["Race"].apply(lambda x: x.split(",") if pd.notnull(x) else [])

    def get_unique_race_options():
        """ Get unique race options """
        unique_races = set()
        df_players["Race"].dropna().astype(str).str.lower().apply(lambda x: unique_races.update(x.split(", ")))
        return sorted(unique_races)

    selected_programs = st.sidebar.multiselect("Select Program", get_lowercase_unique_options("Program"))
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
            filtered_players = filtered_players[filtered_players["Program"].str.lower().isin(selected_programs)]
        if selected_ages:
            filtered_players = filtered_players[filtered_players["Age"].isin(selected_ages)]
        if selected_gender:
            filtered_players = filtered_players[filtered_players["Gender"].str.lower().isin([selected_gender])]
        if selected_grade:
            filtered_players = filtered_players[filtered_players["Grade"].isin(selected_grade)]
        if selected_race:
            filtered_players = filtered_players[filtered_players["Race List"].apply(lambda races: any(race in races for race in selected_race))]
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



    # def calculate_distances(players_df, fields_df):
    #     distances = pd.DataFrame(index=players_df.index, columns=fields_df['Name'])

    #     for player_idx, player in players_df.iterrows():
    #         player_coords = (player['latitude'], player['longitude'])

    #         for field_idx, field in fields_df.iterrows():
    #             field_coords = (field['latitude'], field['longitude'])
    #             distances.at[player_idx, field['Name']] = distance(player_coords, field_coords).miles
                
    #     return distances

    # def find_optimal_field(distance_df):
    #     avg_distances = distance_df.mean()
    #     return avg_distances, avg_distances.idxmin()

    # fields_df = pd.read_csv('distance_mapping/new_cleaned_fields_data.csv')

    # fields_df['latitude'] = pd.to_numeric(fields_df['latitude'])
    # fields_df['longitude'] = pd.to_numeric(fields_df['longitude'])

    # optimal_fields = {}

    # program_files = ['distance_mapping/new_cleaned_2017_Players_Data.csv', 'distance_mapping/new_cleaned_PTA_fall.csv', 'distance_mapping/new_cleaned_rec_fall24.csv', 'distance_mapping/new_cleaned_travel_data_base.csv']

    # for file in program_files:
    #     program_name = file.split('_')[3]
    #     players_df = pd.read_csv(file)

    #     players_df['latitude'] = pd.to_numeric(players_df['latitude'])
    #     players_df['longitude'] = pd.to_numeric(players_df['longitude'])
        
    #     distances = calculate_distances(players_df, fields_df)
    #     avg_distances, optimal_field = find_optimal_field(distances)
    #     optimal_fields[program_name] = optimal_field
    #     #print optimal field and average distance for each file
    #     print(f'Optimal field for {program_name} is {optimal_field} with an average distance of {avg_distances[optimal_field]} miles')
