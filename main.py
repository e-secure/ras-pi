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
PRIVATE_KEY_PATH = ""

def thread():
    t1 = threading.Thread(target=connection.get_gps, args=(vehicles,))
    t2 = threading.Thread(target=connection.get_rfid, args=(vehicles,))
    t1.start()
    t2.start()
    """
    works without the following codes as well
    as you start a thread, main function is also keeps executing
    so for the main function to not terminate and wait for the
    threads to finish executing, .join() is used
    """
    #t1.join()
    #t2.join()


if __name__ == "__main__":
    import sys

    cred = credentials.Certificate(PRIVATE_KEY_PATH)
    firebase_admin.initialize_app(cred, {
    'databaseURL': FIREBASE_URL_CONST
    })

    vehicles = connection.connect()
    
    thread()
    
    



