import random
import json

stations = []
for i in range(10):
	new_station = {}
	new_station["node"]=i
	n = random.randint(1,3)
	new_station["ports"] = []
	for j in range(n):
		new_port = {}
		new_port["type"]="Level"+str(random.randint(1,3))+random.choice(["AC","DC"])
		new_port["voltage"]= random.randrange(20,280,10)
		new_port["power"] = random.randint(2,20)
		new_port["vehicles"] = sorted(random.sample(["4w","3w","2w"], k=random.randint(1,3)))
		new_station["ports"].append(new_port)
	stations.append(new_station)

json_object = json.dumps(stations, indent=4)
with open("datasets/charging_stations.json","w") as json_file:
	json_file.write(json_object)


