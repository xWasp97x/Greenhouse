from controller import Controller
from greenhouse.esp32.actuator import Actuator
from observer import Observer, Observable
import uasyncio


class Logger:
	def __init__(self, hardware: list, readers: list, controllers: list):
		self.hardware = hardware
		self.observers = {id(reader): [reader.__class__.__name__.replace('Reader', ''), Observer()] for reader in readers}
		reader: Observable
		for reader in readers:
			reader.add_observer(self.observers[id(reader)][1])
		self.controllers = controllers

	def log(self):
		print('\n')
		print('Actuator:')
		hardware: Actuator
		for hardware in self.hardware:
			print('\t{}: {} ({})'.format(hardware.__class__.__name__, 'free' if hardware.available else 'busy', hardware.info))

		print('Controllers:')
		controller: Controller
		for controller in self.controllers:
			print('\t{} enabled: {}'.format(controller.__class__.__name__, controller.enabled))

		print('Sensors:')
		observer: Observer
		for observed, observer in self.observers.values():
			print('\t{}: {}'.format(observed, observer.value))

	async def loop(self, delay):
		while True:
			self.log()
			await uasyncio.sleep(delay)
