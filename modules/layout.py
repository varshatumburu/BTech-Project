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
        dbc.Label("Choose charging station:", html_for="cs_display", width=4),
        dbc.Col(
            dcc.Dropdown(options=[{'label':'None','value':'None'}], value="", id="cs_input_dd"),
            width=4,
        ),
        dbc.Col(
            dbc.Spinner(children=[dbc.Button("Update ports", id="all_cs_button", color="primary")], size="sm", color="primary", id="cs_spinner"),
            width=4,
        )
    ], row = True
)

port_input_dropdown = dbc.FormGroup(
    [
        dbc.Label("Choose corresponding port:", html_for="port_display", width=4),
        dbc.Col(
            dcc.Dropdown(options=[{'label':'None','value':'None'}], value="", id="port_input_dd"),
            width=4,
        ),
        dbc.Col(
            dbc.Spinner(children=[dbc.Button("Find schedule", id="all_port_button", color="primary")], size="sm", color="primary", id="port_spinner"),
            width=4,
        )
    ], row = True
)

cs_schedule_form = dbc.Form([cs_input_dropdown, port_input_dropdown])

new_request_labels = dbc.FormGroup([
    dbc.Label("Select request location (Node ID)", html_for="nid", width=3),
    dbc.Label("Required charging time (in mins)", html_for="dur", width=3),
    dbc.Label("Enter start time of availability", html_for="stime", width=3),
    dbc.Label("Enter end time of availability", html_for="etime", width=3),
])

new_request_children = dbc.FormGroup(
    [
        dbc.Col(
            dcc.Dropdown(options=[{'label':'None','value':'None'}], value="", id="req_node_input"),
            width=3,
        ),
        dbc.Col(
            dbc.Input(type="number", id="duration_input", placeholder="duration",min=0, step=10, max=1440, value=10),
            width=3,
        ),
        dbc.Col(
            dbc.Input(type="number", id="start_time_input", placeholder="start time",min=0, step=10, max=1440, value=600),
            width=3,
        ),
        dbc.Col(
            dbc.Input(type="number", id="end_time_input", placeholder="end time",min=0, step=10, max=1440, value=700),
            width=3,
        ),
    ],
    row = True,
)

vehicle_details = dbc.FormGroup([        
        dbc.Label("Current SOC (in %):", html_for="current_soc", width=2),
        dbc.Col(
            dbc.Input(
                type="number", id="current_soc", placeholder="50%", min=0, step=1, max=100, value=10
            ),
            width=1,
        ),
        dbc.Label("Battery Capacity (in kWh):", html_for="battery_capacity", width=3),
        dbc.Col(
            dbc.Input(
                type="number", id="battery_capacity", placeholder="60", min=0, step=1, max=100, value=60
            ),
            width=1,
        ),
        dbc.Label("Mileage (in kms):", html_for="mileage", width=2),
        dbc.Col(
            dbc.Input(
                type="number", id="mileage", placeholder="300", min=0, step=1, max=1000, value=300
            ),
            width=1,
        ),
    ], 
    row=True,
)

vehicle_option = dbc.FormGroup([
        dbc.Label("Vehicle Type:", html_for="vehicle_type", width=2),
        dbc.Col(
            dcc.Dropdown(
                options=[ {'label':'2-wheeler','value':'2w'},
                          {'label':'3-wheeler','value':'3w'},
                          {'label':'4-wheeler','value':'4w'} ],
                value='4w', 
                id='vehicle_type'), width = 3
        ),
        dbc.Col(
            dbc.Spinner(children=[dbc.Button("Schedule", id="schedule_button", color="primary")], size="sm", color="primary", id="spinner3"),
            width=4,
        )
    ], 
    row = True,
)


new_request_form = dbc.Form([new_request_labels, new_request_children, vehicle_details, vehicle_option])