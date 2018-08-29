#!/usr/bin/python
import subprocess
import Adafruit_DHT
import smtplib
from datetime import datetime
import time
import RPi.GPIO as GPIO  ## Import GPIO library
import logging
import config

GPIO.setmode(GPIO.BOARD)  ## Use board pin numbering
GPIO.setup(11, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)


def init_setup_email(temperature, email_to, gmail_from, gmail_pass):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S %p")
    ip_std = subprocess.Popen(['hostname', '-I'], stdout=subprocess.PIPE)
    ip = ip_std.communicate()[0]
    message = "From: " + gmail_from + "\nTo: " + email_to + "\nSubject: Temperature all good\n\n" + dt + "\nTemperature is: " + str(temperature) + "C at IP: " + ip
    send_email(email_to, gmail_from, gmail_pass, message)


def alarm_email(temperature, email_to, gmail_from, gmail_pass):
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S %p")
    message = "From: " + gmail_from + "\nTo: " + email_to + "\nSubject: Temperature sensor alert\n\n" + dt + "\nTemperature is: " + str(temperature)
    send_email(email_to, gmail_from, gmail_pass, message)


def send_email(email_to, gmail_from, gmail_pass, message):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_from, gmail_pass)
        server.sendmail(gmail_from, email_to, message)
        server.close()
    except:  # but print if theres an email issue
        logging.info("There was a problem sending an email")
        print("There was a problem sending a mail alert!")


def led_control(chan):
    # 11 = yellow
    # 13 = red
    # 15 = green
    GPIO.output(chan, True)  ## Turn on Led
    time.sleep(1)
    GPIO.output(chan, False)  ## Turn off Led
    time.sleep(1)


if __name__ == "__main__":
    too_cold = 22.0
    too_hot = 27.0
    start = time.time() - 600.0
    init_setup = True
    counter = 0
    logging.basicConfig(filename='/home/pi/temperatures.log', filemode='w', level=logging.DEBUG)
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(11, 4)
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S %p")
        output = '{0} - Temp: {1} C  Humidity: {2} %'.format(dt, temperature, humidity)
        print(output)
        if counter ==  50 and init_setup:
            logging.info("Sending initial email to: {}".format(config.email_to))
            init_setup_email(temperature, config.email_to, config.gmail_from, config.gmail_pass)
            init_setup = False
        if counter % 50 == 0:
            logging.info(output)
        counter += 1
        if temperature <= too_cold:
            led_control(15)
        elif temperature >= too_hot:
            led_control(13)
        else:
            led_control(11)
        if temperature <= too_cold or temperature >= too_hot:
            now = time.time()
            if now - start > 600.0:
                start = time.time()
                alarm_email(temperature, config.email_to, config.gmail_from, config.gmail_pass)
