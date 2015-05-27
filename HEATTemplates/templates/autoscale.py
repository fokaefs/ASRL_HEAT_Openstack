#!flask/bin/python
from flask import Flask, json, jsonify, request
import requests
import random
import string
#import timer

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello World"

@app.route('/authenticate')
def authenticate():
    keystone_url = "http://iam.savitestbed.ca:5000/v2.0"
    authenticate_url = "/tokens"
    payload = { "auth": { "tenantName": "yorku", "passwordCredentials": { "username": "fokaefs", "password": "bvA2@saq" } } }
    headers = {'content-type': 'application/json'}
    r = requests.post(keystone_url+authenticate_url, headers=headers, data=json.dumps(payload))
    response = json.loads(r.text)
    return response['access']['token']['id']

def get_stack_id(project_id, stack_name, token):
    heat_url = 'http://10.12.1.70:8004/v1/{0}/stacks/{1}'.format(project_id, stack_name)
    print(heat_url)
    headers = {'Accept': 'application/json', 'X-Region-Name': 'EDGE-MG-1', 'Content-Type': 'application/json', 'X-Auth-Token': token, 'X-Auth-key': 'bvA2@saq', 'X-Auth-User': 'fokaefs'}
    r = requests.get(heat_url, headers=headers)
    response = json.loads(r.text)
    print(response['stack']['id'])
    return response['stack']['id']

@app.route('/scale', methods=['GET','POST'])
def scale():
    project_id = request.args.get('project_id', '')
    stack_name = request.args.get('stack_name', '')
    token = authenticate()
    #stack_id = request.args.get('stack_id', '')
    stack_id = request.args.get('stack_id','')
    adjustment = int(request.args.get('adjustment', ''))
    parameters = eval(request.args.get('parameters',''))
    cluster_size = int(parameters['cluster_size']) + adjustment
    min_cluster_size = int(parameters['min_cluster_size'])
    template_url = parameters['template_url']
    #cooldown = 120
    print(cluster_size)
    if cluster_size < min_cluster_size:
        print("Adjusted cluster size is below the minimum number of worker nodes. Stack update was not initiated.")
        return "Adjusted cluster size is below the minimum number of worker nodes. Stack update was not initiated."
    parameters['cluster_size'] = cluster_size
    url = 'http://10.12.1.70:8004/v1/{0}/stacks/{1}/{2}'.format(project_id, stack_name, stack_id)
    headers = {'Accept': 'application/json', 'X-Region-Name': 'EDGE-MG-1', 'Content-Type': 'application/json', 'X-Auth-Token': token, 'X-Auth-key': 'bvA2@saq', 'X-Auth-User': 'fokaefs'}
    payload = { 'files': {}, 'environment': {}, 'parameters': parameters, 'template_url': template_url }
    r = requests.put(url, headers=headers, data=json.dumps(payload))
    print(r.text)
    #timer.sleep(120)
    return r.text
    #return "http://10.12.1.70:8004/v1/{0}/stacks/{1}/{2}?template_url={3}".format(project_id, stack_name, stack_id, template_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
