from nodes import *
from nodeRegistry import NodeRegistry

class Graph(object):
	"""docstring for Graph"""
	def __init__(self):
		super(Graph, self).__init__()
		self.registry = NodeRegistry(self)
		self.settings = self.registry.settings

	# Retrieval methods
	def get(self,name):
		return self.registry.get(name)

	def rel(self,name):
		return self.registry.rel(name)

	def all(self):
		return NodeList((list)(self.registry.registry.keys()),self.registry);

	# Population methods
	def add(self,name,data=None):
		return self.registry.add(name,data)

	def read(self,filename):
		return self.registry.reader.read(filename)

	def eval(self,exp):
		return self.registry.reader.eval(exp)

	def biject(self,left,right,relation):
		return self.registry.relate(left,right,relation,relation)

	def direct(self,left,right,relation):
		return self.registry.relate(left,right,relation,"")

	def relate(self,left,right,leftward,rightward):
		return self.registry.relate(left,right,leftward,rightward)

	# Persistence methods
	def connect(self,filename):
		return self.registry.dbc.connect(filename)

	def dump(self):
		return self.registry.dbc.dump()

	def initializeDB(self,imsure=0):
		return self.registry.dbc.initialize(imsure)