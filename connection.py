from firebase_admin import db
import datetime
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import picamera
import base64

class hardware:

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

            if(self.vehicle.child("rfid").get()["status"] == "locked"):
                self.vehicle_status = "alert"
                self.vehicle.update({
                    "status": self.vehicle_status
                })
                print("updated vehicle statuss: ",self.vehicle_status,
                        "at", datetime.datetime.now())
        return current_latitude, current_longitude

    def get_rfid(self):
        rfid_password = self.vehicle.child("rfid").get()["password"]
        tag = SimpleMFRC522()

        while True:
            time.sleep(1)
            try:
                print("Place tag on the reader")
                id, text = tag.read()
                print(id)
                print(text)
                print("authenticating")
                if text == rfid_password:
                    print("pass is correct")
                    GPIO.cleanup()
                    self.update_rfid(1)
                else:
                    GPIO.cleanup()
                    self.update_rfid(0)
            finally:
                GPIO.cleanup()

    def update_rfid(self, x):
        rfid        = self.vehicle.child("rfid")
        rfid_status = rfid.get()["status"]

        if x==1:
            if rfid_status == "locked":
                rfid_status = "unlocked"
            else:
                rfid_status = "locked"

            if self.vehicle_status == "unauthorized access":
                self.vehicle_status = "secure"
        else:
            print("Incorrect password.. Unauthorized access")
            self.vehicle_status = "unauthorized access"
            rfid_status = "locked"

        self.vehicle.update({
            "status": self.vehicle_status
        })            
        rfid.update({
            "status": rfid_status
        })
        print("updated rfid status, vehicle status: ", rfid_status, 
                self.vehicle_status, "at", datetime.datetime.now())