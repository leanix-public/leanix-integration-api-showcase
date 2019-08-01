import json 
import requests 
import pandas as pd

api_token = ''
auth_url = 'https://app.leanix.net/services/mtm/v1/oauth2/token' 
request_url = 'https://app.leanix.net/services/integration-ng/v0/' 

# Get the bearer token - see https://dev.leanix.net/v4.0/docs/authentication
response = requests.post(auth_url, auth=('apitoken', api_token),
                         data={'grant_type': 'client_credentials'})
response.raise_for_status() 
header = {'Authorization': 'Bearer ' + response.json()['access_token'], 'Content-Type': 'application/json'}

def createRun(processors, content): 
  data = {
      "connectorType": "ee",
      "connectorId": "Dev",
      "connectorVersion": "0.1",
      "lxWorkspace": "test",
      "lxVersion": "0.0.1",
      "content": content,
      "processors": processors
  }
      
  print (data)
  response = requests.post(url=request_url + 'synchronizationRuns', headers=header, data=json.dumps(data))
  print (response.json())
  return (response.json())

def startRun(run):
  response = requests.post(url=request_url + 'synchronizationRuns/' + run['id'] + '/start?test=false', headers=header)
  
def status(run):
  response = requests.get(url=request_url + 'synchronizationRuns/' + run['id'] + '/status', headers=header)
  return (response.json())  

def getResults(run):
  response = requests.get(url=request_url + 'synchronizationRuns/' + run['id'] + '/results', headers=header)
  return (response.json())  

def processor(fsType): 
  return 	{
		"processorType": "inboundFactSheet",
		"processorName": "Apps from Deployments",
		"processorDescription": "My description",
    "run": 0,
		"type": fsType,
		"identifier": {
			"external": {
				"id": "${content.id}",
				"type": "externalId"
			}
		},
		"filter": { "type": fsType },
		"updates": [ 
      { 
        "key": { "expr": "name" },
				"values": [ { "expr": "${data.name}" }	]
			}	
		]
	}

def relationProcessor(fsType, rel):
  return {
		"processorType": "inboundRelation",
		"processorName": "Rel from Apps to ITComponent",
		"processorDescription": "My description",
		"filter": {
			"type": fsType
		},
		"run": 1,
		"type": rel,
		"from": {
			"external": {
				"type": "externalId",
				"id": "${content.id}"
			}
		},
		"to": {
			"external": {
				"type": "externalId",
				"id": "${data.itc}"
			}
		}
	}

# 1. Read input from XLS
df = pd.read_excel('input.xlsx', sheet_name='Sheet1', sep=';')
apps = set()
itcs = set()
appToITC = {}
for index, row in df.iterrows():
  apps.add(row['Application'])
  itcs.add(row['ITComponent'])
  appToITC[row['Application']] = row['ITComponent']

# 2. Setup content 
content = []
for app in apps:
  content.append({
			"type": "Application",
			"id": app,
			"data": {
				"name": app,
        "itc": appToITC[app]
      }
  })
for itc in itcs:
  content.append({
			"type": "ITComponent",
			"id": itc,
			"data": {
				"name": itc
      }
  })

# 3. Setup processors
processors = [
  processor('Application'),
  processor('ITComponent'),
  relationProcessor('Application', 'relApplicationToITComponent')
]

# 4. Start run and fetch results
run = createRun(processors, content)
startRun(run)
while (True):
  if (status(run)['status'] == 'FINISHED'): break

for result in getResults(run):
  print (str(result['content']) + ' ' + str(result['errors']))
