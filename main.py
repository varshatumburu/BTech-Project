import dash, config as config, requests, urllib.parse
from dash import Dash, html, Input, Output, State, dash_table
from dash.dependencies import ALL
import dash_bootstrap_components as dbc
from modules.navbar import Navbar
import dash_leaflet as dl
from dash.exceptions import PreventUpdate
import pandas as pd
import modules.matching as matching, modules.layout as layout, modules.helper as helper
import datetime
import math
from modules.scheduler import SLOT_TIME
import random
import json
import sys, os

app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

# deals with auto complete input location
@app.callback(
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
@app.callback(
    Output('dl_er_all_nodes','children'),
    Output('dl_er_req_nodes','children'),
    Output('dl_er_cs_nodes', 'children'),
    Output('dl_er_circle', 'children'),
    Output('2w_cs_ports', 'children'),
    Output('3w_cs_ports', 'children'),
    Output('4w_cs_ports', 'children'),
    Output('er_result_map', 'center'),
    Output('er_result_map', 'zoom'),
    Output('req_tbl','data'),
    Output('req_tbl', 'columns'),
    Output('cs_input_dd','options'),
    Output('req_node_input', 'options'),
    Output('schedule_alert', 'children'),
    Output('schedule_alert', 'is_open'),
    Output('schedule_alert', 'color'),
    Input('er_all_nodes_button', 'n_clicks'),
    Input('schedule_button', 'n_clicks'),
    State('req_node_input', 'value'),
    State('start_time_input','value'),
    State('end_time_input','value'),
    State('current_soc','value'),
    State('battery_capacity','value'),
    State('mileage','value'),
    State('vehicle_type','value'),
    State('er_location_input', 'value'),
    State('er_radius_input', 'value'),
    State('er_no_of_cs_input', 'value'),
)
def hp_update_map(n_clicks, sched_clicks, req_nodeid, stime, etime, current_soc, bcap, mileage, vehicle_type, location, radius, number_of_cs):

    alert_message=""; alert_open=False; alert_color = "primary"
    if config.GRAPH is None:
        fig, config.CENTER, config.ZOOM_LEVEL = helper.default_location()

    if n_clicks is None:
        return config.POSITIONS,config.REQUEST_NODES,config.CS_POSITIONS, config.POLYGON, config.W2_PORTS, config.W3_PORTS, config.W4_PORTS, config.CENTER, config.ZOOM_LEVEL, config.REQUESTS.to_dict('records'), config.COLUMNS, config.CS_DROPDOWN.to_dict('records'), config.REQUESTS_DROPDOWN.to_dict('records'), alert_message, alert_open, alert_color
    
    fig, num_of_tot_nodes, config.GRAPH, A, config.X_NODES, config.Y_NODES, center, zoomLevel, latitude, longitude = helper.find_all_nodes(location, radius, number_of_cs)
    if n_clicks and n_clicks>config.N_CLICKS:
        # cs_generator.write_scripts(number_of_cs)
        requests_df = pd.read_json(os.path.join(sys.path[0], 'datasets')+"/base_requests.json")
        stations_df = pd.read_json(os.path.join(sys.path[0], 'datasets')+"/charging_stations.json")
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
        stations_df['node']=config.CS_NODES
        config.CHARGING_STATIONS = stations_df
        config.REQUESTS = requests_df

        # Plot all nodes on map
        positions = []
        for i in range(len(config.X_NODES)):
            positions.append(dl.Marker(position=[config.Y_NODES[i],config.X_NODES[i]],children=dl.Tooltip(i, direction='top', permanent=True),riseOnHover=True))

        # Plot request nodes on map
        request_nodes = random.choices([i for i in range(0,num_of_tot_nodes) if i not in config.CS_NODES],k=requests_df.shape[0])
        requests_df['node'] = request_nodes
        config.REQUESTS = requests_df
        reqpositions = []; 
        for idx, nodeid in enumerate(request_nodes):
            y=config.Y_NODES[nodeid]; x=config.X_NODES[nodeid]
            request_index = requests_df.loc[requests_df.index[idx],'index']
            reqpositions.append(dl.Marker(position=[y,x],children=dl.Tooltip(request_index, direction='right', permanent=True),riseOnHover=True,icon={'iconUrl':'https://icon-library.com/images/marker-icon/marker-icon-12.jpg','iconSize':[40,40]}))
            # SOC restriction
            md = requests_df.loc[requests_df.index[idx],'current_soc']*requests_df.loc[requests_df.index[idx],'mileage']*10
            config.NEAREST_CS[request_index] = helper.get_nearest_cs_pq(x,y,md)
            config.NEAREST_PORTS[request_index] = helper.get_nearest_ports_pq(requests_df.to_dict("records")[request_index], config.NEAREST_CS[request_index])

        # print("request nodes plotted")
        config.REQUEST_MAPPING = helper.mapRequests2Ports(len(requests_df),config.NEAREST_PORTS)
        blocked=set(); leftover=[]
        helper.iterative_scheduling(len(requests_df),blocked,leftover,config.REQUEST_MAPPING,config.NEAREST_PORTS, offline=1)

        # Plot charging stations on map
        config.CS_POSITIONS = [dl.Marker(position=[config.Y_NODES[node],config.X_NODES[node]],children=dl.Tooltip(idx, direction='top', permanent=True),\
            riseOnHover=True,icon={'iconUrl':'https://icon-library.com/images/station-icon/station-icon-14.jpg','iconSize':[30,40]}) \
                for idx, node in enumerate(config.CS_NODES)]
        
        w4_ports = []; w3_ports=[]; w2_ports=[]
        stations = stations_df.to_dict("records")
        for station in stations:
            exclusive_ports = list(set([vt for p in station["ports"] for vt in p["vehicles"]]))
            if "4w" in exclusive_ports: w4_ports.append(station["node"])
            if "3w" in exclusive_ports: w3_ports.append(station["node"])
            if "2w" in exclusive_ports: w2_ports.append(station["node"])
            
        json_object = json.dumps(config.SLOT_MAPPING, indent=4)
        with open("datasets/slot_mapping.json","w") as f:
            f.write(json_object)
            
        config.W4_PORTS = [dl.Marker(position=[config.Y_NODES[id],config.X_NODES[id]],children=dl.Tooltip([idx for idx,f in enumerate(stations) if f["node"]==id][0], direction='top', permanent=True),\
            riseOnHover=True,icon={'iconUrl':'https://icon-library.com/images/free-map-pin-icon/free-map-pin-icon-6.jpg','iconSize':[30,30]}) for id in w4_ports]
        
        config.W3_PORTS = [dl.Marker(position=[config.Y_NODES[id],config.X_NODES[id]],children=dl.Tooltip([idx for idx,f in enumerate(stations) if f["node"]==id][0], direction='top', permanent=True),\
            riseOnHover=True,icon={'iconUrl':'https://icon-library.com/images/free-map-pin-icon/free-map-pin-icon-6.jpg','iconSize':[30,30]}) for id in w3_ports]
        
        config.W2_PORTS = [dl.Marker(position=[config.Y_NODES[id],config.X_NODES[id]],children=dl.Tooltip([idx for idx,f in enumerate(stations) if f["node"]==id][0], direction='top', permanent=True),\
            riseOnHover=True,icon={'iconUrl':'https://icon-library.com/images/free-map-pin-icon/free-map-pin-icon-6.jpg','iconSize':[30,30]}) for id in w2_ports]

        # print("station nodes plotted")
        req_node_content = [[f"Node #{i}",f"{i}"] for i in range(num_of_tot_nodes) if i not in config.CS_NODES]
        config.REQUESTS_DROPDOWN = pd.DataFrame(req_node_content,columns = ['label','value'])

        # setting the global variables in config file
        config.TOTAL_NODES, config.POSITIONS, config.REQUEST_NODES ,config.POLYGON, config.CENTER, config.ZOOM_LEVEL = num_of_tot_nodes, positions, reqpositions, polygon, center, zoomLevel

        config.COLUMNS = [{"name": i, "id": i} for i in requests_df.columns]

        dropdown_content = [[f"CS #{i}",f"{i}"] for i in range(len(config.CS_NODES))]
        dropdown = pd.DataFrame(dropdown_content,columns = ['label','value'])
        config.CS_DROPDOWN = dropdown
        
    if sched_clicks and sched_clicks>config.SCHED_CLICKS:
        config.SCHED_CLICKS = sched_clicks
        new_idx = max(config.REQUESTS['index'])+1
        stime, etime, req_nodeid, current_soc, bcap, mileage = int(stime), int(etime), int(req_nodeid), int(current_soc), int(bcap), int(mileage)
        new_request = pd.DataFrame(data={
            "index": new_idx,
            "rcharge": 0,
			"start_time": stime,
			"end_time": etime,
            "Available from": str(datetime.time(int(stime)//60, int(stime)%60)),
            "Available till": str(datetime.time(int(etime)//60, int(etime)%60)),
			"node": req_nodeid,
            "current_soc": current_soc,
            "battery_capacity": bcap,
            "mileage": mileage,
            "vehicle_type": vehicle_type
        }, index=[0])
        
        config.REQUESTS = pd.concat([new_request, config.REQUESTS[:]]).drop_duplicates().reset_index(drop=True)
        config.REQUESTS.to_json('datasets/requests.json', orient="records", indent=4)
        
        config.REQUEST_NODES.append(dl.Marker(position=[config.Y_NODES[req_nodeid],config.X_NODES[req_nodeid]],children=dl.Tooltip(new_idx, direction='right', permanent=True),riseOnHover=True,icon={'iconUrl':'https://icon-library.com/images/marker-icon/marker-icon-12.jpg','iconSize':[40,40]}))
        config.NEAREST_CS[new_idx] = helper.get_nearest_cs_pq(config.X_NODES[req_nodeid], config.Y_NODES[req_nodeid], current_soc*mileage*10)
        config.NEAREST_PORTS[new_idx] = helper.get_nearest_ports_pq(new_request.to_dict('index')[0], config.NEAREST_CS[new_idx])

        flag=0
        while not config.NEAREST_PORTS[new_idx].empty():
            port_id = config.NEAREST_PORTS[new_idx].get()
            # print(port_id)

            csno = int(port_id.split('p')[0]); portno = int(port_id.split('p')[1])
            charging_port = config.CHARGING_STATIONS.to_dict("records")[csno]["ports"][portno]
    
            st = helper.roundup(stime)
            duration = helper.find_duration(charging_port['power'], bcap)
            nslots = int(math.ceil(duration/SLOT_TIME))
            config.REQUIRED_SLOTS[new_idx]=nslots
            matchedSlots = []
            while st + duration <= etime:
                matchedSlots.append(int(st/SLOT_TIME))
                st+=SLOT_TIME

            if(config.POSSIBLE_SLOTS.get(port_id)==None):
                config.POSSIBLE_SLOTS[port_id]=dict()
            config.POSSIBLE_SLOTS[port_id][new_idx] = matchedSlots
                    
            if(config.REQUEST_MAPPING.get(port_id)==None):
                config.REQUEST_MAPPING[port_id]=[]
            config.REQUEST_MAPPING[port_id].append(new_idx)

            if(config.SLOT_MAPPING.get(port_id)==None): 
                config.SLOT_MAPPING[port_id]={}

            if(matching.kuhn(new_idx, config.VISITED, 0, config.SLOT_MAPPING, port_id)):
                print(f"\n>>> REQUEST ACCEPTED! Accommodated in Port {port_id}")
                alert_message = f"Request Accepted -> Accommodated in Port {port_id}"
                alert_open = True; alert_color="success"
                flag=1
                break
            else:
                config.REQUEST_MAPPING[port_id].remove(new_idx)
                del config.POSSIBLE_SLOTS[port_id][new_idx]

        if(flag==0): 
            print("\n>>> REQUEST DENIED.")
            alert_message = "No slot available for given specifications."; alert_open=True; alert_color="danger"

        json_object = json.dumps(config.SLOT_MAPPING, indent=4)
        with open("datasets/slot_mapping.json","w") as f:
            f.write(json_object)
    
    return config.POSITIONS, config.REQUEST_NODES, config.CS_POSITIONS, config.POLYGON, config.W2_PORTS, config.W3_PORTS, config.W4_PORTS, config.CENTER, config.ZOOM_LEVEL, config.REQUESTS.to_dict('records'), config.COLUMNS, config.CS_DROPDOWN.to_dict('records'), config.REQUESTS_DROPDOWN.to_dict('records'), alert_message, alert_open, alert_color

@app.callback(
    Output('port_input_dd','options'),
    Input('all_cs_button', 'n_clicks'),
    State('cs_input_dd','value')
)
def display_ports(n_clicks, station_index):
    if n_clicks is None: 
        raise PreventUpdate
    
    nports = len(config.CHARGING_STATIONS.to_dict("records")[int(station_index)]["ports"])
    dropdown_content = [[f"Port #{i}",f"{i}"] for i in range(nports)]
    dropdown = pd.DataFrame(dropdown_content,columns = ['label','value'])
    config.PORTS_DROPDOWN = dropdown

    return config.PORTS_DROPDOWN.to_dict("records")

@app.callback(
    Output('cs_schedule','data'),
    Output('cs_schedule','columns'),
    Input('all_port_button','n_clicks'),
    State('cs_input_dd','value'),
    State('port_input_dd','value')
)
def show_schedule(n_clicks, station, port):
    if n_clicks is None:
        raise PreventUpdate
    
    port_id = station+"p"+port
    charging_port = config.CHARGING_STATIONS.to_dict("records")[int(station)]["ports"][int(port)]
    if config.SLOT_MAPPING.get(port_id)==None:
        return [],[]

    check=[]; table_data=[]
    for key in config.SLOT_MAPPING[port_id].keys():
        dup = config.SLOT_MAPPING[port_id]
        if(dup[key] in check): continue
        check.append(dup[key])
        bcap = config.REQUESTS.loc[config.REQUESTS['index']==dup[key], 'battery_capacity'].iloc[0]
        dur = math.ceil(charging_port['power']*60/bcap)
        time = datetime.time(int(key*SLOT_TIME)//60, int(key*SLOT_TIME)%60)
        table_data.append([dup[key],time,dur])

    schedule = pd.DataFrame(table_data, columns=['Request Index','Time','Duration (in mins)'])
    schedule = schedule.sort_values(by=['Time'])
    cols = [{"name": i, "id": i} for i in schedule.columns]
    return schedule.to_dict("records"), cols

app.layout = dbc.Container([
	Navbar(),
    html.Br(),
    html.H1("Slot Scheduling App", style={"text-align":"center"}),
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
                dl.Overlay(dl.LayerGroup(id="2w_cs_ports"), name="2W Charging Ports", checked=False),
                dl.Overlay(dl.LayerGroup(id="3w_cs_ports"), name="3W Charging Ports", checked=False),
                dl.Overlay(dl.LayerGroup(id="4w_cs_ports"), name="4W Charging Ports", checked=False),
                ]
              ) 
            ], id="er_result_map"), width=7),
        dbc.Col(layout.all_nodes_form, width=5), 
    ]),
    html.Br(),
    html.H3("Existing Requests"),
    html.Div([
        dash_table.DataTable(
        data=config.REQUESTS.to_dict("records"), 
        columns=[], 
        id="req_tbl",
        # style_table={'overflowX': 'scroll'},
        style_as_list_view=True,
        style_cell={'textAlign': 'center'},
        style_header={'backgroundColor': 'white','fontWeight': 'bold'}, 
        page_size=5)
    ]),
    html.Br(),
    html.H3("Display Charging Schedule"),
    dbc.Row([
        dbc.Col(layout.cs_schedule_form),
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
    html.Br(),
    html.Br(),
    html.H3("Make a new request"),
    dbc.Row([dbc.Col(layout.new_request_form)]),
    dbc.Alert(id="schedule_alert", is_open=False)
])

if __name__ == "__main__":
    # app.run_server(host='172.16.26.67', port=8053)
    app.run_server(host='127.0.0.1',debug=True, port=8002)