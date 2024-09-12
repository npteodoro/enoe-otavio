import paho.mqtt.client as mqtt
import json
import sys
import time
from queue import Queue
import logging
import os
import base64

# Configuração do logger para o MQTTHandlerSubscriber
mqtt_logger = logging.getLogger('MQTTHandlerSubscriber')
mqtt_logger.setLevel(logging.INFO)

mqtt_handler = logging.FileHandler('./logs/MQTTHandlerSubscriber.log')
mqtt_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
mqtt_logger.addHandler(mqtt_handler)


class MQTTHandlerSubscriber:
    def __init__(self, broker_address, port, username=None, password=None, MAX_RETRIES=5, RETRY_WAIT_TIME=10):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connected_flag = False

        self.MAX_RETRIES = MAX_RETRIES
        self.RETRY_WAIT_TIME = RETRY_WAIT_TIME
        self.port = port
        self.broker_address = broker_address

        self.queue = Queue()

        if username and password:
            self.client.username_pw_set(username, password)

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            mqtt_logger.info("Connected to broker")
            client.connected_flag = True
        else:
            mqtt_logger.error(f"Failed to connect, return code {rc}")
            client.connected_flag = False

    def connect(self):
        attempt = 0
        while attempt < self.MAX_RETRIES:
            try:
                self.client.connect(self.broker_address, port=self.port)
                self.client.loop_start()
                mqtt_logger.info("Successfully connected to MQTT broker")
                return
            except Exception as e:
                mqtt_logger.error(f"Failed to connect to MQTT broker (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")
                attempt += 1
                time.sleep(self.RETRY_WAIT_TIME)

        mqtt_logger.critical("Maximum connection attempts reached. Exiting....")
        sys.exit(1)

    def disconnect(self):
        self.client.disconnect()
        self.client.loop_stop()
        mqtt_logger.info("Disconnected from MQTT broker")

    def on_message(self, client, userdata, message):
        message_data = {
            'topic': message.topic,
            'message': message.payload.decode('utf-8')
        }
        mqtt_logger.info(f"Received {message_data['topic']}")
        self.queue.put(message_data)

    def subscribe(self, topic):
        try:
            self.client.subscribe(topic)
            mqtt_logger.info(f"Subscribed to topic: {topic}")
        except Exception as e:
            mqtt_logger.error(f"Failed to subscribe to topic {topic}: {e}")