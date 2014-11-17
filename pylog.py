# Pylog, Relational Intelligence Enging for Python
# ---
# Written by Alex Arendsen, released under the GNU GPLv2.
# Please do not claim ownership of it.

import sqlite3
import re

class Graph(object):
	"""An object representing a graph of nodes related in multiple dimensions"""
	def __init__(self):
		super(Graph, self).__init__()
		self.nodeReg = {}
		self.nodes = {}
		self.relations = []
		self.relationExpression = re.compile("rel\s+(`.+`)\s*(\<|\=)([a-z\s\=]+)(\>|\=)\s*(`.+`)\s*");
		self.dbc = None

	def createNode(self,name):
		out = NodeList([])
		if type(name) == list:
			return NodeList(flatten([self.createNode(n) for n in name]))
		elif type(name) == str:
			if name not in self.nodeReg:
				n = self.nodeReg[name] = Node(name,self)
				self.nodes[n] = {}
				return NodeList([n])
			else:
				return NodeList([self.nodeReg[name]])
		else:
			return NodeList([])

	def createRelation(self,name):
		self.relations.append(Relation(name));
		return self.relations[-1]

	# Get a single node from the graph by name
	def get(self,name,create=False,readCache=1):
		if type(name) == NodeList:
			return name
		elif type(name) == list:
			return NodeList(flatten([self.get(n,create=create,readCache=readCache) for n in name]))

		if name in self.nodeReg:
			return NodeList([self.nodeReg[name]])
		elif type(readCache) == int and readCache > -1 and self.dbc != None:
			return self.load(name,recursionDepth=readCache)
		else:
			if create == False:
				return NodeList([])
			else:
				return self.createNode(name)

	# Get relation from graph by name
	def getRelationByName(self, name):
		name = name.lower()
		for r in self.relations:
			if r.name == name:
				return r
		return None

	# Get all nodes associated with the relation by the given name
	def rel(self,name):
		return NodeList(self.getRelationByName(name).nodes);

	# Get relation from graph by name, creating one if it doesn't exist
	def createRelationByName(self, name):
		rel = self.getRelationByName(name)
		if rel == None:
			rel = self.createRelation(name)
		return rel

	# Alias for Graph.createRelationship, creates symmetric relationship
	# 	between 
	def createBijection(self,leftNames,rightNames,relation):
		return self.createRelationship(leftNames,rightNames,relation,relation)

	# Alias for Graph.createRelationship, creates one-way relationship between
	def createOneWay(self,leftNames,rightNames,relation):
		return self.createRelationship(leftNames,rightNames,relation,"");

	# Create a relationship between two list of nodes by name, creating any that
	#	don't exist. `rightToLeftRelation` denotes the relation the left has to
	#	the right; `leftToRightRelation` likewise
	#	Example: createRelationship("radiohead",["hail to the thief","ok computer","kid a"],"artists","albums")
	def createRelationship(self,leftNames,rightNames,leftToRightRelation,rightToLeftRelation):
		if type(leftNames) != list:
			leftNames = [leftNames]
		left = self.get(leftNames,create=True,readCache=-1)

		if type(rightNames) != list:
			rightNames = [rightNames]
		right = self.get(rightNames,create=True,readCache=-1)

		if rightToLeftRelation != "":
			leftRel = self.createRelationByName(rightToLeftRelation)
		else:
			leftRel = None

		if leftToRightRelation != "":
			rightRel = self.createRelationByName(leftToRightRelation)
		else:
			rightRel = None

		for r in right:
			if leftRel != None:
				leftRel.addNode(r)
			for l in left:
				if rightRel != None:
					rightRel.addNode(l)
					if rightRel not in self.nodes[r]:
						self.nodes[r][rightRel] = NodeList([])
					self.nodes[r][rightRel].append(l)
				if leftRel != None:
					if leftRel not in self.nodes[l]:
						self.nodes[l][leftRel] = NodeList([])
					self.nodes[l][leftRel].append(r)

	# Processes a query and applies to graph
	#	Examples:
	#		eval("node driftless pony club")
	#			Creates a node called "driftless pony club"
	#
	#		eval("relation albums")
	#			Creates a relation called "albums"
	#
	#		eval("rel `driftless pony club` <artists=albums> `magnificent`,`buckminster`")
	#			Creates relationships appropriate to express that 
	#			"dritfless pony club" has albums "magnificent" and
	#			"buckminster". All nodes and relations necessary are
	#			automatically created
	def eval(self,query):
		cmd = query.lower().split(' ')
		if len(cmd) == 0:
			return "(empty command)"
		elif cmd[0] == "node" and len(cmd) > 1:
			self.createNode(' '.join(cmd[1:]))
		elif cmd[0] == "relation" and len(cmd) > 1:
			self.createRelation(' '.join(cmd[1:]))
		elif cmd[0] == "rel":
			tkns = self.relationExpression.findall(query)[0]
			if len(tkns) == 5:
				rel = tkns[2].split('=')
				self.createRelationship(
					tkns[0].replace('`','').split(','),
					tkns[4].replace('`','').split(','),
					rel[0] if tkns[1] == "<" else "",
					rel[-1] if tkns[3] == ">" else ""
					)
			else:
				print("Syntax error:\n---");
				print(tkns);

	# -- Persistence methods

	# Connect to a SQLite Database, creates new Database if one with the given
	#	file name doesn't exist
	def connect(self,filename):
		if self.dbc != None:
			self.dbc.close()
		self.dbc = sqlite3.connect(filename)

		#self.initializeDB();

	# Initialize the connected database. Will remove all existing graph data
	def initializeDB(self):
		if input("Initialize the Database? (All graph data will be removed) ") == 'y':
			c = self.dbc.cursor()
			c.execute("DROP TABLE IF EXISTS NODES")
			c.execute("DROP TABLE IF EXISTS RELATIONS")
			c.execute("DROP TABLE IF EXISTS RELATIONSHIPS")
			c.execute("""
					CREATE TABLE NODES (
							ID INTEGER PRIMARY KEY,
							NAME TEXT
						)
				""")
			c.execute("""
					CREATE TABLE RELATIONS (
							ID INTEGER PRIMARY KEY,
							NAME TEXT
						)
				""")
			c.execute("""
					CREATE TABLE RELATIONSHIPS (
							NODELEFT INT,
							NODERIGHT INT,
							RELATION INT,
							FOREIGN KEY(NODELEFT) REFERENCES NODES(ID),
							FOREIGN KEY(NODERIGHT) REFERENCES NODES(ID),
							FOREIGN KEY(RELATION) REFERENCES RELATION(ID)
						)
				""")
			c.execute("""
					CREATE UNIQUE INDEX
						UNIQUENODE ON NODES(NAME)
				""")
			c.execute("""
					CREATE UNIQUE INDEX
						UNIQUERELATION ON RELATIONS(NAME)
				""")
			c.execute("""
					CREATE UNIQUE INDEX
						UNIQUERELATIONSHIP ON RELATIONSHIPS (
							NODELEFT,
							NODERIGHT,
							RELATION
						)
				""")
			self.dbc.commit()
			c.close()

	# Put all unstored graph data into the connected database.
	def dump(self):
		c = self.dbc.cursor()

		idx = c.execute("SELECT MAX(ID) FROM RELATIONS").fetchall()[0][0]
		if idx == None:
			idx = 1
		else:
			idx += 1

		for r in self.relations:
			if r.name[0] != "_":
				try:
					c.execute("INSERT INTO RELATIONS VALUES(?,?)",[idx,r.name])
					r._dbidx = idx
					idx += 1
				except sqlite3.IntegrityError:
					pass
		self.dbc.commit()

		idx = c.execute("SELECT MAX(ID) FROM NODES").fetchall()[0][0]
		if idx == None:
			idx = 1
		else:
			idx += 1

		for n in self.nodes:
			try:
				c.execute("INSERT INTO NODES VALUES(?,?)",[idx,n.name])
				n._dbidx = idx
				idx += 1
			except sqlite3.IntegrityError:
				n._dbidx = c.execute("SELECT ID FROM NODES WHERE NAME = ?",[n.name]).fetchall()[0][0]

		for n in self.nodes:
			for k in self.nodes[n]:
				if hasattr(k,"_dbidx"):
					for v in self.nodes[n][k]:
						try:
							c.execute("INSERT INTO RELATIONSHIPS VALUES(?,?,?)",[n._dbidx,v._dbidx,k._dbidx])
						except sqlite3.IntegrityError:
							pass
		self.dbc.commit()
		c.close()

	# Read graph data from database starting at node with the given name
	def load(self,name,recursionDepth=0):
		ex = self.get(name,readCache=-1)
		if ex.rel('_loaded').isEmpty():
			c = self.dbc.cursor()
			res = c.execute("SELECT ID FROM NODES WHERE NAME = ?",[name]).fetchall()
			if len(res) > 0:
				ex = self.createNode(name)
				rel = c.execute("""
						SELECT
							LFT.NAME,
							RGT.NAME,
							R.NAME
						FROM
							RELATIONSHIPS K,
							NODES LFT,
							NODES RGT,
							RELATIONS R
						WHERE
							LFT.ID = K.NODELEFT
							AND RGT.ID = K.NODERIGHT
							AND R.ID = K.RELATION
							AND (
								LFT.ID = ?
								OR RGT.ID = ?
							)
					""",[res[0][0],res[0][0]]).fetchall()
				self.createOneWay(ex,"_loaded","true")
				agenda = []
				for tup in rel:
					l = self.get(tup[0],create=True,readCache=-1)
					if l.rel('_loaded').isEmpty():
						self.createOneWay(tup[1],l,tup[2])
						if tup[0] == name and recursionDepth > 0:
							agenda.append(tup[1])

				if recursionDepth > 0:
					for a in agenda:
						self.load(a,recursionDepth=recursionDepth-1)
		return ex


class Node(object):
	"""A node in the graph"""
	def __init__(self, name, parent):
		super(Node, self).__init__()
		self.name = name
		self.relationships = {}
		self.parent = parent

	def __str__(self):
		return self.name;

	def __repr__(self):
		return self.name;

	# Get NodeList of all nodes related to this node by the relation with
	#	the given name
	def rel(self,relation):
		relation = self.parent.getRelationByName(relation)
		s = self.parent.nodes[self]
		if relation in s:
			return NodeList(self.parent.nodes[self][relation])
		else:
			return NodeList([])

	# Alias for Node.rel
	def getRelatedNodes(self,relation):
		return self.rel(relation);

	# Display dictionary of this node's related nodes
	def info(self):
		return self.parent.nodes[self]


class NodeList(object):
	"""Wrapper class for list of nodes"""
	def __init__(self,nodes):
		super(NodeList, self).__init__()
		if type(nodes) == NodeList:
			self.nodes = nodes.nodes
		elif type(nodes) != list:
			print("ERROR: NodeList construction with incompatible type {0}".format(type(nodes)));
		else:
			self.nodes = nodes
	
	def __repr__(self):
		return ', '.join([n.name for n in self.nodes])

	def __str__(self):
		return self.__repr__();

	def __iter__(self):
		for n in self.nodes:
			yield n

	def append(self,node):
		self.nodes.append(node)

	def remove(self,node):
		self.nodes.remove(node)

	def isEmpty(self):
		return len(self.nodes) == 0

	# Applies `rel` for all contained nodes,
	def rel(self,name):
		acc = flatten([n.rel(name) for n in self.nodes])
		return NodeList(acc)

	# Gets the node at the given index
	def eq(self,index):
		return self.nodes[index];

	# Returns only nodes with the given name
	def filterByName(self,name):
		return NodeList([n for n in self.nodes if n.name == name])

	# Removes all nodes not included in the NodeList `includes`
	def limit(self,includes):
		return NodeList([n for n in self.nodes if n in includes.nodes])

	# Removes all nodes included in the NodeList `excludes`
	def exclude(self,excludes):
		return NodeList([n for n in self.nodes if n not in excludes.nodes])

	# Merges this NodeList with NodeList `includes`
	def merge(self,includes):
		return NodeList(flatten([self.nodes,includes.nodes]))

	# Applies `info` to all contained nodes
	def info(self):
		return [n.info() for n in self.nodes]

class Relation(object):
	"""An object describing the way nodes in the graph may relate"""
	def __init__(self, name):
		super(Relation, self).__init__()
		self.name = name
		self.nodes = []

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name

	def addNode(self,node):
		if node not in self.nodes:
			self.nodes.append(node)

	def getNodeNames(self):
		return [n.name for n in self.nodes]

# Read queries line-by-line from source file. Each line in
#	file is fed to Graph.eval
def readSource(filename):
	g = Graph()
	for l in open(filename).readlines():
		g.eval(l)
	return g

# Flattens a list (e.g. [1,2,[3,4],5,[6,[7,8]]] => [1,2,3,4,5,6,7,8])
# Returned list will have unique elements ordered by frequency of appearance
def flatten(lst):
	return sortByFrequency(_flatten(lst,[]))

# Helper for flatten function
def _flatten(lst,out):
	for i in lst:
		if type(i) == list:
			_flatten(i,out)
		elif type(i) == NodeList or type(i) == Relation:
			_flatten(i.nodes,out)
		else:
			out.append(i)
	return out

def sortByFrequency(lst):
	out = {}
	for i in lst:
		if i not in out:
			out[i] = 0
		out[i]+=1
	return sorted(out,key=out.get,reverse=True)
