import dash_bootstrap_components as dbc
from dash import dcc

location_input = dbc.FormGroup(
    [
        dbc.Label("Search Area", html_for="location", width=4),
        dbc.Col(
            dbc.Input(
                type="text", id="er_location_input", placeholder="Enter a valid location",value="Patna, Bihar, India",debounce=False
            ),
            width=8,
        ),
    ],
    row=True,
    id="er_location_input_form"
)

# autocomplete list
autocomplete_list_ecorouting = dbc.Row(
    [
         dbc.Col(width=4),
         dbc.Col(
            dbc.ListGroup(
            [],
            id="er_autocomplete_list",
            style={"margin-bottom":"8px"}
            ),
            width=8
        )
    ]
)

# radius input
radius_input = dbc.FormGroup(
    [
        dbc.Label("Radius (m)", html_for="radius", width=4),
        dbc.Col(
            dbc.Input(
                type="number", id="er_radius_input", placeholder="Enter Radius between [500,8000] meters",min=100, step=1,max=8000, value=500
            ),
            width=8,
        ),
    ],
    row=True,
    id="er_radius_input_form"
)

# total cs input
total_number_cs = dbc.FormGroup(
    [
        dbc.Label("Number of CS:", html_for="no_of_cs", width=4),
        dbc.Col(
            dbc.Input(
                type="number", id="er_no_of_cs_input", placeholder="Enter total no of cs",min=1, step=1,max=50, value=10
            ),
            width=8,
        ),
    ],
    row=True,
)

all_nodes_button = dbc.Spinner(children=[dbc.Button("Find All Nodes",id="er_all_nodes_button",color="primary")],size="sm", color="primary",id="spinner1")

all_nodes_form = dbc.Form([location_input,autocomplete_list_ecorouting, radius_input, total_number_cs, all_nodes_button])

# cs dropdown list
cs_input_dropdown = dbc.FormGroup(
    [
        dbc.Label("Display Schedule for Charging Station:", html_for="no_of_cs", width=4),
        dbc.Col(
            dcc.Dropdown(options=[{'label':'None','value':'None'}], value="", id="cs_input_dd"),
            width=4,
        ),
        dbc.Col(
            dbc.Spinner(children=[dbc.Button("Search", id="all_cs_button", color="primary")], size="sm", color="primary", id="spinner2"),
            width=4,
        )
    ],
    row=True,
)

cs_schedule_form = dbc.Form([cs_input_dropdown])

new_request_labels = dbc.FormGroup([
    dbc.Label("Select request location (Node ID)", html_for="nid", width=3),
    dbc.Label("Required charging time (in mins)", html_for="dur", width=2),
    dbc.Label("Enter start time of availability", html_for="stime", width=2),
    dbc.Label("Enter end time of availability", html_for="etime", width=2),
])

new_request_children = dbc.FormGroup(
    [
        dbc.Col(
            dcc.Dropdown(options=[{'label':'None','value':'None'}], value="", id="req_node_input"),
            width=3,
        ),
        dbc.Col(
            dbc.Input(type="number", id="duration_input", placeholder="duration",min=0, step=10, max=1440, value=10),
            width=2,
        ),
        dbc.Col(
            dbc.Input(type="number", id="start_time_input", placeholder="start time",min=0, step=10, max=1440, value=600),
            width=2,
        ),
        dbc.Col(
            dbc.Input(type="number", id="end_time_input", placeholder="end time",min=0, step=10, max=1440, value=700),
            width=2,
        ),
        dbc.Col(
            dbc.Spinner(children=[dbc.Button("Schedule", id="schedule_button", color="primary")], size="sm", color="primary", id="spinner3"),
            width=3,
        )
    ],
    row = True,
)
new_request_form = dbc.Form([new_request_labels,new_request_children])
