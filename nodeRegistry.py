from nodes import *
from common import *
from reader import *
from dbc import *
from NodeRegistrySettings import *

class NodeRegistry(object):

	"""
	
	"""

	def __init__(self,graph,settings=None):
		super(NodeRegistry, self).__init__()
		self.lookup = {}
		self.registry = {}
		self.parent = graph
		self.dbc = DBC(self)
		self.reader = Reader(self)
		if settings:
			self.settings = settings.copy()
		else:
			self.settings = NodeRegistrySettings()

	def _add(self,name,data=None):

		"""
		Private helper for add() and addAll()
		"""

		if type(name) == str:
			lname = name.lower()
			if lname not in self.lookup:
				n = self.lookup[lname] = Node(name,data)
				self.registry[n] = {}
				return n
			else:
				return self.lookup[lname]
		elif type(name) == Node:
			return name
		else:
			return None

	def add(self,name,data=None):

		"""
		Adds a single node to the graph.

		`name` should be a string
		`data` may be anything

		returns NodeList contaning newly created Node
		"""

		return NodeList([self._add(name,data)],self)

	def addAll(self,names,data=None):

		"""
		Adds multiple nodes to the graph.

		`names` should be a list of strings. If it is just a string, the add
			method will be called instead.
		`data` may be anything. All created nodes will have the same data.

		returns NodeList contining newly created Nodes
		"""

		if type(names) == str:
			return self.add(names,data)
		return NodeList([self._add(n) for n in names],self)


	def get(self,name,create=0,load=1,data=None):

		"""
		Gets nodes by name from the graph.

		`name` must be either a string or a list of strings
		If `create` is True, new nodes for all missing names will be created
		If `load` is True, unfound nodes will be searched for in the connected
			database as long as such a database is connected.
		`data` may be anything, used only when creating new nodes

		returns NodeList of all nodes found
		"""

		coerceType(create,int,0)
		coerceType(load,int,0)
		name = enlist(name)

		if load and self.dbc.isConnected():
			return self.dbc.load(name)
		else:
			if create:
				return self.addAll(name,data)
			else:
				return NodeList([self.lookup[n.lower()] for n in name if n.lower() in self.lookup],self)


	def rel(self,name):

		"""
		Gets all nodes related by the given name(s)

		`name` must be a string or list of strings

		returns NodeList
		"""
		return self.get(name).rel('_connects')
		

	def relate(self,left,right,leftward,rightward):

		"""
		Relates two nodes with by the given relational names

		`left` and `right` must be lists of (some combination of) strings,
			Nodes, tuples, or NodeTuples
		`leftward` and `rightward` must be strings or Nodes. `leftward` is a
			name denoting `left`; `rightward` denoting `right`. Example:

		relate('radiohead',['ok computer','kid a','hail to the thief'],'artists','albums')

		returns None
		"""

		left = tuplate(left,create=1,load=0,registry=self)
		right = tuplate(right,create=1,load=0,registry=self)
		addLeft = self.settings.MANAGE_CONNECTIONS and leftward and leftward[0] != "_"
		addRight = self.settings.MANAGE_CONNECTIONS and rightward and rightward[0] != "_"
		leftward = None if not leftward else self.get(leftward,create=1,load=0).first()
		rightward = None if not rightward else self.get(rightward,create=1,load=0).first()
		acc = self.settings.ACCUMULATE_RELATIONSHIPS

		for l in left:
			if leftward and addLeft:
				self.relate(leftward,l.node,"","_connects")
			for r in right:
				if rightward:
					if addRight:
						self.relate(rightward,r.node,"","_connects")
					rnew = rightward not in self.registry[l.node]
					if rnew:
						self.registry[l.node][rightward] = NodeList([],self)
					self.registry[l.node][rightward].append((r.node,r.weight))
				if leftward:
					lnew = leftward not in self.registry[r.node]
					if lnew:
						self.registry[r.node][leftward] = NodeList([],self)
					self.registry[r.node][leftward].append((l.node,l.weight))