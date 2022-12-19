import random
import json
import datetime

requests = []
for i in range(100):
	new_request = {}
	new_request["index"]=i
	new_request["duration"] = random.randint(10,70)
	new_request["start_time"]=random.randint(0,720)
	new_request["end_time"]=new_request["start_time"]+new_request["duration"]+random.randint(0,60)
	new_request["Available from"]=str(datetime.time(int(new_request["start_time"])//60, int(new_request["start_time"])%60))
	new_request["Available till"]=str(datetime.time(int(new_request["end_time"])//60, int(new_request["end_time"])%60))
	requests.append(new_request)

json_object = json.dumps(requests, indent=4)
with open("datasets/sample.json","w") as json_file:
	json_file.write(json_object)


