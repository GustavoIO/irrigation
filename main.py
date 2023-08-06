import paho.mqtt.client as mqtt
from datetime import datetime
import time
import json
import os
import gpiozero

def publishDiscoveryMessage(client, zone, zoneData):
    payload = json.dumps(zoneData['description'])
    client.publish(zoneData['discovery_topic'], payload, 0, retain=True)

def publishAvailability(client, zone, zoneData, availability):
    client.publish(zoneData['description']['availability']['topic'], availability, 0, retain=True)

def publishState(client, zone, zoneData, state):
    client.publish(zoneData['description']['state_topic'], state, 0, retain=True)

def turnAllZonesOff(zones):
    for zone in zones:
        turnZoneOff(zones[zone])

def turnZoneOff(zone):
    print("Turning zone " + str(zone["gpio"]) + " off")
    zone["gpio"].off()
    zone['state'] = 'off'

def turnZoneOn(zone):
    print("Turning zone " + str(zone["gpio"]) + " on")
    zone["gpio"].on()
    zone['state'] = 'on'

def onConnect(client, userdata, flags, rc):
    print("Connected: " + str(rc))
    zones = userdata

    for zone in zones:
        # subscribe
        client.subscribe(zones[zone]['description']['command_topic'])

        publishDiscoveryMessage(client, zone, zones[zone])
        publishAvailability(client, zone, zones[zone], 'online')
        publishState(client, zone, zones[zone], zones[zone]['state'])

def onMessage(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8")
    print(topic + " " + payload)

    pieces = topic.split('/')
    if pieces[3] == 'set':
        zone = pieces[2]
        if payload == 'on':
           turnZoneOn(zones[zone])
        elif payload == 'off':
           turnZoneOff(zones[zone])
        publishState(client, zone, zones[zone], zones[zone]['state'])

# setup
version = "2.0.0"

zones = {
    "irrigation1": {
        "gpio": gpiozero.OutputDevice(27, False)
    },
    "irrigation2": {
        "gpio": gpiozero.OutputDevice(22, False)
    },
    "irrigation3": {
        "gpio": gpiozero.OutputDevice(24, False)
    },
    "irrigation4": {
        "gpio": gpiozero.OutputDevice(23, False)
    },
    "irrigation5": {
        "gpio": gpiozero.OutputDevice(25, True)
    }
}

turnAllZonesOff(zones)

# fill description
for zone in zones:
    zones[zone]['description'] = {}
    zones[zone]['description']['device'] = {"identifiers": ['irrigation-controller']}
    zones[zone]['description']['name'] = zone
    zones[zone]['description']['device_class'] = 'switch'
    zones[zone]['description']['payload_on'] = 'on'
    zones[zone]['description']['payload_off'] = 'off'
    zones[zone]['description']['state_on'] = 'on'
    zones[zone]['description']['state_off'] = 'off'
    zones[zone]['description']['availability'] = {}
    zones[zone]['description']['availability']['payload_available'] = 'online'
    zones[zone]['description']['availability']['payload_not_available'] = 'offline'
    zones[zone]['description']['availability']['topic'] = 'homeassistant/switch/' + zone + '/available'
    zones[zone]['discovery_topic'] = 'homeassistant/switch/' + zone + '/config'
    zones[zone]['description']['command_topic'] = 'homeassistant/switch/' + zone + '/set'
    zones[zone]['description']['state_topic'] = 'homeassistant/switch/' + zone + '/state'
    zones[zone]['description']['unique_id'] = version+zone

client = mqtt.Client(userdata=zones)
client.on_connect = onConnect
client.on_message = onMessage


client.connect("192.168.1.201", 1883)
client.loop_forever()
