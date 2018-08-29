#!/usr/bin/python
import subprocess
# noinspection PyUnresolvedReferences
import Adafruit_DHT
import smtplib
from datetime import datetime
import time
import RPi.GPIO as GPIO  # Import GPIO library
import logging
import config
import shedule

GPIO.setmode(GPIO.BOARD)  # Use board pin numbering
GPIO.setup(11, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)




def init_setup_email(temperature, email_to, gmail_from, gmail_pass, dt):
    ip_std = subprocess.Popen(['hostname', '-I'], stdout=subprocess.PIPE)
    ip = ip_std.communicate()[0]
    message = "From: {0}\nTo: {1}\nSubject: Temperature all good\n\n{2}\nTemperature is: {3}C at IP: {4}".format(
        gmail_from, email_to, dt, str(temperature), ip)
    send_email(email_to, gmail_from, gmail_pass, message, dt)


def alarm_email(temperature, email_to, gmail_from, gmail_pass, dt):
    message = "From: {0}\nTo: {1}\nSubject: Temperature sensor alert\n\n{2}\nTemperature is: {3}".format(gmail_from,
        email_to, dt, str(temperature))
    send_email(email_to, gmail_from, gmail_pass, message, dt)


def send_functional_email():
    message = "From: {0}\nTo: {1}\nSubject: Pi working properly\n\nDON'T PANIC!!".format(config.gmail_from, config.email_to)
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S %p")
    send_email(config.email_to, config.gmail_from, config.gmail_pass, message, dt)


def send_email(email_to, gmail_from, gmail_pass, message, dt):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_from, gmail_pass)
        server.sendmail(gmail_from, email_to, message)
        server.close()
    except:
        logging.info("{} - There was a problem sending an email".format(dt))
        print("There was a problem sending a mail alert!")


def activate_led(temperature):
    if temperature <= too_cold:
        led_control(15)
    elif temperature >= too_hot:
        led_control(13)
    else:
        led_control(11)


def led_control(chan):
    # 11 = yellow
    # 13 = red
    # 15 = green
    GPIO.output(chan, True)  # Turn on Led
    time.sleep(1)
    GPIO.output(chan, False)  # Turn off Led
    time.sleep(1)


if __name__ == "__main__":
    too_cold = 22.0
    too_hot = 27.0
    start = time.time() - 600.0
    init_setup = True
    counter = 0
    logging.basicConfig(filename='/home/pi/temperatures.log', filemode='w', level=logging.DEBUG)
    schedule.every().day.at("12:15").do(send_functional_email)
    schedule.every().day.at("18:00").do(send_functional_email)
    while True:
        curr_humidity, curr_temp = Adafruit_DHT.read_retry(11, 4)
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %p")
        output = '{0} - Temp: {1} C  Humidity: {2} %'.format(date_time, curr_temp, curr_humidity)
        print(output)
        if counter == 50 and init_setup:
            logging.info("{0} - Sending initial email to: {1}".format(date_time, config.email_to))
            init_setup_email(curr_temp, config.email_to, config.gmail_from, config.gmail_pass, date_time)
            init_setup = False
        if counter % 50 == 0:
            logging.info(output)
        activate_led(curr_temp)
        if curr_temp <= too_cold or curr_temp >= too_hot:
            now = time.time()
            if now - start > 600.0:
                start = time.time()
                alarm_email(curr_temp, config.email_to, config.gmail_from, config.gmail_pass, date_time)
        schedule.run_pending()
        counter += 1
