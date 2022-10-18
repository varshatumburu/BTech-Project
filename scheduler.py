# weighted job scheduling
import json 
from functools import total_ordering
import datetime
import math

SLOT_TIME = 10
# requests = json.load(open('requests.json'))
# stations = json.load(open('charging_stations.json'))

@total_ordering
class Job:
	def __init__(self, index, start, end, duration):
		self.start = start
		self.end = end
		self.index = index
		self.duration = duration

	def __repr__(self) -> str:
		return "{"+str(self.index)+","+str(self.start)+"-"+str(self.end)+"}"

	def __lt__(self, other: object) -> bool:
		return self.end< other.end


def optimalNonConflict(arr, i, vis , sorted_list):
	# for j in range(i-1, -1, -1):
	# 	if(arr[j].end <= arr[i].start and (arr[i].index not in vis[j])):
	# 		return j
	for j in sorted_list:
		if(arr[j[2]].end <= arr[i].start and (arr[i].index not in vis[j[2]])):
			return j[2]
		
	return -1

def optimize(jobs):
	n=len(jobs)
	# print(jobs)

	total_time = [0] * n; global_dp = [0] * n
	total_time[0]=jobs[0].duration 
	global_dp[0]=total_time[0]

	vis = {x:set() for x in range(0,n)}
	gdp_vis = {x:set() for x in range(0,n)}
	used = {y:[] for y in range(0,n)}

	vis[0].add(jobs[0].index)
	gdp_vis[0].add(jobs[0].index)
	used[0].append(0)

	sl = list()
	sl.append(tuple([global_dp[0],1,0]))

	idx=0
	for i in range(1, n):

		dur = jobs[i].duration 
		l = optimalNonConflict(jobs, i, vis, sl)

		# Add to duration if non-overlapping slot is found 
		if l!=-1:
			if jobs[i].index in vis[l]: 
				continue
			dur += total_time[l]
			vis[i]=vis[l].copy()
			used[i]=used[l].copy()

		# print(i,dur)

		total_time[i]=dur
		vis[i].add(jobs[i].index)
		used[i].append(i)

		if(total_time[i]>global_dp[i-1] or (total_time[i]==global_dp[i-1] and len(vis[i])>len(gdp_vis[i-1]))):
			global_dp[i]=total_time[i]
			gdp_vis[i]=vis[i]
			idx=i
		else:
			global_dp[i]=global_dp[i-1]
			gdp_vis[i]=gdp_vis[i-1]

		sl.append(tuple([global_dp[i], len(vis[i]), i]))
		sl.sort(reverse=True)

	return global_dp[n-1],used[idx]


def prebooked_scheduling(requests):

	permuted_jobs = []
	for r in requests:
		interval = r['duration']
		s = math.ceil(r['start_time']/SLOT_TIME) * SLOT_TIME

		for start in range(s, r['end_time'], SLOT_TIME):
			if(start+interval > r['end_time']): break
			permuted_jobs.append(Job(r['index'], start, start+interval, interval))

	permuted_jobs=sorted(permuted_jobs)
	optimized_time, used_intervals = optimize(permuted_jobs)

	# selected_jobs = dict()
	# time_mapping = dict()
	# print("Slot Time =", SLOT_TIME, "mins")
	# for interval in used_intervals:
	# 	# selected_jobs[permuted_jobs[interval].index]=permuted_jobs[interval]
	# 	for i in range(permuted_jobs[interval].start, permuted_jobs[interval].start + permuted_jobs[interval].duration, SLOT_TIME):
	# 		time_mapping[i]=permuted_jobs[interval].index
	# 	time = datetime.time(permuted_jobs[interval].start//60, permuted_jobs[interval].start%60)
	# 	print(f"Request {permuted_jobs[interval].index} scheduled at {time} for {permuted_jobs[interval].duration} mins.")

	scheduled_job_indices = [permuted_jobs[interval].index for interval in used_intervals]
	return scheduled_job_indices
