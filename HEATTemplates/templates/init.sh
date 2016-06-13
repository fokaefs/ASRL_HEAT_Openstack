# init scripts for LEGIS topology
#
# name: legis-manager
# image: Ubuntu-1404-64B
# size: m1.medium
#
apt-get upgrade
apt-get -y install apache2
sudo a2enmod proxy
sudo a2enmod proxy_balancer
sudo a2enmod proxy_http
sudo a2enmod proxy_ajp
sudo a2enmod proxy_connect
sudo a2enmod lbmethod_bybusyness
sudo a2enmod lbmethod_byrequests

sudo apt-add-repository ppa:webupd8team/java
sudo apt-get update
sudo apt-get install oracle-java8-installer
sudo apt-get install unzip

sudo cp /etc/apache2/mods-available/proxy.conf /etc/apache2/mods-available/proxy_bkp.conf
sudo rm /etc/apache2/mods-available/proxy.conf
sudo wget https://bitbucket.org/corbar/docker-load-balancer/raw/87d46d6a5219c6456bf22f3e6b56d009668abd18/lb-conf/proxy.conf -O /etc/apache2/mods-available/proxy.conf

sudo cp /etc/apache2/mods-available/proxy_balancer.conf /etc/apache2/mods-available/proxy_balancer_bkp.conf
sudo rm /etc/apache2/mods-available/proxy_balancer.conf
sudo wget https://bitbucket.org/corbar/docker-load-balancer/raw/87d46d6a5219c6456bf22f3e6b56d009668abd18/lb-conf/proxy_balancer.conf -O /etc/apache2/mods-available/proxy_balancer.conf

sudo cp /etc/apache2/mods-available/ports.conf /etc/apache2/mods-available/ports_bkp.conf
sudo rm /etc/apache2/mods-available/ports.conf
sudo wget https://bitbucket.org/corbar/docker-load-balancer/raw/87d46d6a5219c6456bf22f3e6b56d009668abd18/lb-conf/ports.conf -O /etc/apache2/mods-available/ports.conf

sudo wget https://bitbucket.org/corbar/docker-load-balancer/raw/87d46d6a5219c6456bf22f3e6b56d009668abd18/scripts/lb-add-worker.sh -O /lb-add-worker.sh
sudo wget https://bitbucket.org/corbar/docker-load-balancer/raw/87d46d6a5219c6456bf22f3e6b56d009668abd18/scripts/lb-rm-worker.sh -O /lb-rm-worker.sh

./lb-add-worker.sh $HOST_IP

sudo curl -s http://d3kbcqa49mib13.cloudfront.net/spark-1.6.1-bin-hadoop2.6.tgz | tar -xz -C /usr/local/
sudo mv /usr/local/spark-1.6.1-bin-hadoop2.6 /usr/local/spark

mkdir /job-dependencies
wget http://rodrigoveleda.com/itec/dependency.zip -O /job-dependencies/dependency.zip
unzip /job-dependencies/dependency.zip -d /job-dependencies

wget https://bitbucket.org/corbar/docker-spark.legis/raw/c892cae99643b4a217f87318debe0f717d337d37/jars/spark-cassandra-connector-assembly-1.6.0-M1-s_2.10.jar -O /spark-cassandra-connector-assembly-1.6.0-M1-s_2.10.jar
wget https://bitbucket.org/corbar/docker-spark.legis/raw/c892cae99643b4a217f87318debe0f717d337d37/scripts/spark-defaults.conf -O /spark-defaults.conf

/usr/local/spark/sbin/start-master.sh --properties-file /spark-defaults.conf --host ${SPARK_LOCAL_IP}
#
# name: legis-web
# image: Ubuntu-1404-64B
# size: m1.small
#
apt-get upgrade
sudo apt-add-repository ppa:webupd8team/java
sudo apt-get update
sudo apt-get install oracle-java8-installer
#add JAVA_HOME=/usr/lib/jvm/java-8-oracle in /etc/environment

sudo apt-get install -y tomcat7

sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 9200
wget https://bitbucket.org/corbar/docker-webapp.legis/raw/6baacda423b510b4a6645067827c1bbe170ada8d/tomcat7/context.xml -O /var/lib/tomcat7/conf/context.xml 
wget https://bitbucket.org/corbar/docker-webapp.legis/raw/6baacda423b510b4a6645067827c1bbe170ada8d/webapp/webapp-legis.war -O /var/lib/tomcat7/webapps/webapp-legis.war
service tomcat7 start



# name: legis-spark
# image: Ubuntu-1404-64B
# size: m1.small
apt-get upgrade
apt-add-repository ppa:webupd8team/java
apt-get update
apt-get install oracle-java8-installer
sudo vim ~/.bashrc #add the line: export JAVA_HOME="/usr/lib/jvm/java-8-oracle/jre/bin/java"
source ~/.bashrc
apt-get install unzip

curl -s http://d3kbcqa49mib13.cloudfront.net/spark-1.6.1-bin-hadoop2.6.tgz | tar -xz -C /usr/local/
mv /usr/local/spark-1.6.1-bin-hadoop2.6 /usr/local/spark

mkdir /job-dependencies
wget http://rodrigoveleda.com/itec/dependency.zip -O /job-dependencies/dependency.zip
unzip /job-dependencies/dependency.zip -d /job-dependencies

wget https://bitbucket.org/corbar/docker-spark.legis/raw/c892cae99643b4a217f87318debe0f717d337d37/jars/spark-cassandra-connector-assembly-1.6.0-M1-s_2.10.jar -O /spark-cassandra-connector-assembly-1.6.0-M1-s_2.10.jar
wget https://bitbucket.org/corbar/docker-spark.legis/raw/c892cae99643b4a217f87318debe0f717d337d37/scripts/spark-defaults.conf -O /spark-defaults.conf

/usr/local/spark/bin/spark-class org.apache.spark.deploy.worker.Worker spark://${SPARK_MASTER_IP}:${SPARK_MASTER_PORT} --properties-file /spark-defaults.conf --host ${SPARK_LOCAL_IP}