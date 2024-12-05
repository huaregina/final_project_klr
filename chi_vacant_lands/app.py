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
    ui.panel_title("Vacant Land Distribution and Socioeconomic Features in Chicago"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_select(
                "data_selection", 
                "Select Data:", 
                choices=["Crime Rate", "Income", "Unemployment", "Business Density", "Population"]
            ),
            ui.input_switch(
                id="toggle_scatter",
                label="Show Vacant Lands:",
                value=False  # Default state: off
            ),
            ui.input_slider(
                id="scatter_size",
                label="Adjust Point Size:",
                value=0.6,
                min=0.3,
                max=1
            ),
            ui.input_radio_buttons(
                "ownership_filter", 
                "Filter by Vacant Land Ownership:", 
                choices=["All", "City-Owned", "Non-City-Owned"], 
                selected="All"
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

    @reactive.Calc
    def filtered_layers():
        # Load scatter data
        df = pd.read_csv('./combined_data.csv')
        scatter_size = input.scatter_size()

        # Apply ownership filter
        ownership_filter = input.ownership_filter()

        city_owned_layer = alt.Chart(df[df['type'] == 'City-Owned']).mark_point(
            size=scatter_size, filled=True, color='purple'
        ).encode(
            longitude='longitude',
            latitude='latitude',
            tooltip=['latitude:Q', 'longitude:Q', 'chicago_community_area_name:N', 'zip_code:N']
        ).project(
            type='identity',
            reflectY=True
        )

        non_city_owned_layer = alt.Chart(df[df['type'] == 'Private']).mark_point(
            size=scatter_size, filled=True, color='green'
        ).encode(
            longitude='longitude',
            latitude='latitude',
            tooltip=['latitude:Q', 'longitude:Q', 'chicago_community_area_name:N', 'zip_code:N']
        ).project(
            type='identity',
            reflectY=True
        )

        if ownership_filter == "City-Owned":
            return city_owned_layer
        elif ownership_filter == "Non-City-Owned":
            return non_city_owned_layer
        else:  # All
            return non_city_owned_layer + city_owned_layer
        
    @render_altair
    def map():
        toggle_scatter = input.toggle_scatter()
        geojson_data, color_field, title = processed_data()

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

        # Add filtered layers
        filtered_layer = filtered_layers()

        # Combine scatter plot and choropleth based on toggle
        if toggle_scatter:
            layered_chart = choropleth + filtered_layer
        else:
            layered_chart = choropleth  # Only show choropleth

        return layered_chart

# App Initialization
app = App(app_ui, server)