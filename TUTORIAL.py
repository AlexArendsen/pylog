# First, import Pylog
from pylog import *

# --- Populating graph

# Populating a graph may be done programmatically (discussed in a later section)
#	or through source file. For most of the tutorial, the `friends.txt` example
#	source file will be used.
#
#	Alice, Bob, Chuck, Dan, Eve, Frank, Gloria, and Henrietta are all people.
#	`friends.txt` expresses the way they all relate, as well as some additional
#	information about who they follow on Twitter, what genre of music they like,
#	and which artists are part of those genres. Examine `friends.txt` before
#	continuing.

g = readSource('examples/friends.txt')


# --- Graph traversal

# To select a node from the graph by name, use the Graph.get() method:
g.get('alice')

# To view information about a node, use the Node.info() method:
g.get('alice').info()
#	output: {enemies: chuck, friends: frank, eve, follows: frank, eve, music preference: indie}

# Use the Node.rel() method to get nodes associated to the node by a given relation
#	This example returns all of Alice's friends:
g.get('alice').rel('friends')
#	output: frank, eve

# The rel() method also works on collections of nodes, allowing you to chain
#	invocations of it together. The following example gets all of Alice's
# 	"friends of friends":
g.get('alice').rel('friends').rel('friends')
#	output: alice, gloria, chuck

# Another example: Get all the friends of Alice's enemies:
g.get('alice').rel('enemies').rel('friends')
#	output: frank, dan

# Another example, using the additional data: Chuck likes both metal and EDM.
#	This statement will get all of the music artists that he may like:
g.get('chuck').rel('music preference').rel('artists')
#	output: drop tower, dream theater, pantera, opeth, anamanaguchi

# The graph object also has a `rel()` method, it returns all nodes associated
#	with the given relation. Example: find all of the registered genres
g.rel('genres')
#	output: indie, metal, edm, country, pop


# --- Set arithmetic

# Collections of ndoes may be filtered using boolean arithmetic methods:
# NodeList.limit(), NodeList.merge(), and NodeList.exclude()

# Merged collections: Get all of both Alice's and Dan's friends in one collection:
g.get('dan').rel('friends').merge(g.get('alice').rel('friends'))
#	output: eve, chuck, frank

# Collection exclusion: get Alice's friends of friends, except for those
#	who are also enemies of Alice
g.get('alice').rel('friends').rel('friends').exclude(g.get('alice').rel('enemies'))
#	output: alice, gloria

# Alice is putting together a playlist for a party she will be throwing for
#	all of her Twitter friends and wants to know what they might like to
#	listen to:
g.get('alice')\
	.rel('follows')\
	.limit(g.get('alice').rel('friends'))\
	.rel('music preference')\
	.rel('artists')
#	output: rhianna, bruno mars, justin bieber, drop tower, anamanaguchi

# Find what pop music fans follow on Twitter, excluding individual people
g.get('pop').rel('fans').rel('follows').exclude(g.rel('friends'))
#	output: dreamworks, disney animation


# --- Programmatic graph population

g = Graph()

# In addition to using a source file to populate the graph, Pylog also
#	allows graphs to be populated programmatically. No special setup is 
#	necessary to use these functions; all necessary nodes and relations are
#	created automatically.

# Use `createBijection` to establish a symmetric relationship.
#	(Example: Arin is friends with both Ross and Danny, AND Ross and
#	Danny are friends with Arin. The statement does not establish
#	that Ross and Danny are friends, though)
g.createBijection("arin",["ross","danny"],"friends")

# Use `createOneWay` to establish a directional relationship.
# 	(Example: both Danny and Suzy follow Ross on Twitter. The statement
#	does not establish that Ross follows Danny or Suzy back, though)
g.createOneWay(["danny","suzy"],"ross","follows")

# Use `createRelationship` to establish a mutual relationship with asymmetrical
# denotations
#	(Example: Arin, Ross, Danny, and Barry are all "members" of the "Game Grumps"
#	group. In turn, "Game Grumps" is one of each of their "groups")
g.createRelationship("game grumps",["arin","ross","danny","barry"],"groups","members")

# Additionally, the `eval` method can be used to evaluate strings as they would
# appear as lines in a source file (like `friends.txt`)
