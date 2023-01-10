import dash, config, requests, urllib.parse
from dash import Dash, html, Input, Output, State, dash_table, callback, dcc
from dash.dependencies import ALL
import dash_bootstrap_components as dbc
from navbar import Navbar
import dash_leaflet as dl
from dash.exceptions import PreventUpdate
import pandas as pd
import matching, multipage.customer_layout as customer_layout, helper
import datetime
import math
from scheduler import SLOT_TIME
import random

dash.register_page(__name__)

# deals with auto complete input location
@callback(
    [Output("autocomplete_list","children"),
     Output("location_input","value")],
    [Input("location_input", "value"),
     Input({'type': 'autocomplete_list_item', 'index': ALL}, 'n_clicks')]
)
def update_location_text(place, chosen_item):
    ctx=dash.callback_context
    if not ctx.triggered:
        # if config.location is not None:
        #     return dash.no_update, config.location
        return dash.no_update, dash.no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id == "location_input":
        if(place is None or place.strip() == ""):
            return [], dash.no_update
        
        autocomplete_list=[]

        parsed_loc = urllib.parse.quote(place)
        response = requests.get("http://api.mapbox.com/geocoding/v5/mapbox.places/"+parsed_loc+".json?country=IN&access_token=pk.eyJ1IjoiaGFyc2hqaW5kYWwiLCJhIjoiY2tleW8wbnJlMGM4czJ4b2M0ZDNjeGN4ZyJ9.XXPg4AsUx0GUygvK8cxI6g")
        res=response.json()
        chosen_location=""
        cnt = 0
        for feat in res["features"]:
            autocomplete_list.append(dbc.ListGroupItem(feat["place_name"],id={'type': 'autocomplete_list_item','index': feat["place_name"]},action=True))
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
    Output('all_nodes','children'),
    Output('cs_nodes', 'children'),
    Output('circle', 'children'),
    Output('result_map', 'center'),
    Output('result_map', 'zoom'),
    Output('node_input', 'options'),
    Output('status_alert', 'children'),
    Output('status_alert', 'is_open'),
    Output('status_alert', 'color'),
    Input('all_nodes_button', 'n_clicks'),
    Input('sched_button', 'n_clicks'),
    State('node_input', 'value'),
    State('duration','value'),
    State('start_time','value'),
    State('end_time','value'),
    State('location_input', 'value'),
    State('radius_input', 'value'),
    State('no_of_cs_input', 'value'),
)
def hp_update_map(n_clicks, sched_clicks, req_nodeid, duration, stime, etime, location, radius, number_of_cs):

    alert_message=""; alert_open=False; alert_color = "primary"
    if config.GRAPH is None:
        fig, config.CENTER, config.ZOOM_LEVEL = helper.default_location()

    if n_clicks is None:
        return config.POSITIONS,config.CS_POSITIONS, config.POLYGON , config.CENTER, config.ZOOM_LEVEL, config.REQUESTS_DROPDOWN.to_dict('records'), alert_message, alert_open, alert_color
    
    fig, num_of_tot_nodes, config.GRAPH, A, config.X_NODES, config.Y_NODES, center, zoomLevel, latitude, longitude = helper.find_all_nodes(location, radius, number_of_cs)
    if n_clicks and n_clicks>config.N_CLICKS:
        if len(config.POLYGON)==0:
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

            req_node_content = [[f"Node #{i}",f"{i}"] for i in range(num_of_tot_nodes) if i not in config.CS_NODES]
            config.REQUESTS_DROPDOWN = pd.DataFrame(req_node_content,columns = ['label','value'])

            # setting the global variables in config file
            config.TOTAL_NODES, config.POSITIONS, config.REQUEST_NODES ,config.POLYGON, config.CENTER, config.ZOOM_LEVEL = num_of_tot_nodes, positions, reqpositions, polygon, center, zoomLevel, 

            requests_df['node'] = request_nodes

            config.COLUMNS = [{"name": i, "id": i} for i in requests_df.columns]

            dropdown_content = [[f"CS #{i}",f"{i}"] for i in config.CS_NODES]
            dropdown = pd.DataFrame(dropdown_content,columns = ['label','value'])
            config.CS_DROPDOWN = dropdown
            config.REQUESTS = requests_df

    if sched_clicks and sched_clicks>config.SCHED_CLICKS:
        new_idx = max(config.REQUESTS['index'])+1
        duration, stime, etime, req_nodeid = int(duration), int(stime), int(etime), int(req_nodeid)
        new_request = pd.DataFrame({
            "index": new_idx,
            "rcharge": 0,
			"duration": duration,
			"start_time": stime,
			"end_time": etime,
            "Available from": str(datetime.time(int(stime)//60, int(stime)%60)),
            "Available till": str(datetime.time(int(etime)//60, int(etime)%60)),
			"node": req_nodeid
        }, index=[0])
        
        config.REQUESTS = pd.concat([new_request, config.REQUESTS[:]]).drop_duplicates().reset_index(drop=True)

        config.REQUEST_NODES.append(dl.Marker(position=[config.Y_NODES[req_nodeid],config.X_NODES[req_nodeid]],children=dl.Tooltip(new_idx, direction='right', permanent=True),riseOnHover=True,icon={'iconUrl':'https://icon-library.com/images/marker-icon/marker-icon-12.jpg','iconSize':[40,40]}))
        config.NEAREST_CS[new_idx] = helper.get_nearest_cs_pq(config.X_NODES[req_nodeid], config.Y_NODES[req_nodeid])

        st = helper.roundup(stime)
        nslots = int(math.ceil(duration/SLOT_TIME))
        matching.reqSlots[new_idx]=nslots
        matchedSlots = []
        while st + duration <= etime:
            matchedSlots.append(int(st/SLOT_TIME))
            st+=SLOT_TIME

        flag=0
        while not config.NEAREST_CS[new_idx].empty():

            station = config.NEAREST_CS[new_idx].get()[1]
            if(matching.graphs.get(station)==None):
                matching.graphs[station]=dict()
            matching.graphs[station][new_idx] = matchedSlots
            if(config.REQUEST_MAPPING.get(station)==None):
                config.REQUEST_MAPPING[station]=[]
            config.REQUEST_MAPPING[station].append(new_idx)

            matching.used.clear()
            if(config.SLOT_MAPPING.get(station)==None): 
                config.SLOT_MAPPING[station]={}
            if(matching.kuhn(new_idx, 0, config.SLOT_MAPPING[station], station)):
                print(f"\n>>> REQUEST ACCEPTED! Accommodated in Station {station}")
                alert_message = f"Request Accepted -> Accommodated in Station {station}"
                alert_open = True; alert_color="success"
                matching.satisfied_requests+=1
                flag=1
                break
            else:
                config.REQUEST_MAPPING[station].remove(new_idx)
                del matching.graphs[station][new_idx]

        if(flag==0): 
            print("\n>>> REQUEST DENIED.")
            alert_message = "Request Denied :("; alert_open=True; alert_color="danger"

    
    return config.POSITIONS, config.CS_POSITIONS, config.POLYGON , config.CENTER, config.ZOOM_LEVEL, config.REQUESTS_DROPDOWN.to_dict('records'), alert_message, alert_open, alert_color


layout = dbc.Container([
	Navbar(),
    html.Br(),
    html.H1("Customer End", style={"text-align":"center"}),
    html.Br(),
    dbc.Row([
        dbc.Col(dl.Map(style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block"},
            center=[config.LOCATION.latitude, config.LOCATION.longitude],
            zoom=5,
            children=[
                dl.LayersControl(
               [dl.TileLayer()] +
                [
                dl.Overlay(dl.LayerGroup(id="all_nodes"), name="General Nodes", checked=False),
                # dl.Overlay(dl.LayerGroup(id="dl_er_req_nodes"), name="User Requests", checked=True),
                dl.Overlay(dl.LayerGroup(id="circle"), name="Search Area", checked=True),
                dl.Overlay(dl.LayerGroup(id="cs_nodes"), name="Charging Stations", checked=True),
                ]
              ) 
            ], id="result_map"), width=7),
        dbc.Col(customer_layout.all_nodes_form, width=5), 
    ]),
    html.Br(),
	dbc.Row([dbc.Col(customer_layout.new_request_form)]),
    dbc.Alert(id="status_alert", is_open=False)
])