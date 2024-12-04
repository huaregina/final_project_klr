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
    ui.panel_title("Vacant Lands and Community Characteristics"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select("data_selection", "Select Data:", choices=dropdown_options),
        ),
        ui.output_plot("combined_map"),
    ),
)

# Server logic
def server(input, output, session):
    @reactive.Calc
    def processed_data():
        selected_data = input.data_selection()
        if selected_data == "Crime Rate":
            # Process crime rate data
            gdf_crime = gpd.read_file('Crime Data/crime_data.shp')
            crime_count_zip = gdf_crime.groupby('zip').size().reset_index(name='crime_count')
            df_crime_rate = crime_count_zip.merge(
                df_pop_2021[['zip', 'total_population']], on='zip', how='left'
            )
            df_crime_rate['crime_rate'] = (
                df_crime_rate['crime_count'] / df_crime_rate['total_population'] * 1000
            ).fillna(0)
            gdf_combined = gdf1.merge(df_crime_rate, on='zip', how='left')
            gdf_combined['crime_rate_windsorized'] = winsorize(
                gdf_combined['crime_rate'], limits=(0.01, 0.96)
            )
            return gdf_combined, "crime_rate_windsorized", "Crime Rate (per 1,000)"
        elif selected_data == "Income Level":
            gdf_income = gpd.read_file('Income/income_data.shp')
            return gdf_income, "properties.INCOME", "Per Capita Income"
        elif selected_data == "Unemployment Rate":
            gdf_unemployment = gpd.read_file('Unemployment/unemployment_data.shp')
            return gdf_unemployment, "properties.UNEMPLOYME", "Unemployment Rate"
        elif selected_data == "Population":
            gdf_population = gdf1.merge(df_pop_2021, on='zip', how='left')
            return gdf_population, "total_population", "Population"

    @render_altair
    def combined_map():
        gdf_combined, color_field, title = processed_data()
        base_map = alt.Chart(
            alt.Data(values=json.loads(gdf_combined.to_crs(epsg=4326).to_json())["features"])
        ).mark_geoshape(
            stroke="white", strokeWidth=0.5
        ).encode(
            color=alt.Color(color_field + ":Q", scale=alt.Scale(scheme="bluegreen"), title=title),
            tooltip=["zip:N", color_field + ":Q"],
        ).project(
            type="identity"
        ).properties(
            width=600, height=400
        )
        scatter = alt.Chart(df).mark_point(size=3, color="red").encode(
            longitude="longitude:Q", latitude="latitude:Q"
        )
        return base_map + scatter

    output.combined_map = combined_map


# App
app = App(app_ui, server)
