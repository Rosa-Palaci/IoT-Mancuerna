'''
Install paho-mqtt run this command in the terminal:  pip install paho-mqtt
A nice tutorial is here: https://pypi.org/project/paho-mqtt/
'''
import pymysql
import random
from paho.mqtt import client as mqtt_client

broker = 'localhost'
port = 1884

topic = "rescue"
client_id = "python-mqtt-0x"
username = 'bridge1'
password = 'bridge123456789'
table = 'events'
counter = 25
def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def subscribe(client: mqtt_client, dbconn):
    def on_message(client, userdata, msg):
        line = str(msg.payload.decode())
        print("value of message: "+line)
        line_sp = line.split(":")
        node_id = line_sp[0]
        print('nodeid: '+ node_id)
        severity = line_sp[1]
        print('severity: '+severity)
        lat_long = line_sp[2]
        print('lat_long: '+lat_long)
        lat_long_sp = lat_long.split(",")
        lat = lat_long_sp[0]
        lon = lat_long_sp[1]
        counter = 25

        color = '1'
        if severity == 'Medium':
            color = '2'
        if severity == 'High':
            color = '3'


        cursor = dbconn.cursor()
        cursor.execute("INSERT INTO events  (lat,lon,color) VALUES (%s, %s, %s);",(lat,lon,color))

        dbconn.commit()
        counter = counter+1
        

    client.subscribe(topic)
    client.on_message = on_message

def run():
    counter = 28
    client = connect_mqtt()
    dbconn = pymysql.connect(host='localhost', port=3306, db='events', user='sammy', passwd='password')
    subscribe(client, dbconn)
    client.loop_forever()

run()