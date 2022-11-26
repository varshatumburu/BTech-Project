import dash, config, requests, urllib.parse
from dash import Dash, dcc, html, Input, Output, State, dash_table
from dash.dependencies import ALL
import dash_bootstrap_components as dbc
import plotly.express as px
from geopy.geocoders import Nominatim
from navbar import Navbar
import dash_leaflet as dl
import plotly.graph_objects as go
import osmnx as ox
from math import asin,cos,pi,sin
from dash.exceptions import PreventUpdate
import pandas as pd
import networkx as nx
from queue import PriorityQueue
import matching
import datetime

mapbox_access_token = "pk.eyJ1IjoiaGFyc2hqaW5kYWwiLCJhIjoiY2tleW8wbnJlMGM4czJ4b2M0ZDNjeGN4ZyJ9.XXPg4AsUx0GUygvK8cxI6g"
geolocator = Nominatim(user_agent="Slot Scheduling App")
location = geolocator.geocode("India")
Oid = []
input_ev_locations = []
Xnode = []
Ynode = []
paths = []
path_nodes = []
optimal_paths = []
optimal_path_nodes = []
optimal_paths_info = []
G1 = None
algo_input = {}
path_id = None
distances = []
slotMapping = dict()

def roundup(x):
    return int(math.ceil(x / SLOT_TIME)) * int(SLOT_TIME)

app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
requests_df = pd.read_json("requests.json")
Search_Region=[22.59372606392931, 78.57421875000001]
location_input = dbc.FormGroup(
    [
        dbc.Label("Search Area", html_for="location", width=4),
        dbc.Col(
            dbc.Input(
                type="text", id="er_location_input", placeholder="Enter a valid location",value="Patna, Bihar, India",debounce=False, disabled=True
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
                type="number", id="er_radius_input", placeholder="Enter Radius between [500,8000] meters",min=100, step=1,max=8000, value=500, disabled=True
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
                type="number", id="er_no_of_cs_input", placeholder="Enter total no of cs",min=1, step=1,max=10, value=10, disabled=True
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
        dbc.Label("Show schedule for Charging Station:", html_for="no_of_cs", width=4),
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
        if config.location is not None:
            return dash.no_update, config.location
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
        config.location = loc
        return [], loc

def get_eco_zoom_level(radius):
    level=17
    p=1
    while(p*100<radius):
        p=p*2
        level=level-1
    return level

#Function to form default intial map
def default_location():
    parsed_loc = urllib.parse.quote("India")
    response = requests.get("http://api.mapbox.com/geocoding/v5/mapbox.places/"+parsed_loc+".json?country=IN&access_token=pk.eyJ1IjoiaGFyc2hqaW5kYWwiLCJhIjoiY2tleW8wbnJlMGM4czJ4b2M0ZDNjeGN4ZyJ9.XXPg4AsUx0GUygvK8cxI6g")
    res=response.json()
    latitude=res["features"][0]["geometry"]["coordinates"][1]
    longitude=res["features"][0]["geometry"]["coordinates"][0]
    location = geolocator.geocode("India")
    center=[]
    center.append(latitude)
    center.append(longitude)
    zoomLevel = get_eco_zoom_level(500000)
    fig = go.Figure(go.Scattermapbox(
    lat=[location.latitude],
    lon=[location.longitude]
    ))
    fig.update_layout(
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=location.latitude,
                lon=location.longitude
            ),
            pitch=0,
            zoom=5,
        )
    )
    fig.update_layout(mapbox_style="open-street-map")
    return fig, center, zoomLevel



# Function to get all the nodes from osmnx and writting those nodes to input file
def get_all_nodes(latitude,longitude,radius):

    location_point=(latitude,longitude)
    global G1
    G1 = ox.graph_from_point(location_point, dist=radius, simplify=True, network_type='drive', clean_periphery=False)
    ox.save_graphml(G1, filepath='network1.graphml')
    nodes, edges = ox.graph_to_gdfs(G1, nodes=True, edges=True)

    print(f"location used: {location_point}")
    print("node data:")

    global Oid
    Oid=pd.Series.tolist(nodes.index)
    print(nodes.dtypes)
    
    
    Ynode=pd.Series.tolist(nodes.y)
    Xnode=pd.Series.tolist(nodes.x)
    

    A = nx.adjacency_matrix(G1,weight='length')
   
    B1=A.tocoo()
    list1=B1.data
    list2=B1.row
    list3=B1.col

    my_file = open('input_graph.txt', "w+")
    my_file.write("%d \n" %len(G1.nodes))
    my_file.write("%d \n" %len(list1))

    for i in range(len(list1)):
        my_file.write("%d " %(list2[i]))  
        my_file.write("%d " %(list3[i]))  
        my_file.write("%d \n" %int(list1[i])) 
    
    my_file.close()

    return len(G1.nodes), G1, A, Xnode, Ynode

# finds nodes based on search location and radius
def find_all_nodes(search_location, radius):
    
    parsed_loc = urllib.parse.quote(search_location)
    response = requests.get("http://api.mapbox.com/geocoding/v5/mapbox.places/"+parsed_loc+".json?country=IN&access_token=pk.eyJ1IjoiaGFyc2hqaW5kYWwiLCJhIjoiY2tleW8wbnJlMGM4czJ4b2M0ZDNjeGN4ZyJ9.XXPg4AsUx0GUygvK8cxI6g")
    res=response.json()
    lat_center=res["features"][0]["geometry"]["coordinates"][1]
    long_center=res["features"][0]["geometry"]["coordinates"][0]
    # print(search_location)
    center = [lat_center,long_center]
    zoomLevel = get_eco_zoom_level(radius)
    global G1
    num_of_tot_nodes, G1, A, Xnode, Ynode = get_all_nodes(lat_center,long_center,radius)
    
    # Preparing the map to display all the nodes got from Osmnx
    all_nodes = go.Figure(go.Scattermapbox(
        name='General nodes',
        lat=Ynode,
        lon=Xnode,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=10
        ),
        text=[search_location],
    ))

    all_nodes.update_layout(
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=lat_center,
                lon=long_center,
            ),
            pitch=0,
            zoom=15
        )
    )
    all_nodes.update_layout(mapbox_style="open-street-map")
    
    return all_nodes, num_of_tot_nodes, G1, A, Xnode, Ynode, center, zoomLevel, lat_center, long_center

rEarth = 6371.01 # Earth's average radius in km
epsilon = 0.000001 # threshold for floating-point equality

def deg2rad(angle):
    return angle*pi/180


def rad2deg(angle):
    return angle*180/pi

# Function to form polygon with 24 sides around the search space
def pointRadialDistance(lat1, lon1, bearing, distance):
    """
    Return final coordinates (lat2,lon2) [in degrees] given initial coordinates
    (lat1,lon1) [in degrees] and a bearing [in degrees] and distance [in km]
    """
    rlat1 = deg2rad(lat1)
    rlon1 = deg2rad(lon1)
    rbearing = deg2rad(bearing)
    rdistance = distance / rEarth # normalize linear distance to radian angle

    rlat = asin( sin(rlat1) * cos(rdistance) + cos(rlat1) * sin(rdistance) * cos(rbearing) )

    if cos(rlat) == 0 or abs(cos(rlat)) < epsilon: # Endpoint a pole
        rlon=rlon1
    else:
        rlon = ( (rlon1 - asin( sin(rbearing)* sin(rdistance) / cos(rlat) ) + pi ) % (2*pi) ) - pi

    lat = rad2deg(rlat)
    lon = rad2deg(rlon)
    return (lat, lon)

import random

def mapRequests2Stations(nreq, nearest_cs):
    reqMapping = dict()
    for i in range(nreq):
        st=-1
        if not nearest_cs[i].empty():
            st = nearest_cs[i].get()[1]
            if reqMapping.get(st)==None or len(reqMapping[st])==0:
                reqMapping[st]=[]

        if(st!=-1): reqMapping[st].append(i)

    return reqMapping

def iterative_scheduling(nreq, blocked, leftover, reqMapping, nearest_cs):
    iter=0; prev=-1
    while len(blocked)!=nreq and prev!=len(blocked):
        print(f"\n>>> Iteration {iter} >>> ")
        for st in list(reqMapping.keys()):
            prev=len(blocked)
            
            # print(reqMapping[id])
            reqidx = reqMapping[st]
            if len(reqidx)==0: continue
            print(f"\nSchedule for Station {st}:")
            # new_additions = [i for i in leftover if i not in reqidx]
            # reqidx.extend(new_additions)

            selected, slotMapping[st] = matching.init_schedule(reqidx, st, dict())
            leftover = list(set(reqidx)-set(selected))

            # print(leftover)
            for lr in leftover:
                if not nearest_cs[lr].empty():
                    next_nearest_station = nearest_cs[lr].get()[1]
                    reqMapping[st].remove(lr)
                    if reqMapping.get(next_nearest_station)==None or len(reqMapping[next_nearest_station])==0:
                        reqMapping[next_nearest_station]=[]
                    reqMapping[next_nearest_station].append(lr)

            blocked = set(list(blocked)+list(selected))

        if(prev==len(blocked)): break
        iter+=1

    config.slotMapping = slotMapping
    print("\nCompleted scheduling!")

# Callback dealing with intial inputs(area and radius) and output(all nodes and polygon around the search space)
@app.callback(
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

    if n_clicks is None:
        raise PreventUpdate
    #     if config.num_of_tot_nodes != 0:
    #         return config.positions,config.cs_positions, config.polygon,config.center, config.zoomLevel

    #     if n_clicks is None:
    #         fig, center, zoomLevel = default_location()    
    #         return dash.no_update, dash.no_update, dash.no_update, center, zoomLevel


    global Xnode, Ynode, G1
    fig, num_of_tot_nodes, G1, A, Xnode, Ynode, center, zoomLevel, latitude, longitude = find_all_nodes(location, radius)
    

    testcases = []
    corners = []
    for x in range(0,361,1):
        testcases.append((latitude,longitude,x,(radius+350)/1000))
    
    for lat1, lon1, bear, dist in testcases:
        (lat,lon) = pointRadialDistance(lat1,lon1,bear,dist)
        corners.append([lat,lon])
    polygon = dl.Polygon(positions=corners)

    # info related to cs
    config.num_of_cs = number_of_cs
    config.cs_nodes = random.sample(range(0,num_of_tot_nodes),number_of_cs)

    request_nodes = random.sample([i for i in range(0,num_of_tot_nodes) if i not in config.cs_nodes],requests_df.shape[0])
    reqpositions = []; positions = []
    for i in range(len(Xnode)):
        positions.append(dl.Marker(position=[Ynode[i],Xnode[i]],children=dl.Tooltip(i, direction='top', permanent=True),riseOnHover=True))

    nearest_cs = dict()
    for i in range(len(request_nodes)):
        y=Ynode[request_nodes[i]]; x=Xnode[request_nodes[i]]
        reqpositions.append(dl.Marker(position=[y,x],children=dl.Tooltip(i, direction='right', permanent=True),riseOnHover=True,
        icon={'iconUrl':'https://icon-library.com/images/marker-icon/marker-icon-12.jpg','iconSize':[40,40]}))
        q = PriorityQueue()
        for j in config.cs_nodes: 
            [n1, n2] = ox.distance.nearest_nodes(G1,[x,Xnode[j]], [y,Ynode[j]])
            try:
                dist = nx.shortest_path_length(G1, n1, n2, weight='length')
                q.put((dist,j))
            except nx.exception.NetworkXNoPath:
                continue

        nearest_cs[i]=q
    
    print(requests_df)
    requestMapping = mapRequests2Stations(len(requests_df),nearest_cs)
    print(requestMapping)
    blocked=set(); leftover=[]
    iterative_scheduling(len(requests_df),blocked,leftover,requestMapping,nearest_cs)


    config.cs_positions = [dl.Marker(position=[Ynode[i],Xnode[i]],children=dl.Tooltip(i, direction='top', permanent=True),\
        riseOnHover=True,icon={'iconUrl':'https://icon-library.com/images/station-icon/station-icon-14.jpg','iconSize':[30,40]}) \
            for i in config.cs_nodes]

    dropdown_content = [[f"Cs Node{i}",f"Node{i}"] for i in config.cs_nodes]
    dropdown = pd.DataFrame(dropdown_content,columns = ['label','value'])
    config.cs_dropdown = dropdown

    # setting the global variables in config file
    config.num_of_tot_nodes, config.positions, config.polygon, config.center, config.zoomLevel = num_of_tot_nodes, positions, polygon,center, zoomLevel
    # print(config.cs_nodes)
    # print([i for i in range(0,config.num_of_tot_nodes) if i not in config.cs_nodes])
    # print(requests_df.shape[0])

    requests_df['node'] = request_nodes
    
    # nnodes = [ox.distance.nearest_nodes(G1,Xnode[i],Ynode[i]) for i in request_nodes]
    # print(nnodes)

    cols = [{"name": i, "id": i} for i in requests_df.columns]

    dropdown_content = [[f"CS #{i}",f"{i}"] for i in config.cs_nodes]
    dropdown = pd.DataFrame(dropdown_content,columns = ['label','value'])
    config.cs_dropdown = dropdown

    return positions,reqpositions,config.cs_positions,polygon ,center, zoomLevel, requests_df.to_dict("records"), cols, config.cs_dropdown.to_dict('records')

    # return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
from scheduler import SLOT_TIME
@app.callback(
    Output('cs_schedule','data'),
    Output('cs_schedule','columns'),
    Input('all_cs_button','n_clicks'),
    State('cs_input_dd','value')
)
def show_schedule(n_clicks, cs_input):
    if n_clicks is None:
        raise PreventUpdate

    if config.slotMapping.get(int(cs_input))==None:
        return [],[]

    check=[]; table_data=[]
    for key in config.slotMapping[int(cs_input)].keys():
        dup = config.slotMapping[int(cs_input)]
        if(dup[key] in check): continue
        check.append(dup[key])
        dur = requests_df.loc[requests_df['index']==dup[key], 'duration'].iloc[0]
        time = datetime.time(int(key*SLOT_TIME)//60, int(key*SLOT_TIME)%60)
        table_data.append([dup[key],time,dur])

    schedule = pd.DataFrame(table_data, columns=['Request Index','Time','Duration (in mins)'])
    cols = [{"name": i, "id": i} for i in schedule.columns]
    return schedule.to_dict("records"), cols

app.layout = dbc.Container([
	Navbar(),
    html.Br(),
    html.H1("Slot Scheduling App", style={"text-align":"center"}),
    html.Br(),
    dbc.Row([
        dbc.Col(dl.Map(style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block"},
            center=Search_Region,
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
        dbc.Col(all_nodes_form, width=5), 
    ]),
    html.Br(),
    html.H3("Existing Requests"),
    html.Div([
        dash_table.DataTable(
        data=requests_df.to_dict("records"), 
        columns=[], 
        id="req_tbl",
        # style_table={'overflowX': 'scroll'},
        style_as_list_view=True,
        style_cell={'textAlign': 'center'},
        style_header={'backgroundColor': 'white','fontWeight': 'bold'})
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col(cs_schedule_form),
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
    ])
])

if __name__ == "__main__":
    app.run_server(debug=True, port=8002)