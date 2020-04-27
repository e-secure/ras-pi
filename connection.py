from firebase_admin import db
import datetime
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import picamera
import base64
import random

class piHandler:

    def __init__(self):
        self.GAADI_CONST    = ""
        self.vehicles_db    = self.connectTable("")
        self.vehicle        = self.vehicles_db.child(self.GAADI_CONST)
        self.location       = self.vehicle.child("location")
        self.rfid           = self.vehicle.child("rfid")
        self.events         = self.connectTable("/")
       
        self.vehicle_status = self.vehicle.get()["status"]
        #self.rfid_status    = self.rfid.get()["status"]
        self.img_count      = self.vehicle.get()["counter"]
        self.latitude       = self.location.get()["latitude"]
        self.longitude      = self.location.get()["longitude"]
        self.event_count    = self.events.get()["counter"]

    def connectTable(self, table_name):
        print("trying to connect to table {}\n" .format(table_name[1:]))
        table = db.reference(table_name)
        if table:
            print("table {} connected successfully\n" .format(table_name[1:]))
        return table

    def get_gps(self):
        current_latitude  = self.latitude
        current_longitude = self.longitude

        while True:
            dir = input()
            if dir == "d":
                self.longitude += 5
            elif dir == "a":
                self.longitude -= 5
            elif dir == "w":
                self.latitude  += 5
            elif dir == "s":
                self.latitude  -= 5
            else:
                pass
            current_latitude, current_longitude = self.updating_gps(
                                current_latitude, current_longitude)

    def updating_gps(self, current_latitude, current_longitude):

        if(abs(current_latitude - self.latitude) > 0.005 or
           abs(current_longitude - self.longitude) > 0.005):
            self.location.update({
                "latitude": self.latitude,
                "longitude": self.longitude
            })
            current_latitude=self.latitude
            current_longitude=self.longitude
            print("updated latitude: " + str(self.latitude) + ", longitude: "
                + str(self.longitude) + " at ", datetime.datetime.now())

            rfid_status = self.rfid.get()["status"]

            if rfid_status == "locked" or rfid_status == "lost" or rfid_status == "new_key":
                self.vehicle_status = "Unauthorized movement"
                self.vehicle.update({
                    "status": self.vehicle_status
                })
                self.updateEvents()
                print("updated vehicle status: ",self.vehicle_status,
                        "at", datetime.datetime.now())
        return current_latitude, current_longitude

    def get_rfid(self):
        l=['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','1','2','3','4','5','6','7','8','9','0','!','@','#','$','%','^','&','*','_','-','+','=','/','\\','|']
        while True:
            rfid_status =self.rfid.get()["status"]
            rfid_password = self.rfid.get()["password"]
            rfid_id = self.rfid.get()["id"]
            tag = SimpleMFRC522()
            if rfid_status == "locked" or rfid_status == "unlocked":
                try:
                    time.sleep(1)
                    print("Place tag on the reader")
                    id, text = tag.read()
                    print("authenticating")
                    if text == rfid_password and id==rfid_id:
                        self.update_rfid(1)
                    elif text == rfid_password and id!=rfid_id:
                        self.update_rfid(2)
                    else:
                        self.update_rfid(0)
                finally:
                    GPIO.cleanup()
            elif rfid_status == "new_key":
                newpass=""
                try:
                    print("Place tag on the reader")
                    id,text=tag.read()
                    for i in range(len(rfid_password)):
                        j=random.randint(0,len(l)-1)
                        newpass=newpass+l[j]
                    print(newpass)
                    tag.write(newpass)
                    print("Password updated")
                    self.rfid.update({
                        "status":"locked",
                        "id":id,
                        "password":newpass
                        })
                    newpass=''
                    print("New key registered!")
                finally:
                    GPIO.cleanup()
            else:
                print("waiting")

    def update_rfid(self, x):
        rfid_status=self.rfid.get()["status"]
        if x==1:
            if rfid_status == "locked":
                rfid_status = "unlocked"
            elif rfid_status == "unlocked":
                rfid_status = "locked"
            if self.vehicle_status == "Unauthorized access":
                self.vehicle_status = "secure"
        elif x==2:
            print("correct password.. Invalid Key.")
            self.vehicle_status = "Unauthorized access"
            rfid_status = "locked"
        else:
            print("Incorrect password.. Unauthorized access")
            self.vehicle_status = "Unauthorized access"
            if rfid_status == "locked" or rfid_status == "unlocked":
                rfid_status = "locked"
        self.vehicle.update({
            "status": self.vehicle_status
        })
        self.updateEvents()
        self.rfid.update({
            "status": rfid_status
        })
        print("updated rfid status, vehicle status: ", rfid_status, 
                self.vehicle_status, "at", datetime.datetime.now())
    
    def get_camera(self):
        while True:
            if self.vehicle_status != "secure":
                cam = picamera.PiCamera()
                cam.resolution=(256,256)
                cam.brightness=60
                cam.start_preview()
                cam.capture('img.jpeg')
                cam.stop_preview()
                img = open('img.jpeg','rb')
                bs64 = base64.b64encode(img.read()).decode('ascii')
                img.close()
                self.update_camera(bs64)
                cam.close()
                time.sleep(5)
            else:
                time.sleep(1)
            
    def update_camera(self, bs64):
        images = self.vehicle.child("images")
        ctr=str(self.img_count)
        ctr=ctr.zfill(5)
        img = "IMG_" + ctr
        images.update({
            img : {
                "base64": bs64,
                "dateTime": str(datetime.datetime.now()),
                "id": img,
                "location": {
                    "latitude": self.latitude,
                    "longitude": self.longitude
                }
            }
        })
        print("updated image at", datetime.datetime.now())

        self.img_count += 1

        self.vehicle.update({
            "counter": self.img_count
        })
        print("updated image count:", self.img_count, "at",
             datetime.datetime.now())

    def updateEvents(self):
        counter = str(self.event_count)
        counter = counter.zfill(5)
        date    = str(datetime.datetime.now())
        eventId = "event" + str(counter)
        rfid_status=self.rfid.get()["status"]
        self.event_count += 1
        self.events.update({
            eventId : {
                "Event_id"   : eventId
                "Vehicle_id" : self.GAADI_CONST,
                "time"       : date,
                "status"     : self.vehicle_status,
                "rfid"       : rfid_status
            },
            "counter" : self.event_count
        })
        print("event added at", datetime.datetime.now())