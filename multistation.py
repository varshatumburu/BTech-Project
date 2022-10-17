import json
import sched
from scheduler import scheduling

stations = json.load(open('charging_stations.json'))
requests = json.load(open('requests.json'))

def findNearestStation(coordinates):
	mn = 1e9; x1=coordinates[0]; y1=coordinates[1]
	idx=0
	for c in stations:
		if((x1-c['location'][0])**2 + (y1-c['location'][1])**2<mn):
			mn = (x1-c['location'][0])**2 + (y1-c['location'][1])**2
			idx = c['index']
	return idx 

reqMapping = dict()
for i,r in enumerate(requests):
	st = findNearestStation(r['location'])
	if reqMapping.get(st)==None or len(reqMapping[st])==0:
		reqMapping[st]=[]

	reqMapping[st].append(i)

leftover=[]
for st in stations:
	print(f"\nStation {st['index']}:")
	# print(reqMapping[id])
	reqidx = reqMapping[st['index']]
	reqidx.extend(leftover)
	# print(reqidx)
	req = [requests[i] for i in reqidx]
	indices = scheduling(req)
	leftover = list(set(reqidx)-set(indices))
	# print(leftover)


