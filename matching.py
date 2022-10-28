import json, datetime, math
from scheduler import prebooked_scheduling, SLOT_TIME

global_requests = json.load(open('requests.json'))

def roundup(x):
    return int(math.ceil(x / SLOT_TIME)) * int(SLOT_TIME)

graph=dict(); reqSlots = dict()
slot_mapping = dict(); used=dict()
satisfied_requests=0
graphs = dict()

def createGraph(requests):
	for req in requests:
		st = roundup(req['start_time'])
		nslots = int(math.ceil(req['duration']/SLOT_TIME))
		reqSlots[req['index']]=nslots

		matchedSlots=[]
		i=1
		while st + req['duration']<=req['end_time']:
			matchedSlots.append(int(st/SLOT_TIME))
			st+=SLOT_TIME; i+=1

		graph[req['index']]=(matchedSlots)

def createGraph(requests, station_index):
	for req in requests:
		st = roundup(req['start_time'])
		nslots = int(math.ceil(req['duration']/SLOT_TIME))
		reqSlots[req['index']]=nslots

		matchedSlots=[]
		i=1
		while st + req['duration']<=req['end_time']:
			matchedSlots.append(int(st/SLOT_TIME))
			st+=SLOT_TIME; i+=1

		graphs[station_index][req['index']]=(matchedSlots)

	
def printSchedule(request=global_requests, slot_mapping=slot_mapping):

	check=[]
	for key in sorted(slot_mapping.keys()):
		if(slot_mapping[key] in check): continue
		check.append(slot_mapping[key])
		dur = [req for req in request if req['index']==slot_mapping[key]][0]['duration']
		time = datetime.time(int(key*SLOT_TIME)//60, int(key*SLOT_TIME)%60)
		print(f"Request {slot_mapping[key]} scheduled at {time} for {dur} mins.")

def kuhn(src, start_slot=0, slot_mapping=slot_mapping):

	if(used.get(src)!=None): return False
	used[src]=True

	nslots = reqSlots[src]
	for slot in graph[src]:
		if slot<start_slot:continue

		fl=1
		lst = [val for val in range(slot,slot+nslots) if val in slot_mapping.keys()]

		if(len(lst)==0):
			for i in range(nslots):
				slot_mapping[slot+i]=src
			return True
		else:
			for l in lst:
				if(kuhn(slot_mapping[l], slot+nslots, slot_mapping)): fl*=1
				else: fl*=0; break

			if(fl):
				for i in range(nslots):
					slot_mapping[slot+i]=src
				return True

	return False

def kuhn2(src, station_index, start_slot=0, slot_mapping=slot_mapping):

	if(used.get(src)!=None): return False
	used[src]=True

	nslots = reqSlots[src]
	for slot in graphs[station_index][src]:
		if slot<start_slot:continue

		fl=1
		lst = [val for val in range(slot,slot+nslots) if val in slot_mapping.keys()]

		if(len(lst)==0):
			for i in range(nslots):
				slot_mapping[slot+i]=src
			return True
		else:
			for l in lst:
				if(kuhn2(slot_mapping[l], station_index, slot+nslots, slot_mapping)): fl*=1
				else: fl*=0; break

			if(fl):
				for i in range(nslots):
					slot_mapping[slot+i]=src
				return True

	return False

def init_schedule(reqSet, slot_mapping = dict()):
	graph.clear()
	requests = [req for req in global_requests if req['index'] in reqSet]
	selected = prebooked_scheduling(requests)
	requests = [req for req in requests if req['index'] in selected]

	createGraph(requests)
	satisfied_requests=0
	# print(nreq)
	for i in [r['index'] for r in requests]:
		used.clear()
		if(kuhn(i,0,slot_mapping)): satisfied_requests+=1

	printSchedule(global_requests, slot_mapping)
	return selected, slot_mapping

def init_schedule(reqSet, station_index, slot_mapping = dict()):
	graphs[station_index] = {}
	requests = [req for req in global_requests if req['index'] in reqSet]
	selected = prebooked_scheduling(requests)
	requests = [req for req in requests if req['index'] in selected]

	createGraph(requests, station_index)
	satisfied_requests=0
	# print(nreq)
	for i in [r['index'] for r in requests]:
		used.clear()
		if(kuhn2(i,station_index,0,slot_mapping)): satisfied_requests+=1

	printSchedule(global_requests, slot_mapping)
	print(graphs)
	return selected, slot_mapping

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
