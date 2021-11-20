from mqtt_as import MQTTClient, config
import network
import ubinascii
import machine
import uasyncio
from sensorreader import ADCReader
from greenhouse.esp32.actuator import Actuator
from controller import Controller
import ujson as json
import time


class MQTTLogger:
	def __init__(self, wlan: network.WLAN, ssid, pwd, broker, port, topic, qos, sensors: list, actuators: list, controllers: list):
		self.wlan = wlan
		self.id = ubinascii.hexlify(machine.unique_id())
		config['server'] = broker
		config['port'] = port
		config['client_id'] = self.id
		config['will'] = (topic, 'Disconnecting...', qos)
		config['ssid'] = ssid
		config['wifi_pw'] = pwd
		self.client = MQTTClient(config)
		self.topic = topic
		self.broker = broker
		self.port = port
		self.qos = qos
		self.sensors = sensors
		self.controllers = controllers
		self.actuators = actuators
		self.event_loop = uasyncio.get_event_loop()
		self.event_loop.create_task(self.connect())

	async def reset_wifi(self):
		self.wlan.disconnect()

		while self.wlan.isconnected():
			await uasyncio.sleep(1)

		self.wlan.active(False)

	def wifi_connected(self) -> bool:
		return self.wlan.isconnected()

	async def connect(self):
		await self.reset_wifi()

		print('[{}] Connecting to "{}"...'.format(self.__class__.__name__, self.broker))
		await self.client.connect()
		while not self.client.isconnected():
			await uasyncio.sleep(1)
		print('[{}] Connected'.format(self.__class__.__name__))

	async def send(self, payload: str):
		await self.client.publish(self.topic, payload, qos=self.qos)

	def get_payload(self) -> str:
		payload_dict = {'timestamp': time.time(),
						'sensors': {},
						'actuators': {},
						'controllers': {}}

		sensor: ADCReader
		for sensor in self.sensors:
			payload_dict['sensors'][sensor.__class__.__name__] = sensor.value

		actuator: Actuator
		for actuator in self.actuators:
			class_name = actuator.__class__.__name__
			payload_dict['actuators'][class_name] = {}
			payload_dict['actuators'][class_name]['available'] = actuator.available
			payload_dict['actuators'][class_name]['info'] = actuator.info

		controller: Controller
		for controller in self.controllers:
			class_name = controller.__class__.__name__
			payload_dict['actuators'][class_name] = {}
			payload_dict['actuators'][class_name]['enabled'] = controller.enabled
			payload_dict['actuators'][class_name]['busy'] = controller.busy

		payload = json.dumps(payload_dict, separators=(',', ':'))

		return payload

	async def loop(self, delay):
		while True:
			while not self.client.isconnected():
				await uasyncio.sleep(5)

			payload = self.get_payload()

			await self.send(payload)

			await uasyncio.sleep(delay)


