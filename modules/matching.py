import json, datetime, math, sys

sys.path.insert(1, '/home/varsha_1901cs69/btp/scheduling/modules')
from scheduler import prebooked_scheduling, SLOT_TIME

sys.path.insert(2, '/home/varsha_1901cs69/btp/scheduling')
import config


global_requests = json.load(open(config.DATASET + "/requests.json"))

def roundup(x):
    return int(math.ceil(x / SLOT_TIME)) * int(SLOT_TIME)

graph=dict(); reqSlots = dict()
slot_mapping = dict(); used=dict()
satisfied_requests=0
graphs = dict()

def createGraph(requests, port_id="-1", charging_port={}):
	duration = 0
	for req in requests:
		st = roundup(req['start_time'])
		if charging_port:
			duration = math.ceil(charging_port['power']*60/req['battery_capacity'])
		else: 
			duration = req['duration']
		nslots = int(math.ceil(duration/SLOT_TIME))
		reqSlots[req['index']]=nslots

		matchedSlots=[]
		i=1
		while st + duration<=req['end_time']:
			matchedSlots.append(int(st/SLOT_TIME))
			st+=SLOT_TIME; i+=1

		if(port_id=="-1"):
			graph[req['index']]=(matchedSlots)
		else:
			graphs[port_id][req['index']]=(matchedSlots)
	
def printSchedule(charging_port, request=global_requests, slot_mapping=slot_mapping):

	check=[]
	for key in sorted(slot_mapping.keys()):
		if(slot_mapping[key] in check): continue
		check.append(slot_mapping[key])
		bcap = [req for req in request if req['index']==slot_mapping[key]][0]['battery_capacity']
		dur = math.ceil(charging_port['power']*60/bcap)
		time = datetime.time(int(key*SLOT_TIME)//60, int(key*SLOT_TIME)%60)
		print(f"Request {slot_mapping[key]} scheduled at {time} for {dur} mins.")

def kuhn(src, start_slot=0, slot_mapping=slot_mapping, port_id="-1"):

	if(used.get(src)!=None): return False
	used[src]=True
	charging_stations = config.CHARGING_STATIONS.to_dict("records")
	charging_requests = config.REQUESTS.to_dict("records")
	nslots = reqSlots[src] # number of slots required to fit

	# Iterate through all ports in 1 cs, take some sorted order of ports 
	cs, pidx="",""
	if port_id=="-1":
		possibleSlots = graph[src]
	else:
		cs, pidx = port_id.split('p')
		possibleSlots = graphs[port_id][src]

	for slot in possibleSlots:
		if slot<start_slot:continue

		busy_slots = [val for val in range(slot,slot+nslots) if val in slot_mapping[port_id].keys()]

		if(len(busy_slots)==0):
			for i in range(nslots):
				slot_mapping[port_id][slot+i]=src
			return True
		else:
			for bs in busy_slots:
				print(int(cs), slot_mapping[port_id][bs])
				shiftable_port_indices = [port["id"] for port in charging_stations[int(cs)]["ports"]\
			      	if charging_requests[slot_mapping[port_id][bs]]["vehicle_type"] in port["vehicles"] \
					and port["id"]!=int(pidx)]
				sorted_port_indices = sorted(shiftable_port_indices, key= lambda x: len(charging_stations[int(cs)]["ports"][x]["vehicles"]))
				print(sorted_port_indices)

				if(kuhn(slot_mapping[port_id][bs], slot+nslots, slot_mapping, port_id)):
					for i in range(nslots):
						slot_mapping[port_id][slot+i]=src
					return True
				else: 
					for sp in sorted_port_indices:
						next_portid = cs+"p"+str(sp)
						print(port_id, next_portid)
						if(kuhn(slot_mapping[port_id][bs], 0, slot_mapping, next_portid)):
							for i in range(nslots):
								slot_mapping[port_id][slot+i]=src
							return True

	return False

def init_schedule(reqSet, port_id="-1", slot_mapping = dict()):
	if(port_id=="-1"): graph.clear()
	else: graphs[port_id] = {}

	requests = [req for req in global_requests if req['index'] in reqSet]
	csno = int(port_id.split('p')[0]); portno= int(port_id.split('p')[1])
	charging_port = config.CHARGING_STATIONS.to_dict("records")[csno]["ports"][portno]
	selected = prebooked_scheduling(requests, charging_port)
	requests = [req for req in requests if req['index'] in selected]

	createGraph(requests, port_id, charging_port)
	satisfied_requests=0
	
	slot_mapping[port_id]={}
	for i in [r['index'] for r in requests]:
		used.clear()
		if(kuhn(i,0,slot_mapping, port_id)): satisfied_requests+=1

	printSchedule(charging_port, global_requests, slot_mapping[port_id])
	return selected, slot_mapping[port_id]

# Take in dynamic inputs 
def dynamic_requests(satisfied_requests=0):
	nreq = len(global_requests)
	idx = max([r['index'] for r in global_requests])+1
	while input("-----------------------\nEnter to go to new request: (-1 to break)")!="-1":
		duration = int(input("Enter duration: "))
		start_time = int(input("Enter start of availability: "))
		end_time = int(input("Enter end time of availability: "))

		global_requests.append({
			"index":idx,
			"duration": duration,
			"start_time": start_time,
			"end_time": end_time
		})

		st = roundup(start_time)
		nslots = int(math.ceil(duration/SLOT_TIME))
		reqSlots[idx]=nslots
		matchedSlots=[]
		while st + duration<=end_time:
			matchedSlots.append(int(st/SLOT_TIME))
			st+=SLOT_TIME

		graph[idx]=(matchedSlots)

		used.clear()
		if(kuhn(idx)): 
			print("\n>>> REQUEST ACCEPTED! NEW SCHEDULE:")
			satisfied_requests+=1
		else: 
			print("\n>>> REQUEST DENIED. BUSY SCHEDULE.")

		nreq+=1; idx+=1
		printSchedule()

if __name__=='__main__':
	createGraph(global_requests)
	satisfied_requests=0

	for i in [r['index'] for r in global_requests]:
		used.clear()
		if(kuhn(i)): satisfied_requests+=1

	printSchedule()
	dynamic_requests()
