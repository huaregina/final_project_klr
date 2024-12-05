from shiny import App, ui, render, reactive
import geopandas as gpd
import altair as alt
import pandas as pd
import json
from shinywidgets import render_altair, output_widget

# Disable the max rows limit for Altair
alt.data_transformers.disable_max_rows()

# UI Layout
app_ui = ui.page_fluid(
    ui.panel_title("Crime Rate Map Viewer"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select(
                "data_selection", "Select Data:", choices=["Crime Rate", "Income"]
            )
        )
    ),
    output_widget("map")     
)

# Server Logic
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
        return None, None, None

    @render_altair
    def map():
        geojson_data, color_field, title = processed_data()
        
        # load the scatter data
        df = pd.read_csv('./combined_data.csv')

        scatter = alt.Chart(df).mark_point(size=0.3, filled=True, color='blue').encode(
            longitude='longitude',
            latitude='latitude',
            tooltip=['latitude:Q', 'longitude:Q', 'chicago_community_area_name:N', 'zip_code:N' ]
            ).project(
                type='identity',
                reflectY=True
                ).properties(
                    title='Vacant Land Locations'
                    )

        # Create the base choropleth map
        choropleth = alt.Chart(alt.Data(values=geojson_data['features'])).mark_geoshape(
            stroke="black",
            strokeWidth=0.5
        ).encode(
            color=alt.Color(
                f"{color_field}:Q",  # Explicitly specify the type as quantitative
                scale=alt.Scale(range=["transparent", "red"]),
                title=title
            ),
            tooltip=[f"properties.zip:N", f"{color_field}:Q"]  # Explicitly specify types
        ).project(
            type='identity',
            reflectY=True
        ).properties(
            width=400,
            height=400
        )


        # layer the map and scatter plot
        layered_chart = scatter+ choropleth

        return layered_chart

# App Initialization
app = App(app_ui, server)