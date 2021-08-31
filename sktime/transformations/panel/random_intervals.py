# -*- coding: utf-8 -*-
"""Random interval features.

A transformer for the extraction of features on randomly selected intervals.
"""

__author__ = "Matthew Middlehurst"
__all__ = ["RandomIntervals"]

import numpy as np
import pandas as pd
from sklearn.utils import check_random_state

from sktime.base._base import _clone_estimator
from sktime.transformations.base import _PanelToTabularTransformer
from sktime.utils.validation.panel import check_X


class RandomIntervals(_PanelToTabularTransformer):
    """Random interval feature transformer.

    Overview:

    random intervals and clones transformers in fit
    transforms all intervals using all transformers and concatenates in transform
    """

    def __init__(
        self,
        n_intervals=100,
        transformers=None,
        random_state=None,
        n_jobs=1,
    ):
        self.n_intervals = n_intervals
        self.transformers = transformers

        self.random_state = random_state
        self.n_jobs = n_jobs

        self._transformers = transformers
        self._intervals = []
        self._dims = []

        super(RandomIntervals, self).__init__()

    def fit(self, X, y=None):
        """fits the random interval transform.

        Parameters
        ----------
        X : pandas DataFrame or 3d numpy array, input time series
        y : array_like, target values (optional, ignored)
        """
        _, n_dims, series_length = X.shape

        # if self._transformers is None:
        #     self._transformers = SummaryTransformer()

        if not isinstance(self._transformers, list):
            self._transformers = [self._transformers]

        for i in range(len(self._transformers)):
            self._transformers[i] = _clone_estimator(
                self._transformers[i],
                self.random_state,
            )

            m = getattr(self._transformers[i], "n_jobs", None)
            if callable(m):
                self._transformers[i].n_jobs = self.n_jobs

        rng = check_random_state(self.random_state)
        self._dims = rng.choice(n_dims, self.n_intervals, replace=True)
        self._intervals = np.zeros((self.n_intervals, 2), dtype=int)

        for i in range(0, self.n_intervals):
            if rng.random() < 0.5:
                self._intervals[i][0] = rng.randint(0, series_length - 3)
                length = (
                    rng.randint(0, series_length - self._intervals[i][0] - 3) + 3
                    if series_length - self._intervals[i][0] - 3 > 0
                    else 3
                )
                self._intervals[i][1] = self._intervals[i][0] + length
            else:
                self._intervals[i][1] = rng.randint(0, series_length - 3) + 3
                length = (
                    rng.randint(0, self._intervals[i][1] - 3) + 3
                    if self._intervals[i][1] - 3 > 0
                    else 3
                )
                self._intervals[i][0] = self._intervals[i][1] - length

        self._is_fitted = True
        return self

    def transform(self, X, y=None):
        """transforms data into random interval features.

        Parameters
        ----------
        X : pandas DataFrame or 3d numpy array, input time series
        y : array_like, target values (optional, ignored)

        Returns
        -------
        Pandas dataframe of random interval features.
        """
        self.check_is_fitted()
        X = check_X(X, coerce_to_numpy=True)

        X_t = []
        for i in range(0, self.n_intervals):
            for j in range(len(self._transformers)):
                t = self._transformers[j].fit_transform(
                    X[:, self._dims[i], self._intervals[i][0] : self._intervals[i][1]],
                    y,
                )

                if isinstance(t, pd.DataFrame):
                    t = t.to_numpy()

                if i == 0 and j == 0:
                    X_t = t
                else:
                    X_t = np.concatenate((X_t, t), axis=1)

        return pd.DataFrame(X_t)