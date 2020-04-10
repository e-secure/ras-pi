from firebase_admin import db
import datetime
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import picamera
import base64
TABLE_VEHICLES_CONST = ""

#as of now, we are operating only on 1 vehicle
#so this is the id of the object we are working on
GAADI_CONST = ""
PASS=""

def capture():
    cam=picamera.PiCamera()
    cam.resolution=(256,256)
    cam.brightness=60
    cam.start_preview()
    cam.capture('img.jpeg')
    cam.stop_preview()
    img=open('img.jpeg','rb')
    bs64=base64.b64encode(img.read()).decode('ascii')
    img.close()
    cam.close()
    return bs64

def authenticate():
    tag=SimpleMFRC522()
    time.sleep(1)
    try:
        print("Place tag on the reader")
        id, text=tag.read()
        print(id)
        print(text)
        if text==PASS:
            GPIO.cleanup()
            return 1
        else:
            GPIO.cleanup()
            return 0
    finally:
        GPIO.cleanup()

def connect():
    print("trying to connect to table vehicles\n")
    vehicles = db.reference(TABLE_VEHICLES_CONST)
    if vehicles:
        print("table vehicles connected successfully\n")
    return vehicles

def updating_gps(vehicles, gaadi, latitude, longitude):
    vehicle_child = vehicles.child(gaadi)
    vehicle_position=vehicle_child.child("position")
    vehicle_images=vehicle_child.child("images")
    current_latitude = vehicle_position.get()["latitude"]
    current_longitude = vehicle_position.get()["longitude"]
    count=vehicle_child.get()["counter"]
    if(abs(current_latitude - latitude) > 0.005 or abs(current_longitude - longitude) > 0.005):
        vehicle_position.update({
            "latitude": latitude,
            "longitude": longitude
        })
        print("updated latitude: " + str(latitude) + ", longitude: " + str(longitude) + " at ", datetime.datetime.now())

        if(vehicle_child.get()["rfid"].lower() == "locked"):
            vehicle_child.update({
                "status": "alert"
            })
        if(vehicle_child.get()["status"].lower() == "alert"):
            print("send photo")
            b64=capture()
            img="img"+str(count)
            vehicle_images.update({
                img: b64
            })
            count=count+1
            vehicle_child.update({
                "counter": count
            })

def get_gps(vehicles):
    vehicle_child = vehicles.child(GAADI_CONST)
    vehicle_position=vehicle_child.child("position")
    latitude = vehicle_position.get()["latitude"]
    longitude = vehicle_position.get()["longitude"]
    while True:
        dir = input()
        if dir == "d":
            longitude += 5
        elif dir == "a":
            longitude -= 5
        elif dir == "w":
            latitude += 5
        elif dir == "s":
            latitude -= 5
        else:
            pass
        print(latitude, longitude)
        updating_gps(vehicles, GAADI_CONST, latitude = latitude, longitude = longitude)

def updating_rfid(vehicles, gaadi, rfid_status):
    vehicle_child = vehicles.child(gaadi)
    vehicle_child.update({
        "rfid": rfid_status
    })
    print("updated rfid at ", datetime.datetime.now())

def get_rfid(vehicles):
    vehicle_child = vehicles.child(GAADI_CONST)
    rfid_status = vehicle_child.get()["rfid"]
    while True:
        """
        fill this function with your code to get gps coordinates
        vehicles is the json file consiting the gaadi details
        put an if statement, that if the rfid is detected,
        then only call updating_rfid
        """
        print("authenticating")
        x=authenticate()
        if x==1:
            if rfid_status=="locked":
                rfid_status="unlocked"
            else:
                rfid_status="locked"
            updating_rfid(vehicles, GAADI_CONST, rfid_status)
        else:
            pass

def printing(vehicles):
    print(vehicles.get())