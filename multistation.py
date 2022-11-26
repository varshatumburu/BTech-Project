import json, math
import matching
from scheduler import SLOT_TIME
from ast import literal_eval

distances = []
slotMapping = dict()
def roundup(x):
    return int(math.ceil(x / SLOT_TIME)) * int(SLOT_TIME)

def calcStationDistances(requests, stations):
	for r in requests:
		x=r['location'][0]; y=r['location'][1]
		row=[]
		for s in stations:
			a=s['location'][0]; b=s['location'][1]
			row.append(math.sqrt((x-a)**2 + (y-b)**2))
		distances.append(row)

def createMapping():
	reqMapping = dict()
	for i,r in enumerate(requests):
		st = distances[i].index(min(distances[i]))
		if reqMapping.get(st)==None or len(reqMapping[st])==0:
			reqMapping[st]=[]

		reqMapping[st].append(i)

	return reqMapping

def iterative_scheduling(blocked, leftover, reqMapping):
	iter=0; prev=-1
	while len(blocked)!=len(requests) and prev!=len(blocked):
		print(f"\n>>> Iteration {iter} >>> ")
		for i,st in enumerate(stations):
			prev=len(blocked)
			print(f"\nSchedule for Station {st['index']}:")
			# print(reqMapping[id])
			reqidx = reqMapping[st['index']]
			# new_additions = [i for i in leftover if i not in reqidx]
			# reqidx.extend(new_additions)

			selected, slotMapping[i] = matching.init_schedule(reqidx, i, dict())
			leftover = list(set(reqidx)-set(selected))

			# print(leftover)
			for l in leftover:
				distances[l][i]=1e9
				if(min(distances[l])==1e9): continue
				sti = distances[l].index(min(distances[l]))
				reqMapping[i].remove(l)
				reqMapping[sti].append(l)

			blocked = set(list(blocked)+list(selected))

		if(prev==len(blocked)): break
		iter+=1

	print("\nCompleted scheduling!")

if __name__=="__main__":
	stations = json.load(open('charging_stations.json'))
	requests = json.load(open('requests.json'))	

	calcStationDistances(requests, stations)
	requestMapping = createMapping()

	blocked=set(); leftover=[]

	iterative_scheduling(blocked, leftover, requestMapping)

	while input("-----------------------\nEnter to go to new request: (-1 to break)")!="-1":
		curr_idx = len(requests)
		print(f"Request #{curr_idx}")
		duration = int(input("Enter duration: "))
		start_time = int(input("Enter start of availability: "))
		end_time = int(input("Enter end time of availability: "))
		location = literal_eval(input("Enter coordinates of user location (eg.(0,0)): "))
		
		new_request = {
			"index":curr_idx,
			"duration": duration,
			"start_time": start_time,
			"end_time": end_time,
			"location": location
		}
		requests.append(new_request)
		calcStationDistances([new_request], stations)

		sortedStations = [i[0] for i in sorted(enumerate(distances[curr_idx]), key = lambda x:x[1])]

		st = roundup(start_time)
		nslots = int(math.ceil(duration/SLOT_TIME))
		matching.reqSlots[curr_idx]=nslots
		matchedSlots=[]
		while st + duration<=end_time:
			matchedSlots.append(int(st/SLOT_TIME))
			st+=SLOT_TIME

		# matching.graph[curr_idx]=(matchedSlots)
		# print("ok",matching.graph)
		flag=0

		for s in sortedStations:
			matching.graphs[s][curr_idx]= matchedSlots
			requestMapping[s].append(curr_idx)

			matching.used.clear()
			if(matching.kuhn(curr_idx, 0, slotMapping[s], s)): 
				print("\n>>> REQUEST ACCEPTED! NEW SCHEDULE:")
				matching.satisfied_requests+=1
				print(f"\nAccommodated in Station {s}:")
				matching.printSchedule(requests, slotMapping[s])
				flag=1
				break
			else:
				requestMapping[s].remove(curr_idx)
				del matching.graphs[s][curr_idx]

		if(flag==0):
			print("\n>>> REQUEST DENIED.")




