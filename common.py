import re

def enforceType(var,typ,message=None):
	typ = enlist(typ)
	if type(var) not in typ:
		raise Exception((message or '{0}: Invalid type (expected {1})').format(type(var),typ))

def enlist(var):
	return var if type(var) == list else [var]

def coerceType(var,typ,default):
	typ = enlist(typ)
	return var if type(var) in typ else default