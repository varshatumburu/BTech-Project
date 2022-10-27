import json, datetime, math
from scheduler import prebooked_scheduling, SLOT_TIME

global_requests = json.load(open('requests.json'))

def roundup(x):
    return int(math.ceil(x / SLOT_TIME)) * int(SLOT_TIME)

graph=dict(); reqSlots = dict()
slot_mapping = dict(); used=dict()
satisfied_requests=0

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

	# print(graph)
	
def printSchedule(request=global_requests):
	# print("Current Schedule: ")
	check=[]
	for key in sorted(slot_mapping.keys()):
		if(slot_mapping[key] in check): continue
		check.append(slot_mapping[key])
		dur = [req for req in request if req['index']==slot_mapping[key]][0]['duration']
		time = datetime.time(int(key*SLOT_TIME)//60, int(key*SLOT_TIME)%60)
		print(f"Request {slot_mapping[key]} scheduled at {time} for {dur} mins.")

def kuhn(src, start_slot=0):
	# print(src, start_slot)
	if(used.get(src)!=None): return False
	used[src]=True
	# print(graph[src])
	# n = len(graph[src])
	nslots = reqSlots[src]
	for slot in graph[src]:
		
		if slot<start_slot:continue
		# if(verifyAvailability(slot, nslots)):
		# 	for s in range(slot, slot+nslots):
		# 		slot_mapping[s]=src
		fl=1
		lst = [val for val in range(slot,slot+nslots) if val in slot_mapping.keys()]
		# print("lst",lst)
		if(len(lst)==0):
			for i in range(nslots):
				slot_mapping[slot+i]=src
			return True
		else:
			for l in lst:
				if(kuhn(slot_mapping[l], slot+nslots)): fl*=1
				else: fl*=0; break

			if(fl):
				for i in range(nslots):
					slot_mapping[slot+i]=src
				return True

	return False

def init_schedule(reqSet):
	slot_mapping.clear(); graph.clear()
	requests = [req for req in global_requests if req['index'] in reqSet]
	selected = prebooked_scheduling(requests)
	requests = [req for req in requests if req['index'] in selected]

	createGraph(requests)
	satisfied_requests=0
	# print(nreq)
	for i in [r['index'] for r in requests]:
		used.clear()
		if(kuhn(i)): satisfied_requests+=1

	printSchedule()
	return selected

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
		# print(graph)

		used.clear()
		if(kuhn(idx)): 
			print("\n>>> REQUEST ACCEPTED! NEW SCHEDULE:")
			satisfied_requests+=1
		else: 
			print("\n>>> REQUEST DENIED. BUSY SCHEDULE.")
		# print(slot_mapping)

		nreq+=1; idx+=1
		printSchedule()

if __name__=='__main__':
	createGraph(global_requests)
	satisfied_requests=0
	# print(nreq)
	for i in [r['index'] for r in global_requests]:
		used.clear()
		if(kuhn(i)): satisfied_requests+=1

	printSchedule()
	dynamic_requests()
