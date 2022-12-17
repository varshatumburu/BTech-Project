import dash, config, requests, urllib.parse
from dash import Dash, html, Input, Output, State, dash_table
from dash.dependencies import ALL
import dash_bootstrap_components as dbc
from navbar import Navbar
import dash_leaflet as dl
from dash.exceptions import PreventUpdate
import pandas as pd
import matching, layout, helper
import datetime
import math
from scheduler import SLOT_TIME
import random

app = Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

Search_Region=[22.59372606392931, 78.57421875000001]

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
        config.location = loc
        return [], loc

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
    Output('req_node_input', 'options'),
    Output('schedule_alert', 'children'),
    Output('schedule_alert', 'is_open'),
    Output('schedule_alert', 'color'),
    Input('er_all_nodes_button', 'n_clicks'),
    Input('schedule_button', 'n_clicks'),
    State('req_node_input', 'value'),
    State('duration_input','value'),
    State('start_time_input','value'),
    State('end_time_input','value'),
    State('er_location_input', 'value'),
    State('er_radius_input', 'value'),
    State('er_no_of_cs_input', 'value'),
)
def hp_update_map(n_clicks, sched_clicks, req_nodeid, duration, stime, etime, location, radius, number_of_cs):

    alert_message=""; alert_open=False; alert_color = "primary"
    if config.G1 is None:
        fig, config.center, config.zoomLevel = helper.default_location()

    if n_clicks is None:
        return config.positions,config.reqpositions,config.cs_positions, config.polygon , config.center, config.zoomLevel, config.requests.to_dict('records'), config.cols, config.cs_dropdown.to_dict('records'), config.req_dropdown.to_dict('records'), alert_message, alert_open, alert_color
    
    fig, num_of_tot_nodes, config.G1, A, config.Xnode, config.Ynode, center, zoomLevel, latitude, longitude = helper.find_all_nodes(location, radius, number_of_cs)
    if n_clicks and n_clicks>config.n_clicks:
        requests_df = pd.read_json("requests.json")
        config.n_clicks = n_clicks
        testcases = []
        corners = []
        for x in range(0,361,1):
            testcases.append((latitude,longitude,x,(radius+350)/1000))
        
        for lat1, lon1, bear, dist in testcases:
            (lat,lon) = helper.pointRadialDistance(lat1,lon1,bear,dist)
            corners.append([lat,lon])
        polygon = dl.Polygon(positions=corners)

        # info related to cs
        config.num_of_cs = number_of_cs
        config.cs_nodes = random.sample(range(0,num_of_tot_nodes),number_of_cs)

        request_nodes = random.sample([i for i in range(0,num_of_tot_nodes) if i not in config.cs_nodes],requests_df.shape[0])
        reqpositions = []; positions = []
        for i in range(len(config.Xnode)):
            positions.append(dl.Marker(position=[config.Ynode[i],config.Xnode[i]],children=dl.Tooltip(i, direction='top', permanent=True),riseOnHover=True))

        for idx, nodeid in enumerate(request_nodes):
            y=config.Ynode[nodeid]; x=config.Xnode[nodeid]
            request_index = requests_df.loc[requests_df.index[idx],'index']
            reqpositions.append(dl.Marker(position=[y,x],children=dl.Tooltip(request_index, direction='right', permanent=True),riseOnHover=True,icon={'iconUrl':'https://icon-library.com/images/marker-icon/marker-icon-12.jpg','iconSize':[40,40]}))
            config.nearest_cs[request_index]=helper.get_nearest_cs_pq(x,y)

        config.requestMapping = helper.mapRequests2Stations(len(requests_df),config.nearest_cs)
        blocked=set(); leftover=[]
        helper.iterative_scheduling(len(requests_df),blocked,leftover,config.requestMapping,config.nearest_cs)

        config.cs_positions = [dl.Marker(position=[config.Ynode[i],config.Xnode[i]],children=dl.Tooltip(i, direction='top', permanent=True),\
            riseOnHover=True,icon={'iconUrl':'https://icon-library.com/images/station-icon/station-icon-14.jpg','iconSize':[30,40]}) \
                for i in config.cs_nodes]

        req_node_content = [[f"Node #{i}",f"{i}"] for i in range(num_of_tot_nodes) if i not in config.cs_nodes]
        req_dropdown = pd.DataFrame(req_node_content,columns = ['label','value'])
        config.req_dropdown = req_dropdown

        # setting the global variables in config file
        config.num_of_tot_nodes, config.positions, config.reqpositions ,config.polygon, config.center, config.zoomLevel = num_of_tot_nodes, positions, reqpositions, polygon, center, zoomLevel, 

        requests_df['node'] = request_nodes

        config.cols = [{"name": i, "id": i} for i in requests_df.columns]

        dropdown_content = [[f"CS #{i}",f"{i}"] for i in config.cs_nodes]
        dropdown = pd.DataFrame(dropdown_content,columns = ['label','value'])
        config.cs_dropdown = dropdown
        config.requests = requests_df

    if sched_clicks and sched_clicks>config.sched_clicks:
        new_idx = max(config.requests['index'])+1
        duration, stime, etime, req_nodeid = int(duration), int(stime), int(etime), int(req_nodeid)
        new_request = pd.DataFrame({
            "index": new_idx,
            "rcharge": 0,
			"duration": duration,
			"start_time": stime,
			"end_time": etime,
			"node": req_nodeid
        }, index=[0])
        
        config.requests = pd.concat([new_request, config.requests[:]]).drop_duplicates().reset_index(drop=True)

        config.reqpositions.append(dl.Marker(position=[config.Ynode[req_nodeid],config.Xnode[req_nodeid]],children=dl.Tooltip(new_idx, direction='right', permanent=True),riseOnHover=True,icon={'iconUrl':'https://icon-library.com/images/marker-icon/marker-icon-12.jpg','iconSize':[40,40]}))
        config.nearest_cs[new_idx] = helper.get_nearest_cs_pq(config.Xnode[req_nodeid], config.Ynode[req_nodeid])

        st = helper.roundup(stime)
        nslots = int(math.ceil(duration/SLOT_TIME))
        matching.reqSlots[new_idx]=nslots
        matchedSlots = []
        while st +duration<=etime:
            matchedSlots.append(int(st/SLOT_TIME))
            st+=SLOT_TIME

        flag=0
        while not config.nearest_cs[new_idx].empty():

            station = config.nearest_cs[new_idx].get()[1]
            if(matching.graphs.get(station)==None):
                matching.graphs[station]=dict()
            matching.graphs[station][new_idx] = matchedSlots
            if(config.requestMapping.get(station)==None):
                config.requestMapping[station]=[]
            config.requestMapping[station].append(new_idx)

            matching.used.clear()
            if(config.slotMapping.get(station)==None): 
                config.slotMapping[station]={}
            if(matching.kuhn(new_idx, 0, config.slotMapping[station], station)):
                print(f"\n>>> REQUEST ACCEPTED! Accommodated in Station {station}")
                alert_message = f"Request Accepted -> Accommodated in Station {station}"
                alert_open = True; alert_color="success"
                matching.satisfied_requests+=1
                flag=1
                break
            else:
                config.requestMapping[station].remove(new_idx)
                del matching.graphs[station][new_idx]

        if(flag==0): 
            print("\n>>> REQUEST DENIED.")
            alert_message = "Request Denied :("; alert_open=True; alert_color="danger"

    
    return config.positions,config.reqpositions,config.cs_positions, config.polygon , config.center, config.zoomLevel, config.requests.to_dict('records'), config.cols, config.cs_dropdown.to_dict('records'), config.req_dropdown.to_dict('records'), alert_message, alert_open, alert_color


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
        dur = config.requests.loc[config.requests['index']==dup[key], 'duration'].iloc[0]
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
        dbc.Col(layout.all_nodes_form, width=5), 
    ]),
    html.Br(),
    html.H3("Existing Requests"),
    html.Div([
        dash_table.DataTable(
        data=config.requests.to_dict("records"), 
        columns=[], 
        id="req_tbl",
        # style_table={'overflowX': 'scroll'},
        style_as_list_view=True,
        style_cell={'textAlign': 'center'},
        style_header={'backgroundColor': 'white','fontWeight': 'bold'}, 
        page_size=5)
    ]),
    html.Br(),
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
    dbc.Row([dbc.Col(layout.new_request_form)]),
    dbc.Alert(id="schedule_alert", is_open=False)
])

if __name__ == "__main__":
    # app.run_server(host='172.16.26.67', port=8053)
    app.run_server(host='127.0.0.1',debug=True, port=8002)