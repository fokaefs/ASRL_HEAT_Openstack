import sys
import json
import subprocess

def update_haproxy():

    current_servers = json.loads(open('/etc/haproxy/servers.json').read())
    
    # generate a new haproxy config file
    f = open('/etc/haproxy/haproxy.cfg', 'wt')
    f.write(open('/etc/haproxy/haproxy_base.cfg').read())
    f.write("""listen app *:80
        mode http
        balance roundrobin
       #option httpchk HEAD / HTTP/1.0
        option httpclose
        option forwardfor
        """)
    for i, server in enumerate(current_servers ):
        f.write('server server-{0} {1}:{2}\n        '.format(i, server, 80))
    f.close()
    # reload haproxy's configuration
    print('Reloading haproxy with servers: ' + ', '.join(current_servers))
    subprocess.call(['service', 'haproxy', 'reload'])
