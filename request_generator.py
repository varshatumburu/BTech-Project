import random
import json
import datetime

requests = []
for i in range(100):
	new_request = {}
	new_request["index"]=i
	new_request["duration"] = random.randint(10,70)
	new_request["start_time"]=random.randint(0,1440-new_request["duration"])
	new_request["end_time"]=new_request["start_time"]+new_request["duration"]+random.randint(0,int(min(60,1440-new_request["start_time"]-new_request["duration"])))
	if(new_request["end_time"]==1440): new_request["end_time"]-=1
	new_request["Available from"]=str(datetime.time(int(new_request["start_time"]//60), int(new_request["start_time"])%60))
	new_request["Available till"]=str(datetime.time(int(new_request["end_time"]//60), int(new_request["end_time"])%60))
	new_request["current_soc"] = random.randint(2,20)
	new_request["battery_capacity"]=random.randint(40,80)
	new_request["mileage"] = random.randint(50,400)
	new_request["vehicle_type"] = random.choice(["4w","3w","2w"])
	requests.append(new_request)

json_object = json.dumps(requests, indent=4)
with open("datasets/requests.json","w") as json_file:
	json_file.write(json_object)


