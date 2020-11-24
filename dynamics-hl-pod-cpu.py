#!/usr/bin/python3

import requests
import json
import os
import glom
import ast
from json import loads

###### Load the config file
cwd = os.getcwd()
with open(f"{cwd}/config.txt", "r") as file:
  data = file.readlines()

arr_data = []
for i in data:
  arr_data.append(i.strip())

controller_host = arr_data[1].rsplit(' ',1)[1]
username = arr_data[4].rsplit(' ',1)[1]
accountname = arr_data[7].rsplit(' ',1)[1]
password = arr_data[10].rsplit(' ',1)[1]
selectedNamespace = arr_data[13].rsplit(' ',1)[1]
alert_template = arr_data[16].rsplit(' ',1)[1]


###### Collect latest server entity (Server, Pod, Container)
url_sim = f"http://{controller_host}:8090/controller/sim/v2/user/machines"
payload = {}
headers = {
  'Content-Type': 'application/json;charset=UTF-8',
  'X-CSRF-TOKEN': '4c6b8ec96e40e97e65e7a07ed2a582359d5c1ca0',
  'Authorization': 'Basic dGNhZG1pbkBjdXN0b21lcjE6R29vZDJkYXk=',
  'Cookie': 'X-CSRF-TOKEN=4c6b8ec96e40e97e65e7a07ed2a582359d5c1ca0; JSESSIONID=966e423ce8e5d0047454e997ab50'
}
response = requests.request("GET", url_sim, headers=headers, data = payload)
string = response.content.decode('utf-8')
json_obj = json.loads(string)
with open(f"{cwd}/entity-response.json", "w+") as file:
	file.write(string)


##### Search Pods in the selected Namespace
with open(f"{cwd}/entity-response.json","r") as file:
	input = json.loads(file.read())

cwd = os.getcwd()

# print((input[5]['properties']['Container|K8S|Namespace']))

list_latest_data = []
try:
  for i in range(len(input)):
    if (input[i]['hierarchy']) and (input[i]['properties']["Container|K8S|Namespace"]) and ((input[i]['properties']['Container|K8S|Namespace']) == selectedNamespace):
      namespace = (input[i]['properties']['Container|K8S|Namespace'])
      podname = (input[i]['properties']['Container|K8S|PodName'])
      list_latest_data.append(f"{namespace}/{podname}")
    else:
      None
except Exception as e:
  pass
# print(list_latest_data)


##### Compare Pods between new pods and existing pods
writepath = f"{cwd}/entity-based.json"
mode = 'r+' if os.path.exists(writepath) else 'w+'
with open(writepath,mode) as f:
	string_based_data = f.read()
	list_based_data = []
	if string_based_data:
		list_based_data = ast.literal_eval(string_based_data)
	else:
		None
	# print(list_based_data)
list_add_data = list(set(list_latest_data) - set(list_based_data))
list_remove_data = list(set(list_based_data) - set(list_latest_data))

# Summary of Pods to be added and Pods to be removed
print(list_add_data)
print(list_remove_data)


##### Write the lastest Pods information to the test-entity-based.json
with open(f"{cwd}/entity-based.json","w") as new:
  new.seek(0)
  new.write(json.dumps(list_latest_data))

##### Get CSRF Token to access Alert API
url_auth = f"http://{controller_host}:8090/controller/auth?action=login"
headers = {'Content-Type': 'application/json'}
r = requests.get(url_auth, auth=(f'{username}@{accountname}', password), headers=headers)
data_cookites = r.cookies.get_dict()
jsessionid = data_cookites['JSESSIONID']
csrf_token = data_cookites['X-CSRF-TOKEN']


##### API POST to add HL from Alert & Respond
for i in range(len(list_add_data)):
  newpodname = list_add_data[i]
  print(newpodname)
  with open(alert_template, 'r') as f:
    data = json.load(f)
    data['name'] = (data['name'].replace('podname',newpodname))
    data['affects']['affectedEntityScope']['affectedEntityName'] = (data['affects']['affectedEntityScope']['affectedEntityName'].replace('podname',newpodname))
    data['evalCriterias']['criticalCriteria']['conditions'][0]['evalDetail']['metricPath'] = (data['evalCriterias']['criticalCriteria']['conditions'][0]['evalDetail']['metricPath']).replace('podname',newpodname)
    data['evalCriterias']['warningCriteria']['conditions'][0]['evalDetail']['metricPath'] = (data['evalCriterias']['warningCriteria']['conditions'][0]['evalDetail']['metricPath']).replace('podname',newpodname)
    data_json = json.dumps(data)
    url = "http://150.109.95.180:8090/controller/alerting/rest/v1/applications/3/health-rules"
    headers = {
  'Content-Type': 'application/json;charset=UTF-8',
  'X-CSRF-TOKEN': csrf_token,
  'Authorization': 'Basic dGNhZG1pbkBjdXN0b21lcjE6R29vZDJkYXk=',
  'Cookie': f'JSESSIONID={jsessionid}; X-CSRF-TOKEN={csrf_token}'
}
    response = requests.request("POST", url, headers=headers, data = data_json)
    print(response.text.encode('utf8'))

###### API DELETE to remove HL from Alert & Respond
url = "http://150.109.95.180:8090/controller/alerting/rest/v1/applications/3/health-rules"

payload = {}
headers = {
  'Content-Type': 'application/json;charset=UTF-8',
  'X-CSRF-TOKEN': csrf_token,
  'Authorization': 'Basic dGNhZG1pbkBjdXN0b21lcjE6R29vZDJkYXk=',
  'Cookie': f'JSESSIONID={jsessionid}; X-CSRF-TOKEN={csrf_token}'
}


response = requests.request("GET", url, headers=headers, data = payload)
string = response.content.decode('utf-8')
data_list = json.loads(string)

try:
  for i in range(len(list_remove_data)):
    search_out = next((item for item in data_list if item["name"] == f"hl-pod-cpu-{list_remove_data[i]}"), None)
    print(search_out["id"])
except Exception as e:
  pass
