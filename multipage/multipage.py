from dash import Dash, dcc, html, Input, Output, callback, dash_table, State
import main, config, helper, layout, matching
from navbar import Navbar
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import dash
from dash.exceptions import PreventUpdate
import pandas as pd
import datetime
import math
from scheduler import SLOT_TIME
import random

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.COSMO], use_pages=True)

app.layout = html.Div([
	html.H1('Multi-page app with Dash Pages', style={"text-align":"center"}),

    dbc.Row(
        [
            dbc.Col(
                dcc.Link(
                    f"{page['name']} - {page['path']}", href=page["relative_path"]
                ), style={"text-align":"center"}
            )
            for page in dash.page_registry.values()
        ],
    ),

	dash.page_container
])


index_page = html.Div([
    dcc.Link('Visit operator page', href='/operator', style={"align":"center"}),
    html.Br(),
    dcc.Link('Visit customer page', href='/customer'),
])


@callback(Output('operator-content', 'children'),
              [Input('page-1-dropdown', 'value')])
def page_1_dropdown(value):
    return f'You have selected {value}'


customer_layout = html.Div([
    html.H1('Customer'),
    dcc.RadioItems(['Orange', 'Blue', 'Red'], 'Orange', id='page-2-radios'),
    html.Div(id='customer-content'),
    html.Br(),
    dcc.Link('Go to Operator', href='/operator'),
    html.Br(),
    dcc.Link('Go back to home', href='/')
])

@callback(Output('customer-content', 'children'),
              [Input('page-2-radios', 'value')])
def page_2_radios(value):
    return f'You have selected {value}'


# Update the index
@callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/operator':
        return main.operator_layout
    elif pathname == '/customer':
        return main.app.layout
    else:
        return index_page
    # You could also return a 404 "URL not found" page here

if __name__ == '__main__':
    app.run_server(debug=True)