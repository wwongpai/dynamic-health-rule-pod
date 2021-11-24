import requests
import json
import os
import glom
import re
import shutil
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

##### Get CSRF Token to access Alert API
url_auth = f"http://{controller_host}:8090/controller/auth?action=login"
headers = {'Content-Type': 'application/json'}
r = requests.get(url_auth, auth=(f'{username}@{accountname}', password), headers=headers)
data_cookites = r.cookies.get_dict()
jsessionid = data_cookites['JSESSIONID']
csrf_token = data_cookites['X-CSRF-TOKEN']


###### Collect latest server entity (Server, Pod, Container)
url_sim = f"http://{controller_host}:8090/controller/sim/v2/user/machines"
payload = {}
headers = {
  'Content-Type': 'application/json;charset=UTF-8',
  'X-CSRF-TOKEN': csrf_token,
  'Authorization': 'Basic xxxx',
  'Cookie': f'X-CSRF-TOKEN={csrf_token}; JSESSIONID={jsessionid}'
}
response = requests.request("GET", url_sim, headers=headers, data = payload)
string = response.content.decode('utf-8')
list_d = json.loads(string)
with open(f"{cwd}/entity-response.json", "w+") as file:
	file.write(string)


##### Search Pods in the selected Namespace
cwd = os.getcwd()

list_all_data = []

try:
    for i in range(len(list_d)):
        check = list_d[i].get('properties', {}).get(
            'Container|K8S|Namespace', None)
        if (list_d[i]['hierarchy'] == []):
            machaine_hostname = (list_d[i]['hostId'])
            list_all_data.append(f"{machaine_hostname}")
        elif (list_d[i]['hierarchy']) and (check != None):
            namespace = (list_d[i]['properties']['Container|K8S|Namespace'])
            podname = (list_d[i]['properties']['Container|K8S|PodName'])
            list_all_data.append(f"{namespace}/{podname}")
            list_all_data.append(list_d[i]['hostId'])
        else:
            containername = (list_d[i]['hostId'])
            list_all_data.append(f"{containername}")
except Exception as e:
    pass

print(f"List of All Enitites: {list_all_data}")


list_latest_data = []
try:
    for i in range(len(list_d)):
        check = list_d[i].get('properties', {}).get(
            'Container|K8S|Namespace', None)
        if (list_d[i]['hierarchy']) and (check != None) and ((list_d[i]['properties']['Container|K8S|Namespace']) == selectedNamespace):
            namespace = (list_d[i]['properties']['Container|K8S|Namespace'])
            podname = (list_d[i]['properties']['Container|K8S|PodName'])
            list_latest_data.append(f"{namespace}/{podname}")
        else:
            None
except Exception as e:
    pass

print(f"List of the latest selected Namespace Enitites: {list_latest_data}")

##### Compare Pods between new pods and existing pods
writepath = f"{cwd}/entity-based.json"
mode = 'r+' if os.path.exists(writepath) else 'w+'
with open(writepath, mode) as f:
	string_based_data = f.read()
	list_based_data = []
	if string_based_data:
		list_based_data = ast.literal_eval(string_based_data)
	else:
		None
print(f"List of the previous selected Namespace Enitites: {list_based_data}")
list_add_data = list(set(list_latest_data) - set(list_based_data))
list_remove_data = list(set(list_based_data) - set(list_latest_data))

# Summary of Pods to be added and Pods to be removed
print(f"List of ADDED entities: {list_add_data}")
print(f"List of REMOVED entities: {list_remove_data}")


##### Write the lastest Pods information to the test-entity-based.json
with open(f"{cwd}/entity-based.json","w") as new:
  new.seek(0)
  new.write(json.dumps(list_latest_data))


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
    url = f"http://{controller_host}:8090/controller/alerting/rest/v1/applications/3/health-rules"
    headers = {
  'Content-Type': 'application/json;charset=UTF-8',
  'X-CSRF-TOKEN': csrf_token,
  'Authorization': 'Basic dGNhZG1pbkBjdXN0b21lcjE6R29vZDJkYXk=',
  'Cookie': f'JSESSIONID={jsessionid}; X-CSRF-TOKEN={csrf_token}'
}
    response = requests.request("POST", url, headers=headers, data = data_json)
    print(response.text.encode('utf8'))

###### API DELETE to remove HL from Alert & Respond
url = f"http://{controller_host}:8090/controller/alerting/rest/v1/applications/3/health-rules"

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
