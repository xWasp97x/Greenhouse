import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTMessage
from loguru import logger
from observer_pattern import Observable
import json
from time import sleep


class Subscriber(Observable):
    def __init__(self, broker: str, port: int, topic: str, qos: int, client_id: str = 'dashboard'):
        super().__init__()
        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self.on_connect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_message = self.on_message
        self.broker = broker
        self.port = port
        self.topic = topic
        self.qos = qos

    def on_connect(self, client, userdata, flags, rc):
        logger.debug(f'CONNACK: {rc}')
        logger.success(f'Successfully connected.')
        self.subscribe()

    def connect(self):
        logger.info(f'Connecting to {self.broker}:{self.port}...')
        self.client.connect(self.broker, self.port)

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        logger.success(f'Subscribed: {mid} | {granted_qos}')

    def subscribe(self):
        while not self.client.is_connected():
            logger.warning(f"Reconnecting to the broker...")
            self.client.reconnect()
            sleep(3)

        self.client.subscribe(self.topic, self.qos)

    def on_message(self, client, userdata, msg: MQTTMessage):
        logger.debug(f'New message: topic: {msg.topic} | qos: {msg.qos} | payload: {msg.payload}')
        payload = self.parse_payload(msg.payload)
        self.notify_observers(payload)

    @staticmethod
    def parse_payload(message) -> dict:
        try:
            payload = json.loads(message)
        except json.decoder.JSONDecodeError as je:
            logger.warning('Dropping payload; {je}')
            return None
        assert set(payload.keys()) == {'datetime', 'sensors', 'actuators', 'controllers'}
        assert isinstance(payload['datetime'], str) or isinstance(payload['timestamp'], float)
        assert isinstance(payload['sensors'], dict)
        assert isinstance(payload['actuators'], dict)
        assert isinstance(payload['controllers'], dict)

        parsed = {'datetime': payload['datetime'],
                  'sensors': payload['sensors'],
                  'actuators': payload['actuators'],
                  'controllers': payload['controllers']}

        return parsed

    def start(self):
        logger.debug('Stating loop..')
        self.client.loop_start()
        logger.debug('Loop started')
