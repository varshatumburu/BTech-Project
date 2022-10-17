import json, datetime, math

SLOT_TIME = 10.0
TOTAL_SLOTS = 24*6 

def roundup(x):
    return int(math.ceil(x / SLOT_TIME)) * int(SLOT_TIME)

requests = json.load(open('requests.json'))
requests = [requests[r] for r in {1, 2, 3, 6}]
nreq = len(requests)

graph=dict(); reqSlots = dict()
for req in requests:
	st = roundup(req['start_time'])
	nslots = int(math.ceil(req['duration']/SLOT_TIME))
	reqSlots[req['index']]=nslots

	# if st + req['duration']>req['end_time']: continue

	matchedSlots=[]
	i=1
	while st + req['duration']<=req['end_time']:
		matchedSlots.append(int(st/SLOT_TIME))
		st+=SLOT_TIME; i+=1
		# while i<nslots:
		# 	matchedSlots.append(int(st/SLOT_TIME))
		# 	st+=SLOT_TIME; i+=1
	# print(req['index'],matchedSlots)
	graph[req['index']]=(matchedSlots)

# print(graph)
mt = dict(); used=dict()
def verifyAvailability(slot, nslots):
	for i in range(nslots):
		if(mt.get(slot)!=None): 
			print(mt[slot])
		if(mt.get(slot)!=None and not(kuhn(mt[slot]))):
			print("slot",slot, mt[slot])
			return False
		slot+=1
	return True

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
		# 		mt[s]=src
		fl=1
		lst = [val for val in range(slot,slot+nslots) if val in mt.keys()]
		# print("lst",lst)
		if(len(lst)==0):
			for i in range(nslots):
				mt[slot+i]=src
			return True
		else:
			for l in lst:
				if(kuhn(mt[l], slot+nslots)): fl*=1
				else: fl*=0; break

			if(fl):
				for i in range(nslots):
					mt[slot+i]=src
				return True

	return False

satisfied_requests=0
# print(nreq)
for i in [r['index'] for r in requests]:
	used.clear()
	if(kuhn(i)): satisfied_requests+=1


def printSchedule():
	for key in sorted(mt.keys()):
		time = datetime.time(int(key*SLOT_TIME)//60, int(key*SLOT_TIME)%60)
		print(f"Request {mt[key]} scheduled at {time}.")

printSchedule()

idx = max([r['index'] for r in requests])+1
while input("Enter new request: (-1 to break)")!="-1":
	duration = int(input("Enter duration: "))
	start_time = int(input("Enter start of availability: "))
	end_time = int(input("Enter end time of availability: "))

	requests.append({
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
	print(graph)

	used.clear()
	if(kuhn(idx)): satisfied_requests+=1
	print(mt)

	nreq+=1; idx+=1
	printSchedule()



