import requests, urllib.parse
import plotly.graph_objects as go
import osmnx as ox
from math import asin,cos,pi,sin
import pandas as pd
import networkx as nx
from queue import PriorityQueue, Queue
import math, sys
from geopy.geocoders import Nominatim

sys.path.insert(1, '/home/varsha_1901cs69/btp/scheduling/modules')
import config, matching
from scheduler import prebooked_scheduling, SLOT_TIME

mapbox_access_token = "pk.eyJ1IjoiaGFyc2hqaW5kYWwiLCJhIjoiY2tleW8wbnJlMGM4czJ4b2M0ZDNjeGN4ZyJ9.XXPg4AsUx0GUygvK8cxI6g"
geolocator = Nominatim(user_agent="Slot Scheduling App")

def roundup(x):
    return int(math.ceil(x / SLOT_TIME)) * int(SLOT_TIME)

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
    response = requests.get("http://api.mapbox.com/geocoding/v5/mapbox.places/"+parsed_loc+".json?country=IN&access_token="+mapbox_access_token)
    res=response.json()
    latitude=res["features"][0]["geometry"]["coordinates"][1]
    longitude=res["features"][0]["geometry"]["coordinates"][0]
    location = geolocator.geocode("India", timeout=None)
    center=[]
    center.append(latitude)
    center.append(longitude)
    zoomLevel = get_eco_zoom_level(250000)
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
    global GRAPH
    GRAPH = ox.graph_from_point(location_point, dist=radius, simplify=True, network_type='drive')
    ox.save_graphml(GRAPH, filepath='network1.graphml')
    nodes, edges = ox.graph_to_gdfs(GRAPH, nodes=True, edges=True)

    # print(f"location used: {location_point}")
    # print("node data:")
    
    Ynode=pd.Series.tolist(nodes.y)
    Xnode=pd.Series.tolist(nodes.x)

    A = nx.adjacency_matrix(GRAPH,weight='length')
   
    B1=A.tocoo()
    list1=B1.data
    list2=B1.row
    list3=B1.col

    my_file = open('input_graph.txt', "w+")
    my_file.write("%d \n" %len(GRAPH.nodes))
    my_file.write("%d \n" %len(list1))

    for i in range(len(list1)):
        my_file.write("%d " %(list2[i]))  
        my_file.write("%d " %(list3[i]))  
        my_file.write("%d \n" %int(list1[i])) 
    
    my_file.close()

    return len(GRAPH.nodes), GRAPH, A, Xnode, Ynode

# finds nodes based on search location and radius
def find_all_nodes(search_location, radius, num_of_cs):
    
    parsed_loc = urllib.parse.quote(search_location)
    response = requests.get("http://api.mapbox.com/geocoding/v5/mapbox.places/"+parsed_loc+".json?country=IN&access_token=pk.eyJ1IjoiaGFyc2hqaW5kYWwiLCJhIjoiY2tleW8wbnJlMGM4czJ4b2M0ZDNjeGN4ZyJ9.XXPg4AsUx0GUygvK8cxI6g")
    res=response.json()
    lat_center=res["features"][0]["geometry"]["coordinates"][1]
    long_center=res["features"][0]["geometry"]["coordinates"][0]
    # print(search_location)
    center = [lat_center,long_center]
    zoomLevel = get_eco_zoom_level(radius)
    global GRAPH
    num_of_tot_nodes, GRAPH, A, Xnode, Ynode = get_all_nodes(lat_center,long_center,radius)
    
    # Preparing the map to display all the nodes got from Osmnx
    all_nodes = go.Figure(go.Scattermapbox(
        name='General nodes',
        lat=Ynode,
        lon=Xnode,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=num_of_cs
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
    
    return all_nodes, num_of_tot_nodes, GRAPH, A, Xnode, Ynode, center, zoomLevel, lat_center, long_center

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

def mapRequests2Ports(nreq, nearest_ports):
    reqMapping = dict()
    for i in range(nreq):
        st=-1
        if not nearest_ports[i].empty():
            st = nearest_ports[i].get()
            if reqMapping.get(st)==None or len(reqMapping[st])==0:
                reqMapping[st]=[]

        if(st!=-1): reqMapping[st].append(i)

    return reqMapping

def iterative_scheduling(nreq, blocked, leftover, reqMapping, nearest_ports):
    iter=0; prev=-1
    # print(reqMapping)
    while len(blocked)!=nreq and prev!=len(blocked) and reqMapping:
        print(f"\n>>> Iteration {iter} >>> ")
        for port in list(reqMapping.keys()):
            prev=len(blocked)
            
            reqidx = reqMapping[port]
            if len(reqidx)==0: continue
            print(f"\nSchedule for Port {port}:")

            selected, config.SLOT_MAPPING[port] = matching.init_schedule(reqidx, port, dict())
            leftover = list(set(reqidx)-set(selected))

            for lr in leftover:
                if not nearest_ports[lr].empty():
                    next_nearest_port = nearest_ports[lr].get()
                    reqMapping[port].remove(lr)
                    if reqMapping.get(next_nearest_port)==None or len(reqMapping[next_nearest_port])==0:
                        reqMapping[next_nearest_port]=[]
                    reqMapping[next_nearest_port].append(lr)

            blocked = set(list(blocked)+list(selected))

        if(prev==len(blocked)): break
        iter+=1

    print("\nCompleted scheduling!")

def get_nearest_cs_pq(x, y, max_distance=math.inf):
    q = PriorityQueue()
    stations = config.CHARGING_STATIONS
    for j in range(len(stations)): 
        # n1, n2 nearest node to x, y in graph (estimation done from there)
        [n1, n2] = ox.distance.nearest_nodes(config.GRAPH,[x,config.X_NODES[stations.loc[j]["node"]]], [y,config.Y_NODES[stations.loc[j]["node"]]])
        try:
            dist = nx.shortest_path_length(config.GRAPH, n1, n2, weight='length')
            if dist <= max_distance :
                q.put((dist,j))
        except nx.exception.NetworkXNoPath:
            continue
    return q

def get_nearest_ports_pq(request, nearest_cs):
    q = Queue()
    stations = config.CHARGING_STATIONS

    while not nearest_cs.empty():
        dist, station_index = nearest_cs.get()
        sorted_ports = sorted(stations.loc[station_index]["ports"], key = lambda x:len(x["vehicles"]))
        for port in sorted_ports:
            duration = port["power"]*60/request["battery_capacity"]
            if request["vehicle_type"] in port["vehicles"] and duration<=request["end_time"]-request["start_time"]:
                port_id = str(station_index)+"p"+str(port["id"])
                q.put(port_id)
                
    return q