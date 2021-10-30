from actuator import *
from sensorreader import *
import uasyncio
from observer import Observer
from actuator import Actuator


class Controller:
	def __init__(self):
		super().__init__()
		self.busy = False
		self.event_loop = uasyncio.get_event_loop()
		self.enabled = False

	@staticmethod
	def wait_hardware() -> bool:
		await uasyncio.sleep_ms(1)
		# hw: Actuator
		# return any([not hw.available for hw in self.get_hw_instances()])

	def enable(self):
		self.enabled = True
		print('{} enabled'.format(self.__class__.__name__))

	def disable(self):
		self.enabled = False
		print('{} disabled'.format(self.__class__.__name__))

	def set_state(self, state: bool):
		map = {True: self.enable,
			   False: self.disable}

		map[state]()


class SimpleController(Controller, Observer):
	def __init__(self, reader: ADCReader, actuator: Actuator):
		super().__init__()
		self.actuator = actuator
		self.recent_hit = False
		reader.add_observer(self)

	def update(self, new_value):
		self.event_loop.create_task(self.run(new_value))

	def check_requisites(self) -> bool:
		return (self.actuator.available or self._busy) and self.enabled

	def reset(self):
		self.actuator.power_off()
		self.actuator.unlock()
		self.recent_hit = False
		self._busy = False

	def disable(self):
		self.enabled = False
		print('{} disabled'.format(self.__class__.__name__))
		if self._busy:
			self.reset()

	def first_hit_actions(self):
		self._busy = True
		self.actuator.lock()
		self.recent_hit = True

	async def run(self, latest_value):
		raise NotImplementedError


class MoistureController(SimpleController):
	def __init__(self, reader: MoistureReader, pump: Pump, low_threshold: int, high_threshold: int,
				 keep_on_secs: int, irrigation_delay: int):
		super().__init__(reader, pump)
		self.reader = reader
		self.low_threshold = low_threshold
		self.high_threshold = high_threshold
		self.keep_on_secs = keep_on_secs
		self.irrigation_delay = irrigation_delay
		self.actuator.power_off()

	def correct_moisture(self, latest_value) -> bool:
		return self.low_threshold <= latest_value <= self.high_threshold

	def under_threshold(self, latest_value) -> bool:
		return latest_value < self.low_threshold

	def over_threshold(self, latest_value) -> bool:
		return latest_value > self.high_threshold

	async def irrigate(self):
		self.actuator.power_on()
		await uasyncio.sleep(self.keep_on_secs)
		self.actuator.power_off()
		await uasyncio.sleep(self.irrigation_delay)

	async def run(self, latest_value):
		if not self.check_requisites():
			return

		if self.correct_moisture(latest_value):
			self.reset()
			return

		if not self.recent_hit and self.under_threshold(latest_value):
			print('Moisture level {} < {} !'.format(latest_value, self.low_threshold))
			self.recent_hit = True

		while not self.over_threshold(self.reader.value):
			self.actuator.lock()
			await self.irrigate()

		self.reset()


class LightController(SimpleController):
	def __init__(self, reader: LightReader, led: LED, threshold: int):
		super().__init__(reader, led)
		self.threshold = threshold
		self.actuator.power_off()

	def led_value(self, light_value) -> int:
		slack = self.threshold - light_value
		return slack * 100 / self.threshold

	async def run(self, latest_value):
		if not self.check_requisites():
			return

		if latest_value >= self.threshold:
			self.reset()
			return

		if not self.recent_hit:
			print('Light level {} < {} !'.format(latest_value, self.threshold))
			self.first_hit_actions()

		self.actuator.percentage(self.led_value(latest_value))


class TemperatureController(Controller):
	def __init__(self, reader: TemperatureReader, min_threshold: int, max_threshold: int, hysteresis: int, heater: Heater, roof_opener: RoofOpener, inertia: int, loop_delay: float):
		super().__init__(loop_delay)
		self.reader = reader
		self.min_th = min_threshold
		self.max_th = max_threshold
		self.hysteresis = hysteresis
		self.inertia = inertia
		self.heater = heater
		self.roof_opener = roof_opener

	def under_threshold(self, temp: float) -> bool:
		return temp < self.min_th

	def over_threshold(self, temp: float) -> bool:
		return temp > self.max_th

	def out_of_range(self, temp: float) -> bool:
		return self.under_threshold(temp) or self.over_threshold(temp)

	def hardware_needed(self) -> list:
		return self.controlled_hardware

	async def _take_actions(self, available_hardware: list) -> bool:
		temp = self.observer.value
		if not self.out_of_range(temp):
			return True

		if self.under_threshold(temp):
			pass
			# await self.heat()
		elif self.over_threshold(temp):
			await self.cool()

	def get_controlled_hardware(self) -> list:
		return [Heater, RoofOpener]

	@staticmethod
	def heat_power(temp_delta: float) -> int:
		return int(temp_delta * 10)

	async def heat(self):
		self.roof_opener.lock()
		# self.heater.lock()

		target = self.min_th + self.hysteresis
		while self.observer.value < target:
			delta = target - self.observer.value
			self.roof_opener.close()
			# self.heater.percentage(self.heat_power(delta))
			await uasyncio.sleep(self.inertia)
		self.roof_opener.unlock()
		# self.heater.unlock()

	async def cool(self):
		self.roof_opener.lock()
		# self.heater.lock()

		target = self.max_th - self.hysteresis
		while self.observer.value > target:
			# self.heater.power_off()
			self.roof_opener.open()
			await uasyncio.sleep(self.inertia)
		self.roof_opener.unlock()
		# self.heater.unlock()

	def busy(self):
		return self.working or self.waiting

	async def loop(self):
		while True:
			await uasyncio.sleep(self.loop_delay)
			print(self.observer.value)
			if self.busy() or self.roof_opener.moving or self.observer.value is None:
				continue

			print(self.observer.value)
			if self.out_of_range(self.observer.value):
				self.waiting = True
