from graph import *
import re

class Reader(object):
	"""
	Interpreter for AI source data in original notation
	"""
	def __init__(self, registry):
		super(Reader, self).__init__()
		self.registry = registry
		self.relExp = re.compile("(`.+`(?:\*\d+)?)\s+(<|\=)(.+)(\=|>)\s+(`.+`(?:\*\d+)?)")
		self.nodeExp = re.compile("`([^`]+)`(?:\*(\d+))?")
		
	def eval(self,exp):
		exp = exp.split(" ")
		if exp[0] == 'node':
			self.registry.add(' '.join(exp[1:]))
		elif exp[0] == 'rel':
			tkns = self.relExp.findall(' '.join(exp[1:]))[0]
			if len(tkns) == 5:
				rel = tkns[2].split('=')
				self.registry.relate(
					[(n[0],(int)(n[1] or 1)) for n in self.nodeExp.findall(tkns[0])],
					[(n[0],(int)(n[1] or 1)) for n in self.nodeExp.findall(tkns[4])],
					"" if tkns[1] != "<" else rel[0],
					"" if tkns[3] != ">" else rel[-1]
				)

	def read(self,filename):
		f = open(filename,'r')
		for l in f:
			self.eval(l)
		f.close()