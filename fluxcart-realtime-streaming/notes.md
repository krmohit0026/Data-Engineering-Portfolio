### Kafka pipeline

FluxCart is e-commerce platform. 

every time a user browses a product, places an order or makes payment --> event


**kafka === post office**

**topics --> mailboxes**

**producers --> people who drop letters(events) into the mailboxes**

**consumers --> people who pick those letters(events) form the mailboxes**

**brokers --> post office building (servers) that store the mailboxes**

### Docker and kafka cluster

 **docker compose up -d     --> start the container**

**docker ps --> to enlist all the running containers**

**docker logs fluxcart-broker-1 | grep -i "started"**

*-- container running != kafka ready  ----> but ---> container running + "started" in logs = kafka ready*

#### Now verify if all 3 brokers are registered with the cluster

docker exec fluxcart-broker-1 kafka-broker-api-versions --bootstrap-server localhhost:9092


### kRaft Mode


### Topics and Paritions



### Producers


### Consumers


### Consumer Groups


### Offsets and Manual commits


### Dead letter queues



### Fault tolerance and Replication


### Producer-from-Consumer pattern


## order to build pipeline

docker-compose.yml --> cluster config

config.py --> shared foundation 

models.py --> event design before producer 

setup_topics.py --> topics must exist before producer can write

producer.py --> write events before teaching how to read them

base_consumer.py --> loop everything

analytics.py 

fraud.py 

inventory.py

run_pipeline.py. --> run everything together
