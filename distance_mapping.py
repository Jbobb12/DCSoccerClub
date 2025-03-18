import pandas as pd
from geopy.distance import distance

def calculate_distances(players_df, fields_df):
    """
    Computes the distance in miles from each player to each field,
    returning a DataFrame whose columns are field names and rows are players.
    """
    # Prepare an empty DataFrame with player indices vs. field Names
    distances = pd.DataFrame(index=players_df.index, columns=fields_df['Name'])

    for player_idx, player in players_df.iterrows():
        player_coords = (player['latitude'], player['longitude'])
        for field_idx, field in fields_df.iterrows():
            field_coords = (field['latitude'], field['longitude'])
            # Use geopy.distance to compute miles
            distances.at[player_idx, field['Name']] = distance(player_coords, field_coords).miles

    return distances

def find_optimal_field(distance_df):
    """
    Given a distance matrix (players as rows, fields as columns),
    returns the Series of average distances (index=field name) 
    and the name of the field with the smallest average distance.
    """
    avg_distances = distance_df.mean()
    return avg_distances, avg_distances.idxmin()

def group_and_print_optimal_fields(players_df, fields_df, group_col, label_prefix=None):
    """
    1. Groups 'players_df' by the column 'group_col'.
    2. For each distinct group value, calculates and prints the optimal field.

    'label_prefix' lets you customize how you label the printed lines:
       - If group_col='birth_year', you might set label_prefix='birth year'
         so lines read "birth year 2018 optimal field is X..."
       - If group_col='grade', you might just leave label_prefix=None 
         to print "1st grade optimal field is X..."
    """
    # If grouping by birth_year but the DataFrame only has 'birth_date',
    # convert birth_date -> birth_year if not already done.
    if group_col == 'birth_year' and 'birth_year' not in players_df.columns:
        players_df['birth_year'] = pd.to_datetime(players_df['birth_date']).dt.year

    for group_val, subdf in players_df.groupby(group_col):
        # Skip empty subgroups
        if len(subdf) == 0:
            continue
        
        # Calculate distances for this subset
        distances = calculate_distances(subdf, fields_df)
        avg_distances, best_field = find_optimal_field(distances)
        
        # Build a label for printing
        if label_prefix:
            # e.g. "birth year 2018"
            label = f"{label_prefix} {group_val}"
        else:
            # e.g. "U10" or "Kindergarten"
            label = str(group_val)
        
        print(f"{label} optimal field is {best_field} "
              f"with avg distance of {avg_distances[best_field]:.2f}")

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
FIELDS_FILE = 'distance_mapping/new_cleaned_fields_data.csv'
PROGRAM_FILES = [
    'distance_mapping/new_cleaned_2017_Players_Data.csv', 
    'distance_mapping/new_cleaned_PTA_fall.csv', 
    'distance_mapping/new_cleaned_rec_fall24.csv', 
    'distance_mapping/new_cleaned_travel_data_base.csv'
]

# Choose whether you want to group by birth_year or grade:
GROUP_BY = "birth_year"  
# or, for example:
# GROUP_BY = "grade"

# Read in fields data
fields_df = pd.read_csv(FIELDS_FILE)
fields_df['latitude'] = pd.to_numeric(fields_df['latitude'], errors='coerce')
fields_df['longitude'] = pd.to_numeric(fields_df['longitude'], errors='coerce')

for file_path in PROGRAM_FILES:
    print("\n" + "-"*60)
    print(f"Processing file: {file_path}")
    players_df = pd.read_csv(file_path)
    
    # Make sure lat/long are numeric
    players_df['latitude'] = pd.to_numeric(players_df['latitude'], errors='coerce')
    players_df['longitude'] = pd.to_numeric(players_df['longitude'], errors='coerce')
    
    # Check if there's a 'program' column
    if 'program' in players_df.columns:
        if GROUP_BY == "birth_year":
            print("Based on birth year *with* program:")
        else:
            print("Based on grade *with* program:")

        # 1) Group by the program
        for prog_val, prog_df in players_df.groupby('program'):
            if len(prog_df) == 0:
                continue
            distances = calculate_distances(prog_df, fields_df)
            avg_distances, best_field = find_optimal_field(distances)
            print(f"{prog_val} optimal field is {best_field} "
                  f"with avg distance of {avg_distances[best_field]:.2f}")

        # 2) Then group everyone by birth_year or grade (whichever is GROUP_BY)
        if GROUP_BY == "birth_year":
            group_and_print_optimal_fields(players_df, fields_df, 
                                           group_col='birth_year', 
                                           label_prefix='birth year')
        else:
            # GROUP_BY == 'grade'
            group_and_print_optimal_fields(players_df, fields_df, 
                                           group_col='grade',
                                           label_prefix=None)
    else:
        # No 'program' column in this file
        if GROUP_BY == "birth_year":
            print("No program at all (group everyone based on birth year):")
            group_and_print_optimal_fields(players_df, fields_df, 
                                           group_col='birth_year', 
                                           label_prefix='birth year')
        else:
            print("No program at all (group everyone based on grade):")
            group_and_print_optimal_fields(players_df, fields_df, 
                                           group_col='grade',
                                           label_prefix=None)
