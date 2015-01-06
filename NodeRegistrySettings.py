

class NodeRegistrySettings(object):

	"""docstring for NodeRegistrySettings"""

	def __init__(self):
		super(NodeRegistrySettings, self).__init__()

		# If True, relating the same two nodes more than once will successfully
		# add weight to their relationship. If False, nodes may only be related
		# once; further attempts to relate the same two nodes will have no
		# effect.
		self.ACCUMULATE_RELATIONSHIPS = True

		# If True, nodes acting as relations in a node relationship will be
		# automatically associated with the right-hand nodes with the internal
		# '_connects' relation. This enables the Graph.rel() method to work,
		# but introduces considerable memory overhead as well that is avoided
		# by disabling the setting. It is recommended that if the Graph.rel()
		# is not needed that this setting be set to False.
		self.MANAGE_CONNECTIONS = True