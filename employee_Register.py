import RPi.GPIO as GPIO
import MFRC522
import signal
import sqlite3 as sql
import time

rfidData = sql.connect('coe-employees.db')
rfidData.execute("PRAGMA journal_mode=WAL")
rfidData.execute("VACUUM")
rfid_access = rfidData.cursor()

continue_reading = True

# Capture SIGINT for cleanup when the script is aborted
def end_read(signal,frame):
    global continue_reading
    continue_reading = False
    rfid_access.close() # cursor for close()
    GPIO.cleanup()

# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()

#Welcome Message
print ("Welcome to CoE E.A.T.S\nScanning for cards...")
print ("---------------------")


# This loop keeps checking for chips. If one is near it will get the UID and authenticate
while continue_reading:

    # Scan for cards
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

    # If a card is found
    if status == MIFAREReader.MI_OK:
        print ("--------------------------")
        print ("Card detected")

    # Get the UID of the card
    (status,uid) = MIFAREReader.MFRC522_Anticoll()
    card_uid = str(uid[0:4])

    # If we have the UID, continue
    if status == MIFAREReader.MI_OK:

        for row in rfid_access.execute("SELECT employeeName, username, card_uid, registeredDate FROM employee WHERE card_uid = ?", (card_uid,)):
            name, username, card_uid, registeredDate = row
            print ("Card UID: " + card_uid)
            print ("Registered on: "+ registeredDate)
            if username == None:
                name = input('Enter Name: ')
                username = input('Enter Domain ID: ')
                rfid_access.execute("UPDATE employee SET employeeName = ?, username = ? where card_uid = ?",([name, username,card_uid]))
                print (name+" is registered as "+username)
                rfid_access.execute("UPDATE employee SET registeredDate = datetime('now','localtime') WHERE card_uid = ?", (card_uid,))
            else:
                print ("Welcome "+username)
            
            break
        else:
            print("New Card Identified!! Tap again to register")
            rfid_access.execute("insert into employee (card_uid, registeredDate) values (?, datetime('now','localtime'))", (card_uid,))

        rfidData.commit() # connection for COMMIT

    time.sleep(1)
