import RPi.GPIO as GPIO
import MFRC522
import signal
import sqlite3 as sql
import time

rfidData = sql.connect('coe-eats.db')
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

        for row in rfid_access.execute("SELECT username, card_uid, clockIn FROM rfid_access WHERE card_uid = ?", (card_uid,)):
            username, card_uid, clockIn = row
            print ("Card UID: " + card_uid)
            #print ("registered at: "+date_time)
            print ("Clock in at: "+ clockIn)
            if username == None:
                username = input('Enter Domain ID: ')
                rfid_access.execute("UPDATE rfid_acess SET username = ? where card_uid = ?",([username,card_uid]))
                print (username+" is REgistered!")
            else:
                    print ("Welcome "+username)
            rfid_access.execute("UPDATE rfid_access SET clockIn = datetime('now','localtime') WHERE card_uid = ?", (card_uid,))
            break
        else:
            print("New Card Identified!! Tap again to register")
            rfid_access.execute("insert into rfid_access (card_uid, clockIn) values ?, datetime('now','localtime'))", (card_uid,))

        rfidData.commit() # connection for COMMIT

        hexUid=""
        for val in uid[0:4]:
            hexUid = hexUid+" {:02x}".format(val)

        # This is the default key for authentication
        key = [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF]

        # Select the scanned tag
        MIFAREReader.MFRC522_SelectTag(uid)

        # Authenticate
        status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 0, key, uid)

        # Check if authenticated
        if status == MIFAREReader.MI_OK:
#            print MIFAREReader.MFRC522_Read(0)
            MIFAREReader.MFRC522_StopCrypto1()
        else:
            print ("Authentication error. Ignoring...")

    time.sleep(1)



