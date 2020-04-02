from firebase_admin import db
import datetime

TABLE_VEHICLES_CONST = ""

#as of now, we are operating only on 1 vehicle
#so this is the id of the object we are working on
GAADI_CONST = ""

def connect():
    print("trying to connect to table vehicles\n")
    vehicles = db.reference(TABLE_VEHICLES_CONST)
    if vehicles:
        print("table vehicles connected successfully\n")
    return vehicles

def updating_gps(vehicles, gaadi, latitude, longitude):
    vehicle_child = vehicles.child(gaadi)
    current_latitude = vehicle_child.get()["latitude"]
    current_longitude = vehicle_child.get()["longitude"]

    if(abs(current_latitude - latitude) > 10 or abs(current_longitude - longitude) > 10):
        vehicle_child.update({
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

def get_gps(vehicles):
    vehicle_child = vehicles.child(GAADI_CONST)
    latitude = vehicle_child.get()["latitude"]
    longitude = vehicle_child.get()["longitude"]

    while True:
        dir = input()
        if dir == "w":
            longitude += 5
        elif dir == "s":
            longitude -= 5
        elif dir == "d":
            latitude += 5
        elif dir == "a":
            latitude -= 5
        else:
            pass

        updating_gps(vehicles, GAADI_CONST, latitude = latitude, longitude = longitude)

def updating_rfid(vehicles, gaadi, rfid_status):
    vehicle_child = vehicles.child(gaadi)
    vehicle_child.update({
        "rfid": rfid_status
    })
    #print("updated rfid at ", datetime.datetime.now())

def get_rfid(vehicles):
    while True:
        """
        fill this function with your code to get gps coordinates
        vehicles is the json file consiting the gaadi details
        put an if statement, that if the rfid is detected,
        then only call updating_rfid
        """
        updating_rfid(vehicles, GAADI_CONST, rfid_status = "LoCkEd")

def printing(vehicles):
    print(vehicles.get())