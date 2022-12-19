# contains all the configurable variables to maintain state of user

import pandas as pd
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="Slot Scheduling App")

CENTER = None
CS_DROPDOWN = pd.DataFrame(columns = ['label','value'])
CS_NODES = []
CS_POSITIONS = []
COLUMNS = []
DATASET = 'datasets/sample.json'
GRAPH = None
LOCATION = geolocator.geocode("India")
N_CLICKS = 0
NEAREST_CS = dict()
POLYGON = []
POSITIONS = 0
REQUESTS = pd.DataFrame()
REQUESTS_DROPDOWN = pd.DataFrame(columns = ['label','value'])
REQUEST_MAPPING = dict()
REQUEST_NODES = []
SCHED_CLICKS = 0
SLOT_MAPPING = {}
TOTAL_NODES = 0
TOTAL_STATIONS = 0
X_NODES = []
Y_NODES = []
ZOOM_LEVEL = 0