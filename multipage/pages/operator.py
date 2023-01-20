import dash, requests, urllib.parse
from dash import Dash, html, Input, Output, State, dash_table, callback, dcc
from dash.dependencies import ALL
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash.exceptions import PreventUpdate
import pandas as pd
import datetime
import random, sys

sys.path.insert(1, '/home/varsha_1901cs69/btp/scheduling/modules')
import layout as operator_layout, helper
from navbar import Navbar
from scheduler import SLOT_TIME

sys.path.insert(2, '/home/varsha_1901cs69/btp/scheduling')
import config


# deals with auto complete input location
@callback(
    [Output("er_autocomplete_list","children"),
     Output("er_location_input","value")],
    [Input("er_location_input", "value"),
     Input({'type': 'er_autocomplete_list_item', 'index': ALL}, 'n_clicks')]
)
def update_location_text(place, chosen_item):
    ctx=dash.callback_context
    if not ctx.triggered:
        # if config.location is not None:
        #     return dash.no_update, config.location
        return dash.no_update, dash.no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id == "er_location_input":
        if(place is None or place.strip() == ""):
            return [], dash.no_update
        
        autocomplete_list=[]

        parsed_loc = urllib.parse.quote(place)
        response = requests.get("http://api.mapbox.com/geocoding/v5/mapbox.places/"+parsed_loc+".json?country=IN&access_token=pk.eyJ1IjoiaGFyc2hqaW5kYWwiLCJhIjoiY2tleW8wbnJlMGM4czJ4b2M0ZDNjeGN4ZyJ9.XXPg4AsUx0GUygvK8cxI6g")
        res=response.json()
        chosen_location=""
        cnt = 0
        for feat in res["features"]:
            autocomplete_list.append(dbc.ListGroupItem(feat["place_name"],id={'type': 'er_autocomplete_list_item','index': feat["place_name"]},action=True))
            cnt = cnt + 1
            if chosen_location == "":
                chosen_location=feat["place_name"]
        return autocomplete_list, dash.no_update
    else:
        loc=eval(ctx.triggered[0]['prop_id'].split('.')[0])['index']
        config.LOCATION = loc
        return [], loc

# Callback dealing with intial inputs(area and radius) and output(all nodes and polygon around the search space)
@callback(
    Output('dl_er_all_nodes','children'),
    Output('dl_er_req_nodes','children'),
    Output('dl_er_cs_nodes', 'children'),
    Output('dl_er_circle', 'children'),
    Output('er_result_map', 'center'),
    Output('er_result_map', 'zoom'),
    Output('req_tbl','data'),
    Output('req_tbl', 'columns'),
    Output('cs_input_dd','options'),
    Input('er_all_nodes_button', 'n_clicks'),
    State('er_location_input', 'value'),
    State('er_radius_input', 'value'),
    State('er_no_of_cs_input', 'value'),
)
def hp_update_map(n_clicks, location, radius, number_of_cs):

    if config.GRAPH is None:
        fig, config.CENTER, config.ZOOM_LEVEL = helper.default_location()

    if n_clicks is None:
        return config.POSITIONS,config.REQUEST_NODES,config.CS_POSITIONS, config.POLYGON , config.CENTER, config.ZOOM_LEVEL, config.REQUESTS.to_dict('records'), config.COLUMNS, config.CS_DROPDOWN.to_dict('records')
    fig, num_of_tot_nodes, config.GRAPH, A, config.X_NODES, config.Y_NODES, center, zoomLevel, latitude, longitude = helper.find_all_nodes(location, radius, number_of_cs)
    if n_clicks and n_clicks>config.N_CLICKS:
        requests_df = pd.read_json(config.DATASET)
        config.N_CLICKS = n_clicks
        testcases = []
        corners = []
        for x in range(0,361,1):
            testcases.append((latitude,longitude,x,(radius+350)/1000))
        
        for lat1, lon1, bear, dist in testcases:
            (lat,lon) = helper.pointRadialDistance(lat1,lon1,bear,dist)
            corners.append([lat,lon])
        polygon = dl.Polygon(positions=corners)

        # info related to cs
        config.TOTAL_STATIONS = number_of_cs
        config.CS_NODES = random.sample(range(0,num_of_tot_nodes),number_of_cs)

        request_nodes = random.choices([i for i in range(0,num_of_tot_nodes) if i not in config.CS_NODES],k=requests_df.shape[0])
        reqpositions = []; positions = []
        for i in range(len(config.X_NODES)):
            positions.append(dl.Marker(position=[config.Y_NODES[i],config.X_NODES[i]],children=dl.Tooltip(i, direction='top', permanent=True),riseOnHover=True))

        for idx, nodeid in enumerate(request_nodes):
            y=config.Y_NODES[nodeid]; x=config.X_NODES[nodeid]
            request_index = requests_df.loc[requests_df.index[idx],'index']
            reqpositions.append(dl.Marker(position=[y,x],children=dl.Tooltip(request_index, direction='right', permanent=True),riseOnHover=True,icon={'iconUrl':'https://icon-library.com/images/marker-icon/marker-icon-12.jpg','iconSize':[40,40]}))
            config.NEAREST_CS[request_index]=helper.get_nearest_cs_pq(x,y)

        config.REQUEST_MAPPING = helper.mapRequests2Stations(len(requests_df),config.NEAREST_CS)
        blocked=set(); leftover=[]
        helper.iterative_scheduling(len(requests_df),blocked,leftover,config.REQUEST_MAPPING,config.NEAREST_CS)

        config.CS_POSITIONS = [dl.Marker(position=[config.Y_NODES[i],config.X_NODES[i]],children=dl.Tooltip(i, direction='top', permanent=True),\
            riseOnHover=True,icon={'iconUrl':'https://icon-library.com/images/station-icon/station-icon-14.jpg','iconSize':[30,40]}) \
                for i in config.CS_NODES]


        # setting the global variables in config file
        config.TOTAL_NODES, config.POSITIONS, config.REQUEST_NODES ,config.POLYGON, config.CENTER, config.ZOOM_LEVEL = num_of_tot_nodes, positions, reqpositions, polygon, center, zoomLevel, 

        requests_df['node'] = request_nodes

        config.COLUMNS = [{"name": i, "id": i} for i in requests_df.columns]

        dropdown_content = [[f"CS #{i}",f"{i}"] for i in config.CS_NODES]
        dropdown = pd.DataFrame(dropdown_content,columns = ['label','value'])
        config.CS_DROPDOWN = dropdown
        config.REQUESTS = requests_df

    return config.POSITIONS,config.REQUEST_NODES,config.CS_POSITIONS, config.POLYGON , config.CENTER, config.ZOOM_LEVEL, config.REQUESTS.to_dict('records'), config.COLUMNS, config.CS_DROPDOWN.to_dict('records')


@callback(
    Output('cs_schedule','data'),
    Output('cs_schedule','columns'),
    Input('all_cs_button','n_clicks'),
    State('cs_input_dd','value')
)
def show_schedule(n_clicks, cs_input):
    if n_clicks is None:
        raise PreventUpdate
    
    if config.SLOT_MAPPING.get(int(cs_input))==None:
        return [],[]

    check=[]; table_data=[]
    for key in config.SLOT_MAPPING[int(cs_input)].keys():
        dup = config.SLOT_MAPPING[int(cs_input)]
        if(dup[key] in check): continue
        check.append(dup[key])
        dur = config.REQUESTS.loc[config.REQUESTS['index']==dup[key], 'duration'].iloc[0]
        time = datetime.time(int(key*SLOT_TIME)//60, int(key*SLOT_TIME)%60)
        table_data.append([dup[key],time,dur])

    schedule = pd.DataFrame(table_data, columns=['Request Index','Time','Duration (in mins)'])
    schedule = schedule.sort_values(by=['Time'])
    cols = [{"name": i, "id": i} for i in schedule.columns]
    return schedule.to_dict("records"), cols

layout = dbc.Container([
	Navbar(),
    html.Br(),
    html.H1("Operator End", style={"text-align":"center"}),
    html.Br(),
    dbc.Row([
        dbc.Col(dl.Map(style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block"},
            center=[config.LOCATION.latitude, config.LOCATION.longitude],
            zoom=5,
            children=[
                dl.LayersControl(
               [dl.TileLayer()] +
                [
                dl.Overlay(dl.LayerGroup(id="dl_er_all_nodes"), name="General Nodes", checked=False),
                dl.Overlay(dl.LayerGroup(id="dl_er_req_nodes"), name="User Requests", checked=True),
                dl.Overlay(dl.LayerGroup(id="dl_er_circle"), name="Search Area", checked=True),
                dl.Overlay(dl.LayerGroup(id="dl_er_cs_nodes"), name="Charging Stations", checked=True),
                ]
              ) 
            ], id="er_result_map"), width=7),
        dbc.Col(operator_layout.all_nodes_form, width=5), 
    ]),
    html.Br(),
    html.H3("Existing Requests"),
    html.Div([
        dash_table.DataTable(
        data=config.REQUESTS.to_dict("records"), 
        columns=[], 
        id="req_tbl",
        style_as_list_view=True,
        style_cell={'textAlign': 'center'},
        style_header={'backgroundColor': 'white','fontWeight': 'bold'}, 
        page_size=5)
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col(operator_layout.cs_schedule_form),
    ]),
    html.Div([
        dash_table.DataTable(
            data=[],
            columns=[],
            id="cs_schedule",
            style_as_list_view=True,
            style_cell={'textAlign': 'center'},
            style_header={'backgroundColor': 'white','fontWeight': 'bold'}
        )
    ]),
])