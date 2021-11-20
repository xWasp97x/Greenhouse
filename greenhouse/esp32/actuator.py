from machine import Pin, PWM
from sensorreader import EndStopReader
from utime import sleep_ms


class Actuator(object):
	_instances = []

	def __new__(cls, *args, **kwargs):
		classes = [type(instance) for instance in Actuator._instances]
		if type(cls) not in classes:
			new_instance = object.__new__(cls)
			Actuator._instances.append(new_instance)
			return new_instance
		return Actuator._instances[classes.index(type(cls))]

	def __init__(self):
		self.available = True
		self.info = ""

	def lock(self):
		self.available = False

	def unlock(self):
		self.available = True

	def power_on(self):
		raise NotImplementedError

	def power_off(self):
		raise NotImplementedError


class OnOffActuator(Actuator):
	def __init__(self, pin: int):
		super().__init__()
		self.pin = Pin(pin, Pin.OUT)
		self.power_off()

	def power_off(self):
		self.pin(0)

	def power_on(self):
		self.pin(1)


class PWMActuator(Actuator):
	def __init__(self, pin: int):
		super().__init__()
		self.max = 1023
		self.min = 0
		self.pin = PWM(Pin(pin), 5000)
		self.status = None
		self.power_off()

	def power_on(self):
		self.duty(self.max)
		self.info = "100%"

	def power_off(self):
		self.duty(self.min)
		self.info = "0%"

	def duty(self, duty: int) -> bool:
		if duty < 0 or duty > 1023:
			return False
		self.status = duty
		self.pin.duty(duty)
		return True

	@staticmethod
	def perc_to_duty(perc: int) -> int:
		return int(perc * 1023/100)

	def percentage(self, perc: int) -> bool:
		self.info = "{}%".format(perc)
		return self.duty(self.perc_to_duty(perc))

	def increase(self) -> bool:
		return self.duty(self.status + 1)

	def decrease(self) -> bool:
		return self.duty(self.status - 1)


class Pump(OnOffActuator):
	def __init__(self, pin: int):
		super().__init__(pin)
		self.power_off()


class LED(PWMActuator):
	def __init__(self, pin: int):
		super().__init__(pin)


class Heater(PWMActuator):
	def __init__(self, pin: int):
		super().__init__(pin)


class RoofOpener(Actuator):
	class StopMotor(Exception):
		pass

	CLOSE_DIR = -1
	OPEN_DIR = 0

	def __init__(self, brake_pin: int, sleep_pin: int, dir_pin: int, step_pin: int, close_switch: EndStopReader,
				 open_switch: EndStopReader):
		super().__init__()
		self.brake_pin = Pin(brake_pin, Pin.OUT)
		self.sleep_pin = Pin(sleep_pin, Pin.OUT)
		self.dir_pin = Pin(dir_pin, Pin.OUT)
		self.step_pin = Pin(step_pin, Pin.OUT)
		self.moving = False
		self.close_switch = close_switch
		self.close_switch.register_handler(self.stop)
		self.open_switch = open_switch
		self.open_switch.register_handler(self.stop)
		self.step_delay = 2  # ms
		self.max_gap = 1 * 200  # rotations * rotations/round

	def sleep(self):
		self.sleep_pin.on()

	def awake(self):
		self.sleep_pin.off()

	def stop(self):
		print('stopped')
		raise self.StopMotor()

	def valid_position(self) -> bool:
		return self.opened() ^ self.closed()

	def opened(self) -> bool:
		return self.open_switch.active()

	def closed(self) -> bool:
		return self.close_switch.active()

	def enable(self):
		self.brake_pin.off()

	def disable(self):
		self.brake_pin.on()

	def do_step(self):
		self.step_pin.on()
		sleep_ms(self.step_delay)
		self.step_pin.off()
		sleep_ms(self.step_delay)

	def rotate(self, steps: int, direction: int):
		self.enable()
		self.dir_pin.value(direction == 1)
		sleep_ms(5)

		for _ in range(steps):
			self.do_step()
		self.disable()

	def movement(self, direction, final_check) -> bool:
		if not self.valid_position():
			self.forced_close()
		self.moving = True
		try:
			self.rotate(steps=int(self.max_gap * 1.5), direction=direction)
		except self.StopMotor:
			pass
		self.moving = False
		return self.valid_position() and final_check()

	def forced_close(self):
		self.moving = True
		print('closing forcibly')
		while not self.closed():
			self.rotate(steps=50, direction=self.CLOSE_DIR)
		self.moving = False

	def open(self) -> bool:
		print('opening')
		return self.movement(direction=self.OPEN_DIR, final_check=self.opened)

	def close(self) -> bool:
		print('closing')
		return self.movement(direction=self.CLOSE_DIR, final_check=self.closed)
