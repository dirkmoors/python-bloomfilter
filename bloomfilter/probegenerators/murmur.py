#!/usr/bin/env python
"""
murmur.py: Contains a BloomFilterProbeGenerator implementation based on Murmur hash:
http://en.wikipedia.org/wiki/MurmurHash
"""

import math
from bloomfilter.probegenerators import BloomFilterProbeGenerator
from bloomfilter.tools import enforce_int_overflow, unsigned_right_shift, MIN_INT

__author__ = 'Dirk Moors'
__copyright__ = 'Copyright 2014, Dirk Moors'
__version__ = "1.0.0"
__status__ = "Production"

class MurmurProbeGenerator(BloomFilterProbeGenerator):
    NAME = "MURMUR"
    SEED32 = 89478583

    def get_probes(self, num_probes_k, num_bits_m, key):
        value = bytearray(key)

        positions = [int(0) for _ in xrange(num_probes_k)]

        hashes = int(0)

        data = bytearray(len(value))
        data[:] = value #Copies the entire bytearray

        while hashes < num_probes_k:
            for i in xrange(len(value)):
                if data[i] == 127:
                    data[i] = 0
                    continue
                else:
                    data[i] += 1
                    break

            m = int(0x5bd1e995)
            r = int(24)

            data_len = int(len(data))
            h = int(MurmurProbeGenerator.SEED32 ^ data_len)

            i = 0
            while data_len >= 4:
                k = data[i + 0] & 0xFF
                k |= (data[i + 1] & 0xFF) << 8
                k |= (data[i + 2] & 0xFF) << 16
                k |= (data[i + 3] & 0xFF) << 24

                k *= m
                k = enforce_int_overflow(k)
                msk = unsigned_right_shift(k, r)
                k ^= msk
                k = enforce_int_overflow(k)
                k *= m
                k = enforce_int_overflow(k)

                h *= m
                h = enforce_int_overflow(h)
                h ^= k
                h = enforce_int_overflow(h)

                i += 4
                data_len -= 4

            if data_len == 3:
                h ^= (data[i + 2] & 0xFF) << 16
            if data_len >= 2:
                h ^= (data[i + 1] & 0xFF) << 8
            if data_len >= 1:
                h ^= (data[i + 0] & 0xFF)
                h *= m

            h = enforce_int_overflow(h)

            h ^= unsigned_right_shift(h, 13)
            h = enforce_int_overflow(h)

            h *= m
            h = enforce_int_overflow(h)

            h ^= unsigned_right_shift(h, 15)
            h = enforce_int_overflow(h)

            lastHash = enforce_int_overflow(MurmurProbeGenerator.rejection_sample(h, num_bits_m))
            if lastHash != -1:
                positions[hashes] = lastHash
                hashes += 1

        return positions

    def get_name(self):
        return MurmurProbeGenerator.NAME

    @staticmethod
    def rejection_sample(rand, num_bits_m):
        rand = int(math.fabs(rand))
        rand = enforce_int_overflow(rand)
        if rand > (2147483647 - 2147483647 % num_bits_m) or rand == MIN_INT:
            return -1
        return rand % num_bits_m
