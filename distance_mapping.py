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


#
# NEW FUNCTION: easily called from your Streamlit front end to get the best field
#
def find_optimal_field_for_data(players_df, fields_df):
    """
    Given already-filtered DataFrames of players and fields (with columns
    'Latitude'/'Longitude'), compute the single best field (lowest average distance).
    
    Returns:
        (best_field_name, avg_distance_for_that_field)
        If no players or fields exist, returns (None, None).
    """

    # If either dataframe is empty, return no result
    if players_df.empty or fields_df.empty:
        return None, None
    
    # Copy so as not to mutate original
    p_df = players_df.copy()
    f_df = fields_df.copy()
    
    # Rename columns so the distance logic works
    # (calculate_distances expects 'latitude' and 'longitude')
    p_df.rename(columns={"Latitude": "latitude", "Longitude": "longitude"}, inplace=True)
    f_df.rename(columns={"Latitude": "latitude", "Longitude": "longitude"}, inplace=True)
    
    # Drop any rows missing lat/long
    p_df.dropna(subset=["latitude","longitude"], inplace=True)
    f_df.dropna(subset=["latitude","longitude"], inplace=True)
    
    # If still empty after dropping NAs
    if p_df.empty or f_df.empty:
        return None, None
    
    distances = calculate_distances(p_df, f_df)
    avg_distances, best_field = find_optimal_field(distances)
    return best_field, avg_distances[best_field]

'''
# ------------------------------------------------------------------------------
# (Optional) COMMENT OUT OR KEEP FOR LOCAL TESTING:
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Example usage / local test with existing files:

    FIELDS_FILE = 'distance_mapping/new_cleaned_fields_data.csv'
    PROGRAM_FILES = [
        'distance_mapping/new_cleaned_2017_Players_Data.csv', 
        'distance_mapping/new_cleaned_PTA_fall.csv', 
        'distance_mapping/new_cleaned_rec_fall24.csv', 
        'distance_mapping/new_cleaned_travel_data_base.csv'
    ]

    fields_df = pd.read_csv(FIELDS_FILE)
    for file_path in PROGRAM_FILES:
        print("\n" + "-"*60)
        print(f"Processing file: {file_path}")
        players_df = pd.read_csv(file_path)

        # Just showing how you'd call the new function:
        best_field, dist_val = find_optimal_field_for_data(players_df, fields_df)
        if best_field:
            print(f"Overall best field is '{best_field}' with avg dist of {dist_val:.2f} miles")
        else:
            print("No best field found (either no players or no fields).")

    # You can also still use the older grouping approach below, if needed:
    # GROUP_BY = "birth_year"
    # group_and_print_optimal_fields(players_df, fields_df, group_col=GROUP_BY, label_prefix='birth year')
'''

