#!/usr/bin/env python
from datetime import datetime
import subprocess
import logging
import smtplib
import config
import time
import schedule
import Adafruit_DHT
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

pnconfig = PNConfiguration()
pnconfig.subscribe_key = "sub"
pnconfig.publish_key = "pub"
pnconfig.ssl = False
pubnub = PubNub(pnconfig)

sensor=11
pin=4


class EmailData(object):
    def __init__(self, subject, temp, humidity):
        self.subject = subject
        self.temp = str(temp)
        self.humidity = str(humidity)
        self.dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S %p")
        self.ip = subprocess.Popen(['hostname', '-I'], stdout=subprocess.PIPE).communicate()[0]

    def send_email(self):
        message = "From: {0}\nTo: {1}\nSubject: {2}\n\nTime={3}\tTemperature = {4}C\tHumidity={5}\tIP = {6}".format(
            config.gmail_from,
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


class THLogger(object):
    def __init__(self):
        self.start = time.time() - config.delay_email_seconds
        self.init_setup = True
        self.counter = 0

    def logging(self):
        while True:
            curr_humidity, curr_temp, date_time, output = self._get_sensor_data()
            if self.counter == 50 and self.init_setup:
                logging.info("{0} - Sending initial email to: {1}".format(date_time, config.email_to))
                send_functional_email()
                self.init_setup = False
            if self.counter % 50 == 0:
                logging.info(output)
            if curr_temp <= config.too_cold or curr_temp >= config.too_hot:
                now = time.time()
                if now - self.start > config.delay_email_seconds:
                    self.start = time.time()
                    email = EmailData("Temperature alert!!", curr_temp, curr_humidity)
                    email.send_email()
            schedule.run_pending()
            dictionary = {"eon": {"Temperature": curr_temp, "Humidity": curr_humidity}}
            DHT_Read = ('Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(curr_temp, curr_humidity)) #TODO: Fix this hack
            pubnub.publish().channel('ch2').message([DHT_Read]).pn_async(publish_callback)
            pubnub.publish().channel("eon-chart").message(dictionary).pn_async(publish_callback)
            self.counter += 1
            time.sleep(60)

    @staticmethod
    def _get_sensor_data():
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %p")
        curr_humidity, curr_temp = Adafruit_DHT.read_retry(sensor, pin)
        output = '{0} - Temp: {1} C  Humidity: {2} %'.format(date_time, curr_temp, curr_humidity)
        print(output)
        return curr_humidity, curr_temp, date_time, output


def send_functional_email():
    subject = "Device correctly logging temperature and humidity"
    curr_humidity, curr_temp = Adafruit_DHT.read_retry(sensor, pin)
    email = EmailData(subject, curr_temp, curr_humidity)
    email.send_email()

def publish_callback(result, status):
    pass


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
