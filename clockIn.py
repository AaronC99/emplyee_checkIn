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
print ("\n")


# This loop keeps checking for chips. If one is near it will get the UID and authenticate
while continue_reading:

    # Scan for cards
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

    # If a card is found
    if status == MIFAREReader.MI_OK:
        print ("*****Card Scanned*****")

    # Get the UID of the card
    (status,uid) = MIFAREReader.MFRC522_Anticoll()
    card_uid = str(uid[0:4])

    # If we have the UID, continue
    if status == MIFAREReader.MI_OK:
        # SELECT employeeID, clockInDATE FROM attendance INNER JOIN
        # EMPLOYEE ON EMPLOYEE.ID = attendance.employeeID
        # WHERE EMPLOYEE.CARDNUMBER = ? AND attendance.clockInDATE = ?

        for row in rfid_access.execute("SELECT employeeID, date FROM attendance INNER JOIN EMPLOYEE ON EMPLOYEE.employee_uid= attendance.employeeID WHERE EMPLOYEE.card_uid = ?",(card_uid,)):
            employeeID, date  = row
            if employeeID != None && date != date('now','localtime'):
                rfid_access.execute("INSERT INTO attendance(employeeID,clockIn,lateness,date) VALUES ((SELECT employee_uid FROM employee where card_uid = ?) , strftime('%H:%M','now','localtime'),(strftime('%H','now','localtime') - strftime('%H','09:00'))|| ':' || (strftime('%M','now','localtime') - strftime('%M','09:00')),date('now','localtime') )",[card_uid])
                print(employeeID + "has clocked in.")
            else:
                print ("Welcome!! You have already clock in")
        break

    rfidData.commit() # connection for COMMIT
    
    time.sleep(1)