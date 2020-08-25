import paho.mqtt.client as mqtt
from datetime import datetime
import time
import json
import os

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
    print("gpio: " + str(zone["gpio"]) + " off")
    zone["on"] = False

def turnZoneOn(zone):
    print("gpio: " + str(zone["gpio"]) + " on")
    zone["on"] = True

def onConnect(client, userdata, flags, rc):
    print("Connected: " + str(rc))

    # subscribe
    result = client.subscribe(settingsUpdateTopic)
    print("Subscribed to: " + settingsUpdateTopic + " with result: " + str(result))

def onMessage(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8")
    print(topic + " " + payload)

    if topic == settingsUpdateTopic:
        updateSettings(payload, settingsFile)
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
        "gpio": 10,
        "on": False,
    },
    "zone2": {
        "gpio": 11,
        "on": False
    },
    "zone3": {
        "gpio": 12,
        "on": False
    },
    "zone4": {
        "gpio": 13,
        "on": False
    }
}

client.connect("localhost", 1883)
client.loop_start()

publishSettings(client, settingsTopic, settings)

turnAllZonesOff(zones)

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
        shouldBeOn = False
        for schedule in settings["schedules"][zone]:
            if  dayOfWeek >= schedule["startDayOfWeek"] and \
                hour >= schedule["startHour"] and \
                minute >= schedule["startMinute"] and \
                dayOfWeek <=  schedule["endDayOfWeek"] and \
                hour <= schedule["endHour"] and \
                minute < schedule["endMinute"]:

                shouldBeOn = True
                break

        if shouldBeOn and not zones[zone]["on"]:
            # zone is scheduled. Turn it on
            turnZoneOn(zones[zone])
        elif not shouldBeOn and zones[zone]["on"]:
            # zone is scheduled, but it's on. Turn it off
            turnZoneOff(zones[zone])
            

    time.sleep(20) # sleep for 20 second so schedules are verified thrice a minute


