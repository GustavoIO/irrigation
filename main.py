import paho.mqtt.client as mqtt
from datetime import datetime
import time
import json
import os
import gpiozero

def loadUniqueId(uniqueIdFile):
    file = open(uniqueIdFile, "r")
    uniqueId = file.read().rstrip()
    file.close()
    return uniqueId

def loadSettings(settingsFile):
    file = open(settingsFile, "r")
    settings = json.loads(file.read())
    file.close()
    return settings

def updateSettings(settingsJson, settingsFile):
    file = open(settingsFile, "w")
    file.write(settingsJson)
    file.close()
    os._exit(1) # restart app to load new settings

def publishDescription(client, topic, description):
    s = json.dumps(description)
    client.publish(topic, s, 0, retain=True)

def publishSettings(client, topic, settings):
    s = json.dumps(settings)
    client.publish(topic, s, 0, retain=True)

def turnAllZonesOff(zones):
    for zone in zones:
        turnZoneOff(zones[zone])

def turnZoneOff(zone):
    print("Turning zone " + str(zone["gpio"]) + " off")
    zone["gpio"].off()

def turnZoneOn(zone):
    print("Turning zone " + str(zone["gpio"]) + " on")
    zone["gpio"].on()

def onConnect(client, userdata, flags, rc):
    print("Connected: " + str(rc))

    # subscribe
    client.subscribe(settingsUpdateTopic)
    client.subscribe(zone1Topic)
    client.subscribe(zone2Topic)
    client.subscribe(zone3Topic)
    client.subscribe(zone4Topic)
    

def onMessage(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8")
    print(topic + " " + payload)

    if topic == settingsUpdateTopic:
        updateSettings(payload, settingsFile)
    elif topic == zone1Topic:
        if payload == "on":
            turnZoneOn(zones["zone1"])
        elif  payload == "off":
            turnZoneOff(zones["zone1"])
    elif topic == zone2Topic:
        if payload == "on":
            turnZoneOn(zones["zone2"])
        elif  payload == "off":
            turnZoneOff(zones["zone2"])
    elif topic == zone3Topic:
        if payload == "on":
            turnZoneOn(zones["zone3"])
        elif  payload == "off":
            turnZoneOff(zones["zone3"])
    elif topic == zone4Topic:
        if payload == "on":
            turnZoneOn(zones["zone4"])
        elif  payload == "off":
            turnZoneOff(zones["zone4"])
    else:
        print("Unexpected topic: " + msg.topic)

# setup
client = mqtt.Client()
client.on_connect = onConnect
client.on_message = onMessage

uniqueIdFile = "/home/pi/irrigation/unique_id"
settingsFile = "/home/pi/irrigation/irrigation_settings.json"

version = "0.1.0"

uniqueId = loadUniqueId(uniqueIdFile)
descriptionTopic = "devices/<id>/description".replace("<id>", uniqueId)
settingsTopic = "devices/<id>/settings".replace("<id>", uniqueId)
settingsUpdateTopic = settingsTopic + "/update"
zone1Topic = "devices/<id>/zone/1".replace("<id>", uniqueId)
zone2Topic = "devices/<id>/zone/2".replace("<id>", uniqueId)
zone3Topic = "devices/<id>/zone/3".replace("<id>", uniqueId)
zone4Topic = "devices/<id>/zone/4".replace("<id>", uniqueId)

timeFormat = "%Y-%m-%d %H:%M:%S"
startupTime = datetime.now()

description = {
    "id": uniqueId,
    "type": "irrigatonContoller",
    "version": version,
    "uptime": 0,
    "time": startupTime.strftime(timeFormat)
}

settings = loadSettings(settingsFile)

zones = {
    "zone1": {
        "gpio": gpiozero.OutputDevice(27, False)
    },
    "zone2": {
        "gpio": gpiozero.OutputDevice(22, False)
    },
    "zone3": {
        "gpio": gpiozero.OutputDevice(24, False)
    },
    "zone4": {
        "gpio": gpiozero.OutputDevice(23, False)
    }
}

client.connect("localhost", 1883)
client.loop_start()

publishSettings(client, settingsTopic, settings)

while True:

    now = datetime.now()
    dayOfWeek = now.weekday()
    hour = now.hour
    minute = now.minute

    # update desciption
    description["uptime"] = (now - startupTime).total_seconds()
    description["time"] = now.strftime(timeFormat)

    publishDescription(client, descriptionTopic, description)

    # for each zone check if the schedule matches the status
    for zone in zones:
        for schedule in settings["schedules"][zone]:

            if dayOfWeek == schedule["dayOfWeek"] and \
                hour == schedule["hour"] and \
                minute == schedule["minute"]:

                if schedule["action"] == "on":
                    turnZoneOn(zones[zone])
                elif schedule["action"] == "off":
                    turnZoneOff(zones[zone])

    time.sleep(30) # sleep for 30 seconds so schedules are verified twice a minute


