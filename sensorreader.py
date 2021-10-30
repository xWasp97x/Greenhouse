from machine import ADC, Pin
import uasyncio
from observer import Observable
import onewire, ds18x20
from time import sleep


class MovingAverage:
	def __init__(self, values_count: int):
		self.i = 0
		self.values = [None] * values_count

	def add_value(self, value):
		self.values[self.i] = value
		self.i = (self.i + 1) % len(self.values)

	def average(self):
		values = [v for v in self.values if v is not None]
		return sum(values) / len(values)


class ADCReader(Observable):
	def __init__(self, sensor_pin: int, history_length=50):
		super().__init__()
		self.pin = ADC(Pin(sensor_pin))
		self.pin.atten(ADC.ATTN_11DB)
		self.min = 0  # in volts
		self.max = 3  # in volts
		self.min_offset = 0  # read - theoretic
		self.max_offset = 0  # read - theoretic
		self.moving_average = MovingAverage(history_length)
		self.decimals = 3

	def raw_value(self) -> int:
		return self.pin.read()

	def normalized(self) -> float:
		return self.raw_value() / 4095

	def voltage(self) -> float:
		return (self.normalized() * 3.3) + self.min_offset + self.max_offset

	def percentage(self) -> int:
		return int(self.voltage() / self.max * 100)

	def get_value(self):
		return self.percentage()

	def update_value(self):
		self.moving_average.add_value(self.get_value())
		avg = self.moving_average.average()
		self.value = int(avg) if self.decimals == 0 else round(self.moving_average.average(), self.decimals)

	async def loop(self, delay):
		while True:
			self.update_value()
			await uasyncio.sleep(delay)


class MoistureReader(ADCReader):
	def __init__(self, sensor_pin: int, history_length, max_voltage, decimals):
		super().__init__(sensor_pin, history_length)
		self.max = max_voltage
		self.decimals = decimals

	def get_value(self):
		return 100 - self.percentage()


class LightReader(ADCReader):
	def __init__(self, sensor_pin: int, history_length, max_voltage, decimals):
		super().__init__(sensor_pin, history_length)
		self.max = max_voltage
		self.decimals = decimals


class TemperatureReader(Observable):
	def __init__(self, pin: int):
		super().__init__()
		self.pin = Pin(pin)
		self.strip = ds18x20.DS18X20(onewire.OneWire(self.pin))
		fails = 0
		while len(self.strip.scan()) == 0 and fails < 10:
			fails += 1
			sleep(1)
		self.sensor = self.strip.scan()[0]

	async def loop(self, delay):
		while True:
			try:
				self.strip.convert_temp()
				await uasyncio.sleep(1)
				self.value = self.strip.read_temp(self.sensor)
			except:
				pass
			await uasyncio.sleep(delay)


class EndStopReader(Observable):
	def __init__(self, pin: int):
		super().__init__()
		self.pin = Pin(pin, Pin.IN)

	def register_handler(self, function):
		self.pin.irq(trigger=Pin.IRQ_RISING, handler=function)

	def active(self) -> bool:
		return bool(self.pin.value())

	async def loop(self, delay):
		pass
