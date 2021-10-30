from machine import RTC
from controller import *


class Phase:
	NIGHT = 0
	DAY = 1
	MORNING = 2
	AFTERNOON = 3
	EVENING = 4


BOUNDS = {Phase.DAY: ((8, 0), (20, 0)),
		  Phase.NIGHT: ((20, 0), (8, 0)),
		  Phase.MORNING: ((8, 0), (12, 0)),
		  Phase.AFTERNOON: ((12, 0), (18, 0)),
		  Phase.EVENING: ((18, 0), (24, 0))}


class DayNightManager:
	ENABLING = {Phase.DAY: {LightController: True},
				Phase.NIGHT: {LightController: False}}

	def __init__(self):
		self.rtc = RTC()

	@staticmethod
	def tuple_to_secs(tup: tuple):
		return tup[0] * 60 + tup[1]

	def greater(self, a: tuple, b: tuple) -> bool:
		a_int = self.tuple_to_secs(a)
		b_int = self.tuple_to_secs(b)

		return a_int > b_int

	def lower(self, a: tuple, b: tuple) -> bool:
		a_int = self.tuple_to_secs(a)
		b_int = self.tuple_to_secs(b)

		return a_int < b_int

	def between(self, a: tuple, left: tuple, right: tuple) -> bool:
		a_int = self.tuple_to_secs(a)
		left_int = self.tuple_to_secs(left)
		right_int = self.tuple_to_secs(right)

		if left_int > right_int:
			return self.between(a, left, (24, 0)) or self.between(a, (0, 0), right)

		return left_int <= a_int <= right_int

	def get_phase(self) -> Phase.name:
		now = self.rtc.datetime()[4: 6]

		for phase, bounds in BOUNDS.items():
			if self.between(now, bounds[0], bounds[1]):
				return phase




