import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from datetime import datetime
from distance_mapping import find_optimal_field_for_data
from emails import ALLOWED_EMAILS

# Force light mode theme
st.set_page_config(
    page_title="DC Soccer Club Maps",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Control for different views
if "view" not in st.session_state:
    st.session_state.view = "home"

if "is_adding_program" not in st.session_state:
    st.session_state.is_adding_program = False

if "is_deleting_program" not in st.session_state:
    st.session_state.is_deleting_program = False

if "added_programs" not in st.session_state:
    st.session_state.added_programs = []

if "manage_program_names" not in st.session_state:
    st.session_state.manage_program_names = []


#Google OAuth
#User needs to do "pip install Authlib" before running this code
if not st.experimental_user.is_logged_in:
    if st.button("Login"):
        st.login("google")

if st.experimental_user is None:
    st.info("Please log in to access this app.")
    st.stop()

if st.experimental_user.email not in ALLOWED_EMAILS:
    st.error("Access denied: You are not authorized to view this page.")
    st.stop()

elif st.experimental_user.email not in ALLOWED_EMAILS:
    st.write(f"Access denied: You are not authorized to view this page.")
    
    if st.button("Logout"):
        st.logout()
else:
    st.header(f"Hello, {st.experimental_user.name}!")
    st.image(st.experimental_user.picture)

    if st.button("Logout"):
        st.logout()

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


# Load data
df_fields = pd.read_csv("./new_cleaned_fields_data.csv")
df_travel = pd.read_csv("./new_cleaned_travel_data_base.csv")
df_pta_fall = pd.read_csv("./new_cleaned_PTA_fall.csv")
df_players_2017 = pd.read_csv("./new_cleaned_2017_Players_Data.csv")
df_rec_fall_24 = pd.read_csv("./new_cleaned_rec_fall24.csv")
df_adp_fall = pd.read_csv("./cleaned_ADPFallData.csv")

column_mapping = {
    "latitude": "Latitude", 
    "longitude": "Longitude", 
    "zip": "Zip Code",
    "gender": "Gender", 
    "grade": "Grade",
    "Race (Check all that apply)": "Race",
    "School for the 2024-2025 School Year: School in Fall 2024": "School",
    "School for the 2024-2025 School Year:": "School",
    "program": "Program"
}

for df in [df_fields, df_travel, df_pta_fall, df_players_2017, df_rec_fall_24, df_adp_fall]:
    df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns}, inplace=True)

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
df_adp_fall.rename(columns={"gender":"Gender", "grade": "Grade"}, inplace=True)
df_travel.rename(columns={"gender":"Gender"}, inplace=True)
df_players_2017.rename(columns={"gender":"Gender"}, inplace=True)
df_pta_fall.rename(columns={"gender":"Gender"}, inplace=True)

# Merge player datasets
df_players = pd.concat([df_players_2017, df_rec_fall_24, df_pta_fall, df_adp_fall, df_travel], ignore_index=True)

def create_heatmap(df):
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


st.sidebar.text("")
st.sidebar.text("")
st.sidebar.text("")

if st.sidebar.button("Manage Programs", key="nav_manage_ui"):
    st.session_state.view = "manage"

st.sidebar.markdown("---")

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

if st.session_state.view == "manage":
    st.header("Manage Programs")
    st.markdown("Here you can view, add, or delete programs.")

    st.markdown("---")

    st.markdown("### Current Programs:")
    if st.session_state.manage_program_names:
        for p in st.session_state.manage_program_names:
            st.write(f"• {p}")
    else:
        st.write("No programs currently added.")

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Add Program"):
            st.session_state.is_adding_program = True
            st.session_state.is_deleting_program = False
    
    with col2:
        if st.button("Delete Program"):
            if st.session_state.manage_program_names:
                st.session_state.is_deleting_program = True
                st.session_state.is_adding_program = False
            else:
                st.warning("No programs available to delete.")
    with col3:
        if st.button("Back to Home", key="visible_home"):
            st.session_state.view = "home"
    st.markdown("---")

if st.session_state.is_adding_program:
    st.header("Add New Program")
    st.markdown("Fill in the form below to add a new program to the system.")
    st.markdown("---")

    name = st.text_input("Program Name")
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    if st.button("Submit Program"):
        if not name:
            st.error("Please enter a program name.")
        elif not uploaded_file:
            st.error("Please upload a CSV file.")
        else:
        # Read and process the uploaded file
            try:
                df_uploaded = pd.read_csv(uploaded_file)
                df_uploaded["Program"] = name

                st.session_state.added_programs.append({"name": name, "data": df_uploaded})
                st.session_state.manage_program_names.append(name)

                st.success(f"Successfully added program: **{name}**.")
                st.session_state.is_adding_program = False
            except Exception as e:
                st.error(f"Error reading file: {e}")

if st.session_state.is_deleting_program:
    st.header("Delete a Program")
    st.markdown("Select a program to remove from the list.")

    program_to_delete = st.selectbox("Choose a program", st.session_state.manage_program_names)

    if st.button("Confirm Delete"):
        if program_to_delete in st.session_state.manage_program_names:
            st.session_state.manage_program_names.remove(program_to_delete)

        st.session_state.added_programs = [
            prog for prog in st.session_state.added_programs
            if prog["name"] != program_to_delete
        ]

        st.session_state.deletion_confirmed = True  # 💥 New flag
        st.success(f"Deleted program: {program_to_delete}")
        st.session_state.is_deleting_program = False

# Display updated maps
if st.session_state.view == "home":

    # Title and header
    st.title("Welcome to DC Soccer Club Maps")

    st.header(f"Hello, {st.experimental_user.name}!")
    if st.experimental_user.picture:
        st.image(st.experimental_user.picture)

    if st.button("Logout"):
        st.logout()

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
