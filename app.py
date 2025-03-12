import streamlit as st
import pandas as pd
import numpy as np
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import folium
from datetime import datetime
from geopy.distance import distance


# Title and header
st.title("Welcome to DC Soccer Club Maps")

# Text input and button

import pandas as pd
import numpy as np



#HEAT MAPPING
travel_df = pd.read_csv("/Users/jadenbobb/Desktop/DCSoccerClubNew/new_cleaned_travel_data_base.csv")#  next 5 lines need to be edited based on local computer
players_2017_df = pd.read_csv("/Users/jadenbobb/Desktop/DCSoccerClubNew/new_cleaned_2017_Players_Data.csv")
rec_fall_24_df = pd.read_csv("/Users/jadenbobb/Desktop/DCSoccerClubNew/new_cleaned_rec_fall24.csv")
fields_df = pd.read_csv("/Users/jadenbobb/Desktop/DCSoccerClubNew/new_cleaned_2017_Players_Data.csv")
pta_df = pd.read_csv("/Users/jadenbobb/Desktop/DCSoccerClubNew/new_cleaned_PTA_fall.csv")
adp_df = pd.read_csv("/Users/jadenbobb/Desktop/DCSoccerClubNew/cleaned_ADPFallData.csv")

datasets = [travel_df, players_2017_df, rec_fall_24_df, fields_df, pta_df, adp_df]
for df in datasets:
    df.dropna(subset=['latitude', 'longitude'], inplace=True)

# Combine all datasets into one
combined_df = pd.concat(datasets)

# Convert latitude and longitude columns to float
combined_df['latitude'] = combined_df['latitude'].astype(float)
combined_df['longitude'] = combined_df['longitude'].astype(float)
data = combined_df.copy()

map = folium.Map(location=[38.893859, -77.0971477], zoom_start=12)

# Generate heatmap data from filtered dataset
heatmap_data = [[row['latitude'], row['longitude']] for index, row in data.iterrows()]
HeatMap(heatmap_data).add_to(map)

# Render the map in Streamlit
st.header("Heat Map in Streamlit")
st_folium(map,width=700,height=500)

#FILTERING FOR HEAT MAP

#pinpoint mapping
df1 = pd.read_csv("/Users/jadenbobb/Desktop/DCSoccerClubNew/new_cleaned_fields_data.csv")
df2 = pd.read_csv("/Users/jadenbobb/Desktop/DCSoccerClubNew/new_cleaned_travel_data_base.csv")
df3 = pd.read_csv("/Users/jadenbobb/Desktop/DCSoccerClubNew/new_cleaned_PTA_fall.csv")
df4 = pd.read_csv("/Users/jadenbobb/Desktop/DCSoccerClubNew/new_cleaned_2017_Players_Data.csv")
df5 = pd.read_csv("/Users/jadenbobb/Desktop/DCSoccerClubNew/new_cleaned_rec_fall24.csv")
df6 = pd.read_csv("/Users/jadenbobb/Desktop/DCSoccerClubNew/cleaned_ADPFallData.csv")

for df in [df1, df2, df3, df4, df5, df6]:
    df.rename(columns={"latitude": "Latitude", "longitude": "Longitude","zip": "Zip Code"}, inplace=True)

program_names = ["None", "Travel", "Pre-Travel Academy Fall", "2017 Players", "Rec Fall 2024", "Accelerated Development Program Fall"]
dfs = [df1, df2, df3, df4, df5, df6]

for df, program_name in zip(dfs, program_names):
    df["Program"] = program_name

today = datetime.today()
def calculate_age(birth_date):
    if pd.notnull(birth_date):
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return None

for df in [df2, df5, df6]:
  df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
  df["Age"] = df["birth_date"].apply(calculate_age)

df5.rename(columns={"gender": "Gender", "grade": "Grade", "Race (Check all that apply)": "Race", "School for the 2024-2025 School Year: School in Fall 2024": "School"}, inplace=True)
df6.rename(columns={"grade": "Grade"}, inplace=True)

program_colors = {
    "None": "cadetblue",
    "Travel": "red",
    "Pre-Travel Academy Fall": "red",
    "2017 Players": "red",
    "Rec Fall 2024": "red",
    "Accelerated Development Program Fall": "red"
}

df_all = pd.concat([df1, df2, df3, df4, df5, df6], ignore_index=True)


map_pin = folium.Map(location=[38.95, -77.0369], zoom_start=12)

counter=0
for index, row in df_all.iterrows():
    if counter<500:
        program_name = row.get("Program", "Unknown")
        marker_color = program_colors.get(program_name, "cadetblue")
        folium.Marker(location=[row["Latitude"], row["Longitude"]],
                        popup=f"{row.get('Program', 'N/A')} - {row.get('School', 'N/A')}, Zip: {row.get('Zip Code', 'N/A')}",
                        icon=folium.Icon(color=marker_color)).add_to(map_pin)
        counter=counter+1



st.header("Pin Map in Streamlit")
st_folium(map_pin,width=700,height=500)
program=st.sidebar.multiselect("Select Program", df_all["Program"].unique())
age=st.sidebar.multiselect("Select Age(s)",df_all["Age"].unique())
gender=st.sidebar.selectbox("Select Gender",df_all["Gender"].unique())

#DISTANCING
st.header("Optimal Distance in Streamlit")
selected_option = st.selectbox("Choose a Program",df_all["Program"].unique())
if st.button("Submit"):
    st.write(f"You submitted: {selected_option}")
    st.write(f"The optimal field is: {answer}")
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