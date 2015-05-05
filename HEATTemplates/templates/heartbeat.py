from flask import Flask, request
import json
import haproxy_update

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
    open(servers_file, 'wt').write(json.dumps(s))



@app.route('/', methods=['GET','POST'])
def hello_world():
    worker_ip = request.remote_addr
    if worker_ip not in servers:
        write_json_server_file()
        update.update_haproxy()
    servers[worker_ip]=SECONDS_TO_EXPIRE

    return 'Hello World!'

def timer_thread_func():
    while True:
        sleep(1)
        remove_server = []
        for server in servers:
            if servers[server] > 0:
                servers[server] = servers[server] - 1
                if servers[server] == 0:
                    remove_server.append(server)
        for srv in remove_server:
            servers.pop(srv)
        if len(remove_server) > 0:
            write_servers_to_file()
            update.update_haproxy()

if __name__ == '__main__':
    read_servers_json_file()
    update.update_haproxy()
    start_timer_thread()

    app.run(host='0.0.0.0')
