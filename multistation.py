import json, math
import matching

distances = []
def stationDistances(requests, stations):
	for r in requests:
		[x,y]=r['location']
		row=[]
		for s in stations:
			[a,b]=s['location']
			row.append(math.sqrt((x-a)**2 + (y-b)**2))
		distances.append(row)

if __name__=="__main__":
	stations = json.load(open('charging_stations.json'))
	requests = json.load(open('requests.json'))	

	stationDistances(requests, stations)
	# print(distances)
	
	reqMapping = dict()
	for i,r in enumerate(requests):
		st = distances[i].index(min(distances[i]))
		if reqMapping.get(st)==None or len(reqMapping[st])==0:
			reqMapping[st]=[]

		reqMapping[st].append(i)

	# print(reqMapping)
	blocked=set(); leftover=[]
	prev=-1; iter=1

	while len(blocked)!=len(requests) and prev!=len(blocked):
		print(f"\n>>> Iteration {iter} >>> ")
		for i,st in enumerate(stations):
			prev=len(blocked)
			print(f"\nSchedule for Station {st['index']}:")
			# print(reqMapping[id])
			reqidx = reqMapping[st['index']]
			new_additions = [i for i in leftover if i not in reqidx]
			reqidx.extend(new_additions)

			selected = matching.init_schedule(reqidx)
			leftover = list(set(reqidx)-set(selected))

			# print(leftover)
			for l in leftover:
				distances[l][i]=1e9
				sti = distances[l].index(min(distances[l]))
				reqMapping[i].append(l)

			blocked = set(list(blocked)+list(selected))

		if(prev==len(blocked)): break
		iter+=1
		# print(blocked)
	print("\nCompleted scheduling!")


