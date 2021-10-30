class Observable:
	def __init__(self):
		self.observers = []
		self._value = None

	def update_observers(self, new_value):
		observer: Observer
		[observer.update(new_value) for observer in self.observers]

	def add_observer(self, observer_hook):
		self.observers.append(observer_hook)

	@property
	def value(self):
		return self._value

	@value.setter
	def value(self, new_value):
		if new_value != self.value:
			self.update_observers(new_value)
			self._value = new_value


class Observer:
	def __init__(self):
		self.changed = False
		self._value = None

	def update(self, new_value):
		self.value = new_value

	@property
	def value(self):
		self.changed = False
		return self._value

	@value.setter
	def value(self, new_value):
		self.changed = True
		self._value = new_value
