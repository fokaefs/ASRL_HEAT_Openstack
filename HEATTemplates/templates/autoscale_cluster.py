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

def create_node_group_template(name, flavor, plugin, hadoop_version, node_processes, project_id, token):
    sahara_url = 'http://10.12.1.29:8386/v1.1/{0}/node-group-templates'.format(project_id)
    headers = {'Accept': 'application/json', 'X-Region-Name': 'EDGE-TR-1', 'Content-Type': 'application/json', 'X-Auth-Token': token, 'X-Auth-key': 'bvA2@saq', 'X-Auth-User': 'fokaefs'}
    payload = {"name": name, "flavor_id": flavor, "plugin_name": plugin, "hadoop_version": hadoop_version, "node_processes": node_processes}
    r = requests.post(sahara_url, headers=headers, data=json.dumps(payload))
    response = json.loads(r.text)
    return response['node_group_template']['id']

def create_cluster_template(name, plugin, hadoop_version, node_groups, network, project_id, token):
    sahara_url = 'http://10.12.1.29:8386/v1.1/{0}/cluster-templates'.format(project_id)
    headers = {'Accept': 'application/json', 'X-Region-Name': 'EDGE-TR-1', 'Content-Type': 'application/json', 'X-Auth-Token': token, 'X-Auth-key': 'bvA2@saq', 'X-Auth-User': 'fokaefs'}
    payload = {"name": name, "plugin_name": plugin, "hadoop_version": hadoop_version, "node_groups": node_groups}
    r = requests.post(sahara_url, headers=headers, data=json.dumps(payload))
    response = json.loads(r.text)
    return response['cluster_template']['id']

def random_id():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(30))

def rebuild_nova_servers(project_id, group_name, instance_ids):
    nova_base_url = 'http://tr-edge-1.savitestbed.ca:8774/v2/{0}'.format(project_id)
    headers = {'Accept': 'application/json', 'X-Region-Name': 'EDGE-TR-1', 'Content-Type': 'application/json', 'X-Auth-Token': token, 'X-Auth-key': 'bvA2@saq', 'X-Auth-User': 'fokaefs'}
    group_id = group_name+'_'+random_id()
    for instance in instance_ids:
        nova_url = '{0}/servers/{1}/metadata'.format(nova_base_url, instance)
        payload = { "meta": { "metering.stack": group_id  }  }
        r = requests.post(nova_url, headers=headers, data=json.dumps(payload))
    return group_id

def create_alarm(group_id, scale_up_url):
    ceilometer_url = 'http://tr-edge-1.savitestbed.ca:8777/v2/alarms'
    token = authenticate()
    headers = {'Accept': 'application/json', 'X-Region-Name': 'EDGE-TR-1', 'Content-Type': 'application/json', 'X-Auth-Token': token, 'X-Auth-key': 'bvA2@saq', 'X-Auth-User': 'fokaefs'}
    alarm_name = "cpu_high_"+group_id
    payload = {"alarm_actions": [scale_up_url], "description": "instance running hot", "threshold_rule": {"meter_name": "cpu_util", "evaluation_periods": 1, "period": 60, "statistic": "avg", "threshold": 60.0, "query": [{"field": "matching_metadata", "type": "", "value":{ "metadata.user_metadata.stack": group_id}, "op": "eq"}], "comparison_operator": "gt"}, "type": "threshold", "name": alarm_name}
    r = requests.post(ceilometer_url, headers=headers, data=json.dumps(payload))
    response = json.loads(r.text)
    return response['alarm_id']

@app.route('/scaleCluster', methods=['GET','POST'])
def scale_cluster():
    project_id = request.args.get('project_id','')
    cluster_id = request.args.get('cluster_id','')
    node_group = request.args.get('node_group','')
    adjustment = int(request.args.get('adjustment',''))
    sahara_url = 'http://10.12.1.29:8386/v1.1/{0}/clusters/{1}'.format(project_id,cluster_id)
    r = requests.get(sahara_url)
    response = json.loads(r.text)
    node_groups = response['cluster']['node_groups']
    count = 0
    for group in node_groups:
        if group['name'] == node_group:
            count = group['count']
    count = count + adjustment
    payload = { "resize_node_groups": [ { "count": count, "name": node_group } ] }
    r = requests.put(sahara_url, headers=headers, data=json.dumps(payload))
    return r.text

@app.route('/cluster', methods=['GET','POST'])
def cluster():
    project_id = request.args.get('project_id','')
    template_name = request.args.get('template_name', '')
    hadoop_version = request.args.get('hadoop_version','')
    #network = request.args.get('network', '')
    plugin_name = request.args.get('plugin_name', '')
    master_count = request.args.get('master_count', '')
    worker_count = request.args.get('worker_count', '')
    image = request.args.get('image', '')
    key_name = request.args.get('key_name', '')
    cluster_name = request.args.get('cluster_name', '')
    master_flavor = request.args.get('master_flavor', '')
    master_template_name = request.args.get('master_template_name', '')
    worker_flavor = request.args.get('worker_flavor', '')
    worker_template_name = request.args.get('worker_template_name', '')
    adjustment = request.args.get('adjustment','')

    master_node_processes = ["master", "namenode"]
    worker_node_processes = ["slave", "datanode"]
    token = authenticate()

    master_template_id = create_node_group_template(master_name_template, master_flavor, plugin_name, hadoop_version, master_node_processes, project_id, token)
    worker_template_id = create_node_group_template(worker_name_template, worker_flavor, plugin_name, hadoop_version, worker_node_processes, project_id, token)

    master_node_group = { "name": "master", "node_group_template_id": master_template_id, "count": master_count }
    worker_node_group = { "name": "workers", "node_group_template_id": worker_template_id, "count": worker_count }
    node_groups = [ master_node_group, worker_node_group ]

    cluster_template_id = create_cluster_template(template_name, plugin_name, hadoop_version, node_groups, network, project_id, token)

    sahara_url = 'http://10.12.1.29:8386/v1.1/{0}/clusters'.format(project_id)
    headers = {'Accept': 'application/json', 'X-Region-Name': 'EDGE-TR-1', 'Content-Type': 'application/json', 'X-Auth-Token': token, 'X-Auth-key': 'bvA2@saq', 'X-Auth-User': 'fokaefs'}
    payload = { "plugin_name": plugin_name, "hadoop_version": hadoop_version, "cluster_template_id": cluster_template_id, "default_image_id": image, "user_keypair_id": key_name, "name": cluster_name}
    r = requests.post(sahara_url, headers=headers, data=json.dumps(payload))
    response = json.loads(r.text)
    cluster_id = repsonse['cluster']['id']
    sahara_url = sahara_url+'/{0}'.format(cluster_id)
    r = requests.get(sahara_url)
    response = json.loads(r.text)
    instances_per_group = {}
    for node_group in response['cluster']['node_groups']:
        name = node_group['name']
        group_instances = []
        for instance in node_group['instances']:
            group_instances.append(instance['id'])
        instances_per_group[name]=group_instances
    for group,instances in instances_per_group:
        group_id = rebuild_nova_servers(project_id, group, instances)
        scale_up_url = 'http://142.150.208.240:5000/scaleCluster?project_id={0}&cluster_id={1}&name={2}&adjustment={3}'.format(project_id,cluster_id,group,adjustment)
        create_alarm(group_id, scale_up_url)
    return r.text


if __name__ == '__main__':
    app.run(host='0.0.0.0')
