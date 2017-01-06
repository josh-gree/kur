"""
Copyright 2016 Deepgram

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
import tqdm
import numpy
from ..utils import get_any_value

logger = logging.getLogger(__name__)

###############################################################################
class Evaluator:
	""" Class for using trained models to predict new outputs.
	"""

	###########################################################################
	def __init__(self, model):
		""" Creates a new evaluator.

			# Arguments

			model: Model instance. The model to evaluate.
		"""
		self.model = model
		self._compiled = None

	###########################################################################
	def compile(self, recompile=False, with_provider=None):
		""" Compiles a model.

			This generates a backend-specific representation of the model,
			suitable for prediction.

			# Arguments

			recompile: bool (default: False). If the model has already been
				compiled, it is not compiled again unless this flag is True.
			with_provider: Provider instance or None (default: None). If you
				want to merge the model's auxiliary data sources into your
				provider, you can specify the Provider instance here.

			# Return value

			None
		"""

		if self._compiled is not None and not recompile:
			return

		if not self.model.is_built():
			logger.warning('This model has never been built before. We are '
				'going to try to build it now. But the model should always be '
				'built with Model.build() before trying to compile it, just '
				'to ensure that everything has been parsed as you expect.')
			if with_provider is not None:
				self.model.register_provider(with_provider)
			self.model.build()

		self._compiled = self.model.backend.compile(
			model=self.model
		)

		if with_provider is not None:
			for name, source in self.model.get_data_sources():
				with_provider.add_source(source, name=name)

	###########################################################################
	def evaluate(self, provider, callback=None):
		""" Evaluates the model on some data.

			# Arguments

			provider: Provider instance. The data provider which serves the
				data to be evaluated.
			callback: function or None. If not None, the callback is called
				after each evaluation batch and is passed two parameters:
				`predicted` and `truth`, where `predicted` is the model output
				and `truth` is the ground truth data (if provided by
				`provider`; otherwise, `truth` is set to `None`).

			# Return value

			If `callback` is None, then this returns a tuple `(predicted,
			truth)`, where `predicted` is a dictionary whose keys are the names
			of the output nodes of the model, and whose respective values are
			arrays of predictions (one row per input sample). If the provider
			provides ground truth information, then `truth` has a similar
			structure to `predicted`; if ground truth information is not
			available, then `truth` is None.

			Otherwise, if `callback` is not None, this returns None.
		"""

		self.compile(with_provider=provider)

		result = None
		truth = None
		has_truth = None
		total = len(provider)
		n_entries = 0

		with tqdm.tqdm(
					total=total,
					unit='samples',
					desc='Evaluating'
				) as pbar:

			for batch in provider:
				evaluated = self.model.backend.evaluate(
					model=self.model,
					data=batch,
					compiled=self._compiled
				)
				batch_size = len(get_any_value(batch))

				if has_truth is None:
					has_truth = all(k in batch for k in self.model.outputs)

				if callback is None:
					# There is no callback. We need to hang on to everything.
					if total is None:
						# We don't know how many entries there will be.
						if result is None:
							# This is our first batch.
							result = {k : [] for k in self.model.outputs}
						for k, v in evaluated.items():
							result[k].extend(v)

						if has_truth:
							if truth is None:
								truth = {k : [] for k in self.model.outputs}
							for k in truth:
								truth[k].extend(batch[k])
					else:
						# We know how many entries there will be.
						if result is None:
							# This is our first batch.
							result = {k : [None]*total for k in evaluated}
						for k, v in evaluated.items():
							result[k][n_entries:(n_entries+batch_size)] = v[:]

						if has_truth:
							if truth is None:
								truth = {k : [None]*total for k in evaluated}
							for k in truth:
								truth[k][n_entries:(n_entries+batch_size)] = \
									batch[k][:]
				else:
					callback(evaluated, truth)

				n_entries += batch_size
				pbar.update(batch_size)

		if callback is not None:
			return

		if total is None:
			for k, v in result.items():
				result[k] = numpy.concatenate(v)
			for k, v in truth.items():
				truth[k] = numpy.concatenate(v)

		return result, truth

### EOF.EOF.EOF.EOF.EOF.EOF.EOF.EOF.EOF.EOF.EOF.EOF.EOF.EOF.EOF.EOF.EOF.EOF.EOF
