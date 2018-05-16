import time
import smtplib
import os.path
import MySQLdb as db
import RPi.GPIO as GPIO
from time import sleep
from picamera import PiCamera
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from datetime import datetime


def main():
    GPIO.setmode(GPIO.BCM)
                                             # Pin numbers
    pirPin = 18                              # PiR    18
    buzzerPin = 13                           # Buzzer 13
    LEDpin = 26                              # LED    26

    GPIO.setup(pirPin, GPIO.IN)              # PiR input on pin 26
    GPIO.setup(buzzerPin, GPIO.OUT)          # setting up the buzzer on pin nr 33 as output
    GPIO.setup(LEDpin, GPIO.OUT)             # LED output pin

    timeout_start = time.time()              # timer for sending 'System Alive' message
    buzzTime = 0.5                           # the active buzzer imitates the outside alarm, used only for that purpouse
    aliveTime = 20

    camera = PiCamera()                      # assigning PiCamera to camera variable
    counter = 1                              # pictures will be saved based on basename and number, counter holds number

    filepath = "/home/pi/iot/pic/"           # place where all the images will be stored

    attachments = []                         # this list will store images as attachments to the email

    print("SURVEILLANCE PROGRAM STARTS:")

    while True:                              # our infinite loop starts here

        i = GPIO.input(18)                   # takes input from Pir sensor
        if i == 1:                           # if motion detected start from here
            try:
                camera.start_preview()
                time.sleep(1)

                GPIO.output(buzzerPin, True)   # Turn ON Buzzer
                print("Buzzer ON")             # CONSOLE MESSAGE
                GPIO.output(26, 1)             # Turn ON LED
                print("LED ON")                # CONSOLE MESSAGE
                sleep(buzzTime)                # 0.5 sec
                GPIO.output(buzzerPin, False)  # Turn OFF Buzzer

                for x in range(0, 3):                                   # repeat 3 times - for three pictures to be sent
                    picfile = filepath + str('image%s.jpg' % counter)   # pwd and name of file taken
                    print(picfile)                                      # CONSOLE MESSAGE
                    camera.capture(filepath + 'image%s.jpg' % counter)  # all pictures are saved locally in imageX.jpg format, where X corresponds to our counter value

                    insertImage(picfile, counter)

                    attachments.append(picfile)                         # building up our list made of images
                    print("picture taken " + str(counter))              # CONSOLE MESSAGE about pictures been taken
                    counter = counter + 1
                    camera.stop_preview()                               # freeing camera resource
                    time.sleep(1)

                GPIO.output(26, 0)                                      # Turn OFF LED

                if len(attachments) % 3 == 0:                           # if our list contains three pictures send email
                    sendEmail("link for more: ", "Intruder detected", attachments)
                    attachments = []                                    # holds only three images, empty after that

                timeout_start = time.time()                             # reset the timer for 'System Alive' message

            except:
                camera.stop_preview()
                time.sleep(3)

        elif i == 0:                                           # if motion not detected
            if time.time() - (timeout_start + aliveTime) > 0:  # if particular amount of time has passed sent "System Alive' message
                print("System alive - email was sent")         # for the project presentation purpose set for 20 sec of inacticity
                timeout_start = time.time()
                sendEmail("System is active. No motion detected so far. Your biscuits are safe.", "System alive", [])


def sendEmail(mess, sub, attachment=[]):
    """takes three parameters: message content, subject, and list of files that will be attached to the email,
    and then sends notifying email"""

    msg = MIMEMultipart()                       # used for MIME messages that are multipart
    msg['Subject'] = sub
    msg['From'] = "youremail@gmail.com"
    msg['To'] = "youremail@gmail.com"
    message = mess
    msg.attach(MIMEText(message, 'html'))       # attach message content into email - this is what the user will see inside his email

    for f in attachment:                        # attach 3 image files from attachment list
        with open(f, 'rb') as a_file:
            basename = os.path.basename(f)
            part = MIMEApplication(a_file.read(), Name=basename)

        part['Content-Disposition'] = 'attachment; filename="%s"' % basename
        msg.attach(part)

    sender = 'youremail@gmail.com'
    receivers = ['youremail@gmail.com']

    user = "youremail@gmail.com"
    pwd = "yourpassword"

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)         # setting up the server details
        server.ehlo()
        server.starttls()
        server.login(user, pwd)
        server.sendmail(sender, receivers, msg.as_string())  # sending the email
        server.close()
        print("successfully sent the email")                  # CONSOLE MESSAGE
    except:
        print("failed to send email")                         # CONSOLE MESSAGE


def insertImage(path, counter):

    HOST = "yourhost"
    PORT = 3306
    USER = "youruser"
    PASSWORD = "yourpass"
    DB = "yourdb"

    try:
        connection = db.connect(host=HOST, port=PORT,
                                user=USER, passwd=PASSWORD, db=DB)

        dbhandler = connection.cursor()

        d = datetime.now()
        print(d)                    # TESTING
        p = path

        #image = Image.open('path')
        blob_value = open(path, 'rb').read()

        dbhandler.execute("""INSERT INTO images VALUES (%s,%s,%s,%s)""", (counter, d, p, blob_value))   # Insert into DB
        connection.commit()

        dbhandler.execute("SELECT * from images2")          # Display for testing purpose
        result = dbhandler.fetchall()
        for item in result:
            print(item)

        connection.close()

    except Exception as e:
        print(e)

    #finally:
    #    connection.close()


if __name__ == '__main__':
    main()
