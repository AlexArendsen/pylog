import sqlite3
from common import *

class DBC(object):
	"""docstring for DBC"""
	def __init__(self, registry):
		super(DBC, self).__init__()
		self.registry = registry
		self.connection = None
		
	def connect(self,filename):
		"""
		Connect to a SQLite Database, creates new Database if one with the given
			file name doesn't exist
		"""
		if self.connection:
			self.connection.close()
		self.connection = sqlite3.connect(filename)

		if not self.isInitialized():
			self.initialize(imsure=True)

	def isInitialized(self):
		c = self.connection.cursor()
		return c.execute("SELECT COUNT(1) FROM sqlite_master WHERE type='table' AND name IN ('NODES','RELATIONSHIPS')").fetchall()[0][0]

	def isConnected(self):
		return type(self.connection) == sqlite3.Connection;

	def initialize(self,imsure=False):

		"""
		Initialize the connected database. Will remove all existing graph data:
		only tables NODES and RELATIONSHIP will be dropped and recreated. They
		will not be populated.

		`imsure` will override the terminal confirmation prompt that is
		otherwise presented before initializing the database if it is True
		"""
		if imsure or input("Are you sure you want to initialize? This will remove all existing graph data from the database:") == 'y':
			c = self.connection.cursor()
			c.execute("DROP TABLE IF EXISTS NODES")
			c.execute("DROP TABLE IF EXISTS RELATIONSHIPS")
			c.execute("""
					CREATE TABLE NODES (
							ID INTEGER PRIMARY KEY,
							NAME TEXT
						)
				""")
			c.execute("""
					CREATE TABLE RELATIONSHIPS (
							NODELEFT INT,
							NODERIGHT INT,
							RELATION INT,
							WEIGHT INT,
							FOREIGN KEY(NODELEFT) REFERENCES NODES(ID),
							FOREIGN KEY(NODERIGHT) REFERENCES NODES(ID),
							FOREIGN KEY(RELATION) REFERENCES NODES(ID)
						)
				""")
			c.execute("""
					CREATE UNIQUE INDEX
						UNIQUENODE ON NODES(NAME)
				""")
			c.execute("""
					CREATE UNIQUE INDEX
						UNIQUERELATIONSHIP ON RELATIONSHIPS (
							NODELEFT,
							NODERIGHT,
							RELATION
						)
				""")
			self.connection.commit()
			c.close()

	def dump(self):

		"""
		Put all unstored graph data into the connected database.
		"""

		c = self.connection.cursor()

		# Get next node numeric ID
		idx = (c.execute("SELECT MAX(ID) FROM NODES").fetchall()[0][0] or 0) + 1

		# Insert all nodes into DB
		for name,node in self.registry.lookup.items():
			try:
				c.execute("INSERT INTO NODES VALUES(?,?)",[idx,name])
				node._dbidx = idx
				idx += 1
			except sqlite3.IntegrityError:
				# Node already exists
				node._dbidx = c.execute("SELECT ID FROM NODES WHERE NAME = ?",[name]).fetchall()[0][0]

		# Create all relationships
		for node,info in self.registry.registry.items():

			# Iteratre over each node's relations, skipping over private ones
			#	(those starting with an underscore)
			for relation,relatives in info.items():
				
				if hasattr(relation,"_dbidx"):
					if relation.name[0] != '_':
						for relative in relatives:
							try:
								c.execute("INSERT INTO RELATIONSHIPS VALUES(?,?,?,?)",[node._dbidx,relative.node._dbidx,relation._dbidx,relative.weight])
							except sqlite3.IntegrityError as e:
								# Relationship is already in database
								pass
				else:
					# Should never happen, but leaving it here just in case
					print("[WARN] {0}: Relation ID not found".format(relation.node.name))

		self.connection.commit()
		c.close()

	def load(self,name):

		"""
		Read graph data from database starting at node with the given name.

		`name` must be a string name or a list of string names
		"""

		name = enlist(name)

		# Get names of unloaded / non-existent nodes matching input name(s)
		nex = [n for n in name if not self.registry.get(n,load=0).isLoaded()]

		if len(nex):

			c = self.connection.cursor()

			# Query DB to get list of IDs for each node in the existing list `nex`
			nameMask = ','.join('?'*len(nex))
			res = [(str)(r[0]) for r in c.execute("SELECT ID FROM NODES WHERE NAME IN (%s)" % nameMask,nex).fetchall()]

			if len(res):

				# Get all relationships in which the existing nodes participate
				rel = c.execute("""
						SELECT
							LFT.NAME,
							RGT.NAME,
							R.NAME,
							K.WEIGHT
						FROM
							RELATIONSHIPS K,
							NODES LFT,
							NODES RGT,
							NODES R
						WHERE
							LFT.ID = K.NODELEFT
							AND RGT.ID = K.NODERIGHT
							AND R.ID = K.RELATION
							AND LFT.ID IN (%s)
					""" % (nameMask),res).fetchall()

				# Load the relationships into the graph
				for tup in rel:
					self.registry.relate((tup[1],tup[3]),tup[0],tup[2],"")

				# After all the loading is done, set all input nodes to loaded
				self.registry.get(name,load=0).setLoaded(True)
		return self.registry.get(name,load=0)
	
	def convert(self,filename):

		"""
		Converts old an Pylog SQLite database with the given `filename` to new
		format.
		"""

		if input("""
	--- Are you sure? {0} will be directly modified.

	This action will convert '{0}' to the new supported format and cannot
	be directly reversed. Once the conversion is complete, '{0}' will not
	be readable by earlier versions of this program.

	Continue? [y/N]
			""".format(filename)).lower() != 'y':
			print("--- Conversion aborted")
			return None

		print("Converting {0}...".format(filename))
		conn = sqlite3.connect(filename)

		c = conn.cursor()

		print("Adding weight column to Relationships table...")
		try:
			c.execute("ALTER TABLE RELATIONSHIPS ADD COLUMN WEIGHT INT DEFAULT 1")
		except sqlite3.OperationalError:
			print("--- Weight column already exists.")

		print("Converting relations...")
		if c.execute("SELECT COUNT(1) FROM sqlite_master WHERE type='table' AND name = 'RELATIONS'").fetchall()[0][0]:
			res = c.execute("""
				SELECT
					ID,
					NAME
				FROM
					RELATIONS
				""").fetchall()

			idx = c.execute("""
				SELECT
					MAX(ID)
				FROM
					NODES
				""").fetchall()[0][0]

			tidx = 0

			print("Changing {0} relations into nodes, reworking relationships...".format(len(res)))
			for r in res:
				idx += 1
				try:
					c.execute("""
						INSERT INTO NODES VALUES(?,?)
						""",[idx,r[1]])
				except sqlite3.IntegrityError:
					tidx = c.execute("""
						SELECT ID FROM NODES WHERE NAME = ?
						""",[r[1]]).fetchall()[0][0]
					idx -= 1


				c.execute("""
					UPDATE
						RELATIONSHIPS
					SET
						RELATION = ?
					WHERE
						RELATION = ?
					""",[tidx or idx,r[0]])
				tidx = 0

			print("Dropping relations table...")
			c.execute("DROP TABLE RELATIONS")
		else:
			print("--- Relation table missing; no relations to convert.")

		conn.commit()
		c.close()

		print("Conversion complete!")