from shiny import App, ui, render, reactive
from shinywidgets import render_altair
import pandas as pd
import geopandas as gpd
import altair as alt
import json
from scipy.stats.mstats import winsorize

# Disable the max rows limit for Altair
alt.data_transformers.disable_max_rows()

# Load data
df = pd.read_csv('./combined_data.csv')
df_pop_2021 = pd.read_csv('./df_pop_2021.csv')
gdf1 = gpd.read_file('ZIP Codes/geo_export.shp')

# Preprocess shapefile data
gdf1['zip'] = gdf1['zip'].astype(str).str.zfill(5)

# Dropdown options
dropdown_options = [
    "Crime Rate",
    "Income Level",
    "Unemployment Rate",
    "Population",
]

# UI Layout
app_ui = ui.page_fluid(
    ui.panel_title("Vacant Land Distribution and Socioeconomic Features in Chicago"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select(
                "data_selection", "Select Data:", choices=["Crime Rate", "Income", "Unemployment", "Business Density", "Population"]
            )
        )
    ),
)

# Server logic
def server(input, output, session):
    @reactive.Calc
    def processed_data():
        selected_data = input.data_selection()
        if selected_data == "Crime Rate":
            # Load the crime rate GeoJSON
            with open('crime_rate_data.geojson') as f:
                geojson_data = json.load(f)
            return geojson_data, "properties.crime_rate_windsorized", "Crime rate per 1,000 population"
        elif selected_data == "Income":
            # Load the income GeoJSON
            with open('income_data.geojson') as f:
                geojson_data = json.load(f)
            return geojson_data, "properties.INCOME", "Per Capita Income"
        elif selected_data == "Unemployment":
            # Load the income GeoJSON
            with open('income_data.geojson') as f:
                geojson_data = json.load(f)
            return geojson_data, "properties.UNEMPLOYMENT", "Unemployment Rate"
        elif selected_data == "Business Density":
            # Load the income GeoJSON
            with open('business_data.geojson') as f:
                geojson_data = json.load(f)
            return geojson_data, "properties.business_density", "Business Denisty"
        elif selected_data == "Population":
            # Load the income GeoJSON
            with open('population_data.geojson') as f:
                geojson_data = json.load(f)
            return geojson_data, "properties.total_population", "Population"
        return None, None, None

    @render_altair
    def combined_map():
        gdf_combined, color_field, title = processed_data()
        # Convert GeoDataFrame to GeoJSON
        geojson_data = json.loads(gdf_combined.to_crs(epsg=4326).to_json())["features"]

        # Create Base Map
        base_map = alt.Chart(alt.Data(values=geojson_data)).mark_geoshape(
            stroke="white", strokeWidth=0.5
        ).encode(
            color=alt.Color(color_field + ":Q", scale=alt.Scale(scheme="bluegreen"), title=title),
            tooltip=["zip:N", color_field + ":Q"],
        ).project(
            type="identity"
        ).properties(
            width=600, height=400
        )

        # Overlay Scatter Plot for Vacant Lots
        scatter = alt.Chart(df).mark_point(size=3, color="red").encode(
            longitude="longitude:Q", latitude="latitude:Q"
        )
        return base_map + scatter

    output.combined_map = combined_map


# App
app = App(app_ui, server)
