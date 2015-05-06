#!flask/bin/python
from flask import Flask, request
import json
import haproxy_update
import time
import os

app = Flask(__name__)


SECONDS_TO_EXPIRE=60
servers_file='/etc/haproxy/servers.json'
servers={}

def read_servers_json_file():
    global servers
    s = json.loads(open(servers_file).read())
    for srv in s:
        servers[srv] = SECONDS_TO_EXPIRE * 3

def write_json_servers_file():
    global servers
    s = []
    for srv in servers:
        s.append(srv)
    print(s)
    print(open(servers_file, 'r'))
    open(servers_file, 'wt').write(json.dumps(s))



@app.route('/', methods=['GET','POST'])
def hello_world():
    global servers
    worker_ip = request.remote_addr
    print(worker_ip)
    if worker_ip not in servers:
        servers[worker_ip]=SECONDS_TO_EXPIRE
        write_json_servers_file()
        haproxy_update.update_haproxy()
    servers[worker_ip]=SECONDS_TO_EXPIRE

    return 'Hello World!'

def timer_thread_func():
    while True:
        time.sleep(1)
        remove_server = []
        for server in servers:
            if servers[server] > 0:
                servers[server] = servers[server] - 1
                if servers[server] == 0:
                    remove_server.append(server)
        for srv in remove_server:
            servers.pop(srv)
        if len(remove_server) > 0:
            write_json_servers_file()
            haproxy_update.update_haproxy()

if __name__ == '__main__':
    os.spawnl(os.P_NOWAIT, 'timer_thread_func()')
    app.debug = True
    app.run(host='0.0.0.0')
