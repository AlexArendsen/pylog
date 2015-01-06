from common import *

class Node(object):
	"""
	Class representing a single node.

	It is important to note that Nodes, in isolation, are
	not bound to a single Graph (they are referenced in NodeTuples, which
	compose NodeLists, which are associated with a Graph's NodeRegistry).
	A node must have a name, and may optionally contain data, which may be of
	any type.
	"""
	def __init__(self, name, data):
		super(Node, self).__init__()
		self.name = name
		self.data = data
		self.loaded = False

	def __str__(self):
		return self.name
	__repr__ = __str__


class NodeList(object):
	
	"""
	Class representing a list of nodes.

	A NodeList is associated with a NodeRegistry (`parent`), and contains a
	list of NodeTuples (`nodes`)
	"""

	def __init__(self, nodes, registry):
		super(NodeList, self).__init__()
		self.nodes = tuplate(nodes)
		self.parent = registry
		self.sorted = False

	def __str__(self):
		return '[{0}]'.format(', '.join([n.node.name for n in self.nodes]))
	__repr__ = __str__

	def __iter__(self):
		for n in self.sort().nodes:
			yield n

	def __mul__(self,coefficient):
		out = NodeList(self.nodes,self.parent)
		for n in out:
			n.weight *= coefficient
		return out

	def __imul__(self,coefficient):
		for n in self:
			n.weight *= coefficient
		return self

	def append(self,node):

		"""
		Append node(s) to the NodeList. `node` argument may be a list of (any
		combination of) strings, Nodes, manually notated tuples, NodeTuples, or
		NodeLists.
		"""
		out = self.parent.settings.ACCUMULATE_RELATIONSHIPS or not self.contains(node)
		if out:
			self.nodes += tuplate(node,self.parent)
			self.sorted = False
		return out
	merge = append

	def contains(self,node):
		node = tuplate(node)[0].node
		for n in self.nodes:
			if n.node == node:
				return True
		return False

	def sort(self):

		"""
		Sorts all contained NodeTuples by weight, highest first. Nodes
		represented by multiple NodeTuples within the list are consolidated.
		"""

		if not self.sorted:
			reg = {}
			for n in self.nodes:
				if not n.node in reg:
					reg[n.node] = NodeTuple(n.node,0)
				reg[n.node].addWeight(n.weight)
			self.nodes = sorted([reg[k] for k in reg],key=lambda tup: tup.weight,reverse=True)
			self.sorted = True
		return self

	def isEmpty(self):
		return len(self.nodes) == 0

	def isLoaded(self):

		"""
		Returns True if all the nodes in this list have the `loaded` flag set
		to True. An empty list of nodes is considered not loaded and will
		return False; such a list is the result of a query for nodes which
		should (assumedly) exist, but do not (and must therefore be loaded).
		"""

		if self.isEmpty():
			return False
		for n in self.nodes:
			if not n.node.loaded:
				return False
		return True

	def setLoaded(self,l):

		"""
		Sets the loaded flag for all of the nodes in the list to the given
		value `l`
		"""

		for n in self:
			n.node.loaded = l

	def load(self):

		"""
		Load all of the nodes within this list from the database connected to
		the parent NodeRegistry. Does nothing if all nodes are already loaded
		or if no database is connected.
		"""

		if not self.isLoaded() and self.parent.dbc.isConnected():
			self.parent.dbc.load([n.node.name for n in self.nodes])
		return self

	def rel(self,name=None):

		"""
		Get NodeList of all nodes related to the nodes within this list by
		the given `name`. `name` may be a string or list of strings. Returns
		all related nodes if no name is given.
		"""

		self.sort()
		out = NodeList([],self.parent)
		if not name:
			for tup in [(self.parent.registry[n.node],n.weight) for n in self.nodes]:
				for rel in tup[0]:
					out.append(tup[0][rel]*tup[1])
		else:

			# Get relation node referenced by input `name`
			relation = [n.node for n in self.parent.get(name,load=0)]
			if not relation:
				return out

			# Iterate over list of tuples containing the relatives of this
			#	list's nodes and the weight
			for tup in [(self.parent.registry[n.node],n.weight) for n in self.nodes]:
				for r in relation:
					if r in tup[0]:
					 	out.append(tup[0][r]*tup[1])
		
		return out.sort().load()

	def eq(self,index):

		"""
		Get the node at the given `index` within this sorted list, returning
		None if `index` trespasses the number of nodes in the list
		"""

		self.sort()
		return None if index >= len(self.nodes) else self.nodes[index].node

	def first(self):

		"""
		Gets the first node in this list, returning None if one isn't found;
		alias for eq(0)
		"""

		return self.eq(0)

	def top(self,n):

		"""
		Return a NodeList contaning the first `n` nodes from this list
		"""

		return NodeList(self.nodes[:n],self.parent)

	def bottom(self,n):

		"""
		Return a NodeList containing the last `n` nodes from this list
		"""

		return NodeList(self.nodes[-n:],self.parent)

	def sublist(self,start,end):

		"""
		Return a NodeList containing nodes within this list starting at index
		`start` and ending at index `end`
		"""

		return NodeList(self.nodes[start:end],self.parent)

	def limit(self,nodes):

		"""
		Removes all nodes that are not within the given `nodes`; take the
		intersection between this list and the list provided. `nodes` may be a
		list of (any combination of) strings, nodes, manually notated tuples,
		NodeTuples, or NodeLists.
		"""

		self.sort()
		nodes = list(map(lambda tup: tup.node,tuplate(nodes,registry=self.parent)))
		return NodeList([n for n in self.nodes if n.node in nodes],self.parent)

	def exclude(self,nodes):

		"""
		Removes all of the given `nodes` from the list. `nodes` may be a list
		of (any combination of) strings, nodes, manually notated tuples,
		NodeTuples, or NodeLists.
		"""

		self.sort()
		nodes = list(map(lambda tup: tup.node,tuplate(nodes,registry=self.parent)))
		return NodeList([n for n in self.nodes if n.node not in nodes],self.parent)

	def info(self):

		"""
		Print all of the relationships in which this NodeList's nodes
		participate
		"""

		src = [(self.parent.registry[n.node],n.node) for n in self.nodes]
		for n in src:
			print('='*len(n[1].name))
			print(n[1].name)
			for k in n[0]:
				print("    | ",k,":",n[0][k].sort().format())

	def names(self):

		"""
		Returns an array containing the names of the nodes in this NodeList,
		sorted. Originally written only for testing.
		"""

		self.sort()
		return [n.node.name for n in self]

	def tuples(self):

		"""
		Returns an array containing plain tuples for each node in the NodeList,
		each tuple containing the node name and the weight. Originally written
		only for testing.
		"""

		self.sort()
		return [(n.node.name,n.weight) for n in self]

	def format(self,margin=4,maxwidth=80):
		return re.sub('\s*(.{%d}\s*[^,\]]+)[,\]]' % maxwidth,'\n'+(' '*margin)+'...   \\1',self.nodes.__str__())

class NodeTuple(object):
	"""
	Class representing a `node` and an integer `weight`.
	"""
	def __init__(self, node, weight):
		super(NodeTuple, self).__init__()
		enforceType(weight,int,'Tuple weight must be an integer ({0} was provided)')
		self.node = node
		self.weight = weight

	def __str__(self):
		return "{0} ({1})".format(self.node,self.weight)
	__repr__ = __str__

	def __eq__(self,other):
		return False if type(other) != NodeTuple else (other.node == self.node and other.weight == self.weight)

	def setWeight(self,value):
		self.weight = value

	def addWeight(self,value):
		self.weight += value


def tuplate(src,create=0,load=0,registry=None):

		"""
		Converts input list of node names or manually notated tuples to
		NodeTuples.

		`src` may be a list of (any combination of) strings, nodes, tuples and
			NodeTuples, or a single one of those

		Returns a list of NodeTuples (*not* a NodeList)
		"""

		src = enlist(src)

		def dereference(n):
			if registry:
				o = registry.get(n,create=create,load=load)
				return None if o.isEmpty() else o.nodes[0].node
			else:
				return None

		def p(n):
			if type(n) == str:
				o = dereference(n)
				return None if not o else NodeTuple(o,1)
			elif type(n) == Node:
				return NodeTuple(n,1)
			elif type(n) == tuple:
				o = n[0]
				if type(o) == str:
					o = dereference(o)
				return None if not o else NodeTuple(o,n[1])
			elif type(n) == NodeTuple:
				if type(n.node) == str:
					n.node = dereference(n.node)
				return None if not n.node else n
			elif type(n) == NodeList:
				return n
			else:
				return None

		return flatten(list(filter(lambda i: i!=None,list(map(p,src)))))

def flatten(arr):

	"""
	Flatten a list, works with all sequences (ie, variables with __iter__
		defined)

	Example: [1,2,[3,4],5,[6,7,[8]]] => [1,2,3,4,5,6,7,8]
	"""

	out = []
	for a in arr:
		if hasattr(a,'__iter__'):
			out += flatten(a)
		else:
			out.append(a)
	return out