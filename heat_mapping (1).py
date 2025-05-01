import pandas as pd
import folium
from flask import Flask, request, render_template
from folium import plugins
from folium.plugins import HeatMap

# Read in all datasets
travel_df = pd.read_csv("new_cleaned_travel_data_base.csv")
players_2017_df = pd.read_csv("new_cleaned_2017_Players_Data.csv")
rec_fall_24_df = pd.read_csv("new_cleaned_rec_fall24.csv")
fields_df = pd.read_csv("new_cleaned_fields_data.csv")
pta_df = pd.read_csv("new_cleaned_PTA_fall.csv")
adp_df = pd.read_csv("cleaned_ADPFallData.csv")

# Drop NA values for latitude / longitude only
travel_df = travel_df.dropna(subset=['latitude', 'longitude'])
players_2017_df = players_2017_df.dropna(subset=['latitude', 'longitude'])
rec_fall_24_df = rec_fall_24_df.dropna(subset=['latitude', 'longitude'])
fields_df = fields_df.dropna(subset=['latitude', 'longitude'])
pta_df = pta_df.dropna(subset=['latitude', 'longitude'])
adp_df = adp_df.dropna(subset=['latitude', 'longitude'])

# Combine all data into one large dataset
combined_df = pd.concat([travel_df, players_2017_df, rec_fall_24_df, fields_df, pta_df, adp_df])

# Convert latitude and longitude columns to float
combined_df['latitude'] = combined_df['latitude'].astype(float)
combined_df['longitude'] = combined_df['longitude'].astype(float)

# Export combined_df to csv
combined_df.to_csv('combined_dataset.csv', index=False)
from google.colab import files
files.download('combined_dataset.csv')

### Begin Heat Mapping & Filtering
app = Flask(__name__)

@app.route('/map', methods=['GET', 'POST'])
def generate_map():
    # Load combined dataset
    data = pd.read_csv('combined_dataset.csv')

    # Filter data based on request parameters
    filters = request.json.get('filters', [])
    if filters:
        data = data[data['category'].isin(filters)]

    # Create map with starting point and zoom level
    map = folium.Map(location=[38.893859, -77.0971477], zoom_start = 12)

    # Heat mapping for combined_df
    heatmap = [[row['latitude'], row['longitude']] for index, row in combined_df.iterrows()]

    HeatMap(heatmap).add_to(map)

    # Save map to HTML file
    map.save('templates/map.html')
    return {'success': True}