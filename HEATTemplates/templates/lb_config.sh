#!/bin/bash
apt-get update
apt-get install -y apache2
if [ -f "/var/run/apache2.pid" ]; then
	sudo /etc/init.d/apache2 stop
fi
echo "<IfModule mod_proxy_balancer.c>
ProxyPass /balancer-manager !
ProxyPass / balancer://Valhalla_Cluster/
<Proxy balancer://Valhalla_Cluster>
 BalancerMember http://www.google.com
 BalancerMember http://www.yahoo.com
</Proxy>
<Location /balancer-manager>
  SetHandler balancer-manager
</Location>
</IfModule>" | tee /etc/apache2/mods-available/proxy_balancer.conf


echo "<IfModule mod_proxy.c>
ProxyRequests Off

  <Proxy *>
    AddDefaultCharset off
    Order deny,allow
    Allow from all
  </Proxy>
ProxyVia On
</IfModule>" | tee /etc/apache2/mods-available/proxy.conf


a2enmod proxy
a2enmod proxy_balancer
a2enmod proxy_http
a2enmod proxy_ajp
a2enmod proxy_connect

service apache2 start
