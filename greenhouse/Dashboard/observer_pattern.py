class Observer:
	def update(self, payload):
		raise NotImplementedError


class Observable:
	def __init__(self):
		self.observers = set()

	def add_observer(self, observer: Observer):
		self.observers.add(observer)

	def remove_observer(self, observer: Observer):
		self.observers.remove(observer)

	@staticmethod
	def notify_observer(observer: Observer, payload):
		observer.update(payload)

	def notify_observers(self, payload):
		[self.notify_observer(observer, payload) for observer in self.observers]
