from . import Supplier
from ..sources import MySource

import os

class MySupplier(Supplier):

	@classmethod
	def get_name(cls):
		""" Returns the name of the supplier.
		"""
		return 'mysupplier'

	def __init__(self, path, *args, **kwargs):
		super().__init__(*args, **kwargs)
		fnames = os.listdir(path)
		fnames = [os.path.join(path,x) for x in fnames]
		self.data = {'x':MySource(fnames=fnames,name='x'),
					 'y':MySource(fnames=fnames,name='y')}

	def get_sources(self, sources=None):
		""" Returns all sources from this provider.
		"""

		if sources is None:
			sources = list(self.data.keys())
		elif not isinstance(sources, (list, tuple)):
			sources = [sources]

		for source in sources:
			if source not in self.data:
				raise KeyError(
					'Invalid data key: {}. Valid keys are: {}'.format(
						source, ', '.join(str(k) for k in self.data.keys())
				))

		return {k : self.data[k] for k in sources}
