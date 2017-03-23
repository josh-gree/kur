from . import ChunkSource
from numpy.random import permutation

import numpy as np
import h5py

class MySource(ChunkSource):

	@classmethod
	def default_chunk_size(cls):
		""" Returns the default chunk size for this source.
		"""
		return ChunkSource.USE_BATCH_SIZE

	def __init__(self, fnames,name, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fnames = fnames
		self.name = name

	def shape(self):
		return (256,256,1)

	def __len__(self):
		return len(self.fnames)

	def shuffle(self, indices):
		self.fnames = [self.fnames[i] for i in indices]

	def can_shuffle(self):
		""" This source can be shuffled.
		"""
		return True

	def __iter__(self):
		start = 0
		num_entries = len(self)
		while start < num_entries:
			end = min(num_entries, start + self.chunk_size)
			chunk_fnames = self.fnames[start:end]
			out = np.zeros((self.chunk_size,) + self.shape())
			for ind,name in enumerate(chunk_fnames):
				f = h5py.File(name, "r")
				out[ind,...] = f[self.name]
				f.close()
			yield out
			start = end
