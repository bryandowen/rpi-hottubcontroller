class Queue:

	def __init__(self, maxSize=5):
		self.items = []
		self.maxSize = maxSize

	def size(self):
		return len(self.items)

	def isEmpty(self):
		return self.items == []

	def enqueue(self, item):
		while self.size() >= self.maxSize: # Maintain max queue size
			self.dequeue()
		self.items.insert(0, item)

	def dequeue(self):
		return self.items.pop()

	def inspect(self):
		return self.items

	def drain(self):
		self.items = []
