#!/usr/bin/env python
"""
rng.py: Contains a BloomFilterProbeGenerator implementation based on Random Number Generator
"""

import random

from bloomfilter.probegenerators import BloomFilterProbeGenerator

__author__ = 'Dirk Moors'
__copyright__ = 'Copyright 2014, Dirk Moors'
__version__ = "1.0.0"
__status__ = "Production"

class RandomProbeGenerator(BloomFilterProbeGenerator):
    NAME = "NAME"

    def get_probes(self, num_probes_k, num_bits_m, key):
        hasher = random.Random(key).randrange
        for dummy in range(num_probes_k):
            bitno = hasher(num_bits_m)
            yield bitno % num_bits_m

    def get_name(self):
        return RandomProbeGenerator.NAME
