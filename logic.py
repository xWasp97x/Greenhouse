from sensorreader import MoistureReader
import uasyncio
from machine import Pin
from controller import Controller, MoistureController
from actuator import Actuator
from daynightmanager import DayNightManager


class Logic:
	def __init__(self, hardware: list, controllers: list):
		self.blink_task = None
		self.hardware = hardware
		self.controllers = controllers
		self.led = Pin(2, Pin.OUT)
		self.led(1)
		self.day_night_manager = DayNightManager()

	@staticmethod
	def available_hardware(requested_hardware: list) -> list:
		return [hardware for hardware in requested_hardware if hardware.available]

	async def blink(self):
		while True:
			self.led(not self.led())
			await uasyncio.sleep(0.5)

	def blinking(self) -> bool:
		return self.blink_task is None

	async def loop(self, delay):
		while True:
			self.led(not self.led())
			controller: Controller
			for controller in self.controllers:
				states = []
				day_phase = self.day_night_manager.get_phase()
				enabling = self.day_night_manager.ENABLING[day_phase]
				class_name = controller.__class__

				if class_name in enabling.keys():
					states.append(enabling[class_name])
				else:
					states.append(True)
				controller.set_state(all(states))

			await uasyncio.sleep(delay)

