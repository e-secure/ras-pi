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
        self.PASS           = ""
        self.vehicles_db    = self.connect()
        self.vehicle        = self.vehicles_db.child(self.GAADI_CONST)
        self.location       = self.vehicle.child("location")
        
        self.vehicle_status = self.vehicle.get()["status"]
        self.img_count      = self.vehicle.get()["counter"]
        self.latitude       = self.location.get()["latitude"]
        self.longitude      = self.location.get()["longitude"]

    def connect(self):
        TABLE_VEHICLES_CONST = ""
        print("trying to connect to table vehicles\n")
        vehicles = db.reference(TABLE_VEHICLES_CONST)
        if vehicles:
            print("table vehicles connected successfully\n")
        return vehicles

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

            if self.vehicle.child("rfid").get()["status"] == "locked" or self.vehicle.child("rfid").get()["status"] == "lost" or self.vehicle.child("rfid").get()["status"] == "new_key":
                self.vehicle_status = "Unauthorized movement"
                self.vehicle.update({
                    "status": self.vehicle_status
                })
                print("updated vehicle status: ",self.vehicle_status,
                        "at", datetime.datetime.now())
        return current_latitude, current_longitude

    def get_rfid(self):
        l=['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','1','2','3','4','5','6','7','8','9','0','!','@','#','$','%','^','&','*','_','-','+','=','/','\\','|']
        rfid = self.vehicle.child("rfid")
        while True:
            rfid_password = self.vehicle.child("rfid").get()["password"]
            rfid_id = self.vehicle.child("rfid").get()["id"]
            rfid_status= self.vehicle.child("rfid").get()["status"]
            tag = SimpleMFRC522()
            print(rfid_status+"sumanth")
            if rfid_status == "locked" or rfid_status == "unlocked":
                print("noob")
                try:
                    time.sleep(1)
                    print("Place tag on the reader")
                    id, text = tag.read()
                    print("authenticating")
                    if text == rfid_password and id==rfid_id:
                        print("pass is correct")
                        self.update_rfid(1)
                    elif text == rfid_password and id!=rfid_id:
                        self.update_rfid(2)
                    else:
                        self.update_rfid(0)
                finally:
                    GPIO.cleanup()
            elif rfid_status == "new_key":
                print("pro")
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
                    rfid.update({
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
        rfid        = self.vehicle.child("rfid")
        rfid_status = rfid.get()["status"]

        if x==1:
            if rfid_status == "locked":
                rfid_status = "unlocked"
            elif rfid_status == "unlocked":
                rfid_status = "locked"
            if self.vehicle_status == "Unauthorized access":
                self.vehicle_status = "secure"
        elif x==2:
            print("correct password.. Invalid Key.")
            warning = "RFID duplication attempt warning"
            self.vehicle_status = "Unauthorized access"
            rfid_status = "locked"
            self.vehicle.update({
            "warning": warning
            })   
        else:
            if rfid_status == "locked" or rfid_status == "unlocked":
                print("Incorrect password.. Unauthorized access")
                self.vehicle_status = "Unauthorized access"
                rfid_status = "locked"
            else:
                print("Incorrect password.. Unauthorized access")
                self.vehicle_status = "Unauthorized access"
        self.vehicle.update({
            "status": self.vehicle_status
        })            
        rfid.update({
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