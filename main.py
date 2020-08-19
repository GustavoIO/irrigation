import paho.mqtt.client as mqtt
from datetime import datetime
import time

def loadUniqueId():
    # mock code, on production this will read a file on the filesystem
    return "98b694ce-3d4d-4786-8d45-defd265bb3e0"

def loadSettings():
    # mock code, on production this will read a file on the filesystem
    return {
        "schedules": {
            "zone1": [
                {
                    "startDayOfWeek": 2,
                    "startHour": 14,
                    "startMinute": 34,
                    "endDayOfWeek": 2,
                    "endHour": 14,
                    "endMinute": 35
                },{
                    "startDayOfWeek": 2,
                    "startHour": 14,
                    "startMinute": 37,
                    "endDayOfWeek": 2,
                    "endHour": 14,
                    "endMinute": 40
                }
            ],
            "zone2": [],
            "zone3": [],
            "zone4": [],
        }
    }

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
    client.subscribe(settingsTopic)

def onMessage(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))

# setup
client = mqtt.Client()
client.on_connect = onConnect
client.onMessage = onMessage

uniqueId = loadUniqueId()
descriptionTopic = "devices/<id>/description".replace("<id>", uniqueId)
settingsTopic = "devices/<id>/settings".replace("<id>", uniqueId)

settings = loadSettings()

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

# publishSettings(settings)

turnAllZonesOff(zones)

while True:

    now = datetime.now()
    dayOfWeek = now.weekday()
    hour = now.hour
    minute = now.minute

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


