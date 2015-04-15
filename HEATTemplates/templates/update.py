import sys
import json
import subprocess

# load server list from metadata
metadata = json.loads(sys.stdin.read())
new_servers = json.loads(metadata.get('meta', {}).get('servers', '[]'))
if not new_servers:
    sys.exit(1)  # bad metadata

# generate a new haproxy config file
f = open('/etc/apache2/mods-available/proxy_balancer.conf', 'wt')
f.write("""
<IfModule mod_proxy_balancer.c>
ProxyPass /balancer-manager !
ProxyPass / balancer://Valhalla_Cluster/
<Proxy balancer://Valhalla_Cluster>
""")
for i, server in enumerate(new_servers):
    f.write(' BalancerMember http://{0}:80\n'.format(server))
f.write("""
</Proxy>
<Location /balancer-manager>
  SetHandler balancer-manager
</Location>
</IfModule>
""")
f.close()
# reload haproxy's configuration
subprocess.call(['service', 'apache2', 'reload'])
