#!/usr/bin/env python
"""
Foobar.py: Description of what foobar does.
"""

__author__ = 'Dirk Moors'
__copyright__ = 'Copyright 2014, Dirk Moors'
__version__ = "1.0.0"
__status__ = "Production"

def get_probegenerator(name):
    from bloomfilter.probegenerators.rng import RandomProbeGenerator
    from bloomfilter.probegenerators.mersenne import MersenneProbeGenerator

    if name == RandomProbeGenerator.NAME:
        return RandomProbeGenerator()
    elif name == MersenneProbeGenerator.NAME:
        return MersenneProbeGenerator()
    raise ValueError("Unsupported probegenerator: %s"%name)

class BloomFilterProbeGenerator(object):
    def get_probes(self, num_probes_k, num_bits_m, key):
        raise NotImplementedError("Should be implemented in subclass")

    def get_name(self):
        raise NotImplementedError("Should be implemented in subclass")