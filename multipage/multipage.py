from dash import Dash, dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
from pages import customer, operator

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.COSMO], use_pages=True)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
	html.H1('Multi-page app with Dash Pages', style={"text-align":"center"}),

    dbc.Row(
        [
            dbc.Col(
                dcc.Link(
                    "=>Customer Page", href='/customer'
                ), style={"text-align":"center"}
            ),
            dbc.Col(
                dcc.Link(
                    "=>Operator Page", href='/operator'
                ), style={"text-align":"center"}
            )
        ],
    ),

	html.Div(id='page-content')
])


index_page = html.Div([
    html.H5("Welcome!")
])


# Update the index
@callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/operator':
        return operator.layout
    elif pathname == '/customer':
        return customer.layout
    else:
        return index_page
    # You could also return a 404 "URL not found" page here

if __name__ == '__main__':
    app.run_server(debug=True)