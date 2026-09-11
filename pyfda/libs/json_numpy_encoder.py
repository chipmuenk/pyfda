# -*- coding: utf-8 -*-
#
# This file is part of the pyfda project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyfda Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
JSON encoder for 
"""
import json
import logging

import numpy as np
from numpy.typing import NDArray

logger = logging.getLogger(__name__)

class JSONNumpyEncoder(json.JSONEncoder):
    """
    Special json encoder for numpy and other non-supported types, building upon
    https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable
    """
    def default(self, obj: int | float | complex | NDArray) \
        -> int | float | str | list:
        logger.warning("JSONNumpyEncoder")
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, complex):
            if obj.imag < 0:
                return str(obj.real) + str(obj.imag) + "j"
            return str(obj.real) + "+" + str(obj.imag) + "j"
        if callable(obj):
            logger.warning("Object '%s' not JSON serializable as it is a function.", obj)
            return ""

        try:
            # The following only raises a TypeError which is caught in the next step
            return json.JSONEncoder.default(self, obj)
        except TypeError as e:
            logger.warning(
                "Object of type '%s' is not JSON serializable.\n%s", type(obj), e)
            return ""
