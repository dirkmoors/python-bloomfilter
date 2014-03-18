#!/usr/bin/env python
"""
Foobar.py: Description of what foobar does.
"""

from bloomfilter.probegenerators import BloomFilterProbeGenerator

__author__ = 'Dirk Moors'
__copyright__ = 'Copyright 2014, Dirk Moors'
__version__ = "1.0.0"
__status__ = "Production"

class MersenneProbeGenerator(BloomFilterProbeGenerator):
    NAME = "MERSENNE"

    #http://en.wikipedia.org/wiki/Mersenne_prime
    MERSENNE1 = [2 ** x - 1 for x in [17, 31, 127]]
    MERSENNE2 = [2 ** x - 1 for x in [19, 67, 257]]

    def get_probes(self, num_probes_k, num_bits_m, key):
        '''Apply num_probes_k hash functions to key.  Generate the array index and bitmask corresponding to each result'''
        int_list = [ord(char) for char in key]

        m1 = MersenneProbeGenerator.MERSENNE1
        m2 = MersenneProbeGenerator.MERSENNE2

        hash_value1 = MersenneProbeGenerator.hash1(int_list)
        hash_value2 = MersenneProbeGenerator.hash2(int_list)

        # We're using linear combinations of hash_value1 and hash_value2 to obtain num_probes_k hash functions
        for probeno in range(1, num_probes_k + 1):
            bit_index = hash_value1 + (probeno * hash_value2)
            yield bit_index % num_bits_m

    def get_name(self):
        return MersenneProbeGenerator.NAME

    @staticmethod
    def simple_hash(int_list, prime1, prime2, prime3):
        '''Compute a hash value from a list of integers and 3 primes'''
        result = 0
        for integer in int_list:
            result += ((result + integer + prime1) * prime2) % prime3
        return result

    @staticmethod
    def hash1(int_list):
        '''Basic hash function #1'''
        return MersenneProbeGenerator.simple_hash(int_list,
                                MersenneProbeGenerator.MERSENNE1[0],
                                MersenneProbeGenerator.MERSENNE1[1],
                                MersenneProbeGenerator.MERSENNE1[2])

    @staticmethod
    def hash2(int_list):
        '''Basic hash function #2'''
        return MersenneProbeGenerator.simple_hash(int_list,
                                MersenneProbeGenerator.MERSENNE2[0],
                                MersenneProbeGenerator.MERSENNE2[1],
                                MersenneProbeGenerator.MERSENNE2[2])
