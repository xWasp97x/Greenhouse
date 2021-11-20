import yaml
import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTMessageInfo
import random
import json
import time


class Generator:
	def __init__(self, config_path='./config.yaml', delay: int = 3):
		with open(config_path, 'r') as file:
			self.config = yaml.safe_load(file)

		self.client = mqtt.Client('generator')
		config = self.config['MQTT_BROKER']
		self.broker = config['address']
		self.port = config['port']
		self.qos = config['qos']
		self.topic = config['topic']
		self.client.connect(self.broker, self.port)
		self.delay = delay

	@staticmethod
	def new_payload() -> str:
		payload = {"sensors": {"LightReader": random.randint(0, 100), "MoistureReader": random.randint(0, 100)},
				   "actuators": {"LED": {"available": bool(random.randint(0, 1)), "info": "0%"},
								 "Pump": {"available": bool(random.randint(0, 1)), "info": ""},
								 "MoistureController": {"enabled": bool(random.randint(0, 1)),
														"busy": bool(random.randint(0, 1))},
								 "LightController": {"enabled": bool(random.randint(0, 1)),
													 "busy": bool(random.randint(0, 1))}},
				   "controllers": {},
				   "timestamp": time.time()}

		return json.dumps(payload)

	def loop(self):
		self.client.loop_start()
		while True:
			payload = self.new_payload()
			response: MQTTMessageInfo
			response = self.client.publish(self.topic, payload, self.qos)
			while response.rc != 0:
				print('Failed publishing new message')
				while self.client.reconnect() != 0:
					print('Reconnecting...')
					time.sleep(10)
				response = self.client.publish(self.topic, payload, self.qos)
				time.sleep(0.1)
			print(time.time())
			time.sleep(self.delay)


if __name__ == '__main__':
	generator = Generator()
	generator.loop()
