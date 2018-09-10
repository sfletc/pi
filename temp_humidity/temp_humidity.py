#!/usr/bin/env python
from datetime import datetime
import subprocess
import logging
import smtplib
import config
import time
import schedule
import RPi.GPIO as GPIO
import Adafruit_DHT

GPIO.setmode(GPIO.BOARD)  # Use board pin numbering
GPIO.setup(11, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)


class EmailData(object):
    def __init__(self, subject, temp, humidity):
        self.subject = subject
        self.temp = str(temp)
        self.humidity = str(humidity)
        self.dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S %p")
        self.ip = subprocess.Popen(['hostname', '-I'], stdout=subprocess.PIPE).communicate()[0]

    def send_email(self):
        message = "From: {0}\nTo: {1}\nSubject: {2}\n\nDate/time={3}\tTemperature = {4}C\tHumidity={5}%\tIP = {6}".format(config.gmail_from,
                                                                                                                         config.email_to,
                                                                                                                         self.subject,
                                                                                                                         self.dt,
                                                                                                                         self.temp,
                                                                                                                         self.humidity,
                                                                                                                         self.ip)
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.ehlo()
            server.starttls()
            server.login(config.gmail_from, config.gmail_pass)
            server.sendmail(config.gmail_from, config.email_to, message)
            server.close()
        except:
            logging.info("{} - There was a problem sending an email".format(self.dt))
            print("{} - There was a problem sending an email".format(self.dt))


class Led(object):
    def __init__(self):
        self.blue = 15#GPIO chan
        self.green = 11 #GPIO chan
        self.red = 13 #GPIO chan

    def select_led(self, temperature):
        if temperature <= config.too_cold:
            self.activate(self.blue)
        elif temperature >= config.too_hot:
            self.activate(self.red)
        else:
            self.activate(self.green)

    @staticmethod
    def activate(chan):
        GPIO.output(chan, True)  # Turn on Led
        time.sleep(1)
        GPIO.output(chan, False)  # Turn off Led
        time.sleep(1)


class THLogger(object):
    def __init__(self):
        self.start = time.time() - config.delay_email_seconds
        self.init_setup = True
        self.counter = 0
        self.leds = Led()
        self.previous_temp = 22.0

    def logging(self):
        while True:
            curr_humidity, curr_temp, date_time, output = self._get_sensor_data()
            if self.counter == 50 and self.init_setup:
                logging.info("{0} - Sending initial email to: {1}".format(date_time, config.email_to))
                send_functional_email()
                self.init_setup = False
            if self.counter % 50 == 0 and self.previous_temp - curr_temp < 8:
                logging.info(output)
            self.leds.select_led(curr_temp)
            if curr_temp <= config.too_cold or curr_temp >= config.too_hot:
                if self.previous_temp - curr_temp < 8.0:
                    now = time.time()
                    if now - self.start > config.delay_email_seconds:
                        self.start = time.time()
                        email = EmailData("Temperature alert!!", curr_temp, curr_humidity)
                        email.send_email()
            schedule.run_pending()
            self.previous_temp = curr_temp #hack to ignore spurious low readings
            self.counter += 1

    @staticmethod
    def _get_sensor_data():
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %p")
        curr_humidity, curr_temp = Adafruit_DHT.read_retry(11, 4)
        output = '{0} - Temp: {1} C  Humidity: {2} %'.format(date_time, curr_temp, curr_humidity)
        print(output)
        return curr_humidity, curr_temp, date_time, output


def send_functional_email():
    subject = "Device correctly logging temperature and humidity"
    curr_humidity, curr_temp = Adafruit_DHT.read_retry(11, 4)
    email = EmailData(subject, curr_temp, curr_humidity)
    email.send_email()


if __name__ == "__main__":
    start = time.time() - config.delay_email_seconds
    logging.basicConfig(filename=config.log, filemode='w', level=logging.DEBUG)
    logging.info("email: {0}, lower: {1}, upper: {2}, delay: {3}, morning: {4}, afternoon: {5}".format(config.email_to,
                                                                                                       config.too_cold,
                                                                                                       config.too_hot,
                                                                                                       config.delay_email_seconds,
                                                                                                       config.schedule_morning,
                                                                                                       config.schedule_afternoon))
    schedule.every().day.at(config.schedule_morning).do(send_functional_email)
    schedule.every().day.at(config.schedule_afternoon).do(send_functional_email)
    logger = THLogger()
    logger.logging()
