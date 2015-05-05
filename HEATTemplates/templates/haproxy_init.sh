#!/bin/bash -ex
# install dependencies
apt-get update
apt-get -y install build-essential python python-dev python-virtualenv nginx supervisor haproxy


#configure haproxy
sed -i 's/ENABLED=0/ENABLED=1/' /etc/default/haproxy

# save haproxy original configuration
cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy_base.cfg

# write an initial empty list of worker servers
cat >>/etc/haproxy/servers.json <<EOF
[]
EOF

# create a heartbeat user to run the server process
adduser --disabled-password --gecos "" heartbeat

# install the heartbeat application
cd /home/heartbeat
wget https://raw.githubusercontent.com/fokaefs/ASRL_HEAT_Openstack/master/HEATTemplates/templates/heartbeat.py -O heartbeat.py
wget https://raw.githubusercontent.com/fokaefs/ASRL_HEAT_Openstack/master/HEATTemplates/templates/haproxy_update.py -O haproxy_update.py

# create a virtualenv and install dependencies
virtualenv venv
venv/bin/pip install flask gunicorn==18.0

# make the heartbeat user the owner of the application
chown -R heartbeat:heartbeat heartbeat.py

# configure supervisor to run a private gunicorn web server, and
# to autostart it on boot and when it crashes
# stdout and stderr logs from the server will go to /var/log/tiny
mkdir /var/log/heartbeat
cat >/etc/supervisor/conf.d/heartbeat.conf <<EOF
[program:heartbeat]
command=/home/heartbeat/venv/bin/gunicorn -b 127.0.0.1:8000 -w 4 --chdir /home/heartbeat --log-file - heartbeat:heartbeat
user=heartbeat
autostart=true
autorestart=true
stderr_logfile=/var/log/heartbeat/stderr.log
stdout_logfile=/var/log/heartbeat/stdout.log
EOF
supervisorctl reread
supervisorctl update

# configure nginx as the front-end web server with a reverse proxy
# rule to the gunicorn server
cat >/etc/nginx/sites-available/heartbeat<<EOF
server {
    listen 80;
    server_name _;
    access_log /var/log/nginx/tiny.access.log;
    error_log /var/log/nginx/tiny.error.log;
    location / {
         proxy_pass http://127.0.0.1:8000;
         proxy_redirect off;
         proxy_set_header Host \$host;
         proxy_set_header X-Real-IP \$remote_addr;
         proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF
rm -f /etc/nginx/sites-enabled/default
ln -s /etc/nginx/sites-available/heartbeat /etc/nginx/sites-enabled/
service nginx restart