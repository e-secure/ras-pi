"""
naming conventions
class names = camelCase
normal variables and functions = names_with_underscore
global variables = CAPITAL
global constant varibales = CAPITAL_CONST
"""

import firebase_admin
from firebase_admin import credentials
import connection
import threading

FIREBASE_URL_CONST = ""
PRIVATE_KEY_PATH   = ""

def thread():
    t1 = threading.Thread(target=hardware.get_gps)
    t2 = threading.Thread(target=hardware.get_rfid)
    t3 = threading.Thread(target=hardware.get_camera)
    t1.start()
    t2.start()
    t3.start()

if __name__ == "__main__":
    import sys

    cred = credentials.Certificate(PRIVATE_KEY_PATH)
    firebase_admin.initialize_app(cred, {
    'databaseURL': FIREBASE_URL_CONST
    })

    hardware = connection.hardware()
    thread()