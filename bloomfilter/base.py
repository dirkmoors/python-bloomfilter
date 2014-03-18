#!/usr/bin/env python
"""
base.py: Contains the bloomfilter class implementation
"""

import math
import base64
import json
import zlib
import struct
import hashlib

from bloomfilter.probegenerators import get_probegenerator
from bloomfilter.probegenerators.murmur import MurmurProbeGenerator

__author__ = 'Dirk Moors'
__copyright__ = 'Copyright 2014, Dirk Moors'
__version__ = "1.0.0"
__status__ = "Production"

def hash(bytes):
    m = hashlib.sha256()
    m.update(bytes)
    return m.hexdigest()

def longArrayToByteArray(longArray):
    fmt = '!%s'%('q'*len(longArray))
    return struct.pack(fmt, *longArray)

def byteArrayToLongArray(byteArray):
    fmt = '!%s'%('q'*(len(byteArray)/8))
    return [long(i) for i in struct.unpack(fmt, byteArray)]

class BloomFilter(object):
    VERSION = "1.0"
    def __init__(self, ideal_num_elements_n, error_rate_p, data=None, probegenerator=None):
        if ideal_num_elements_n <= 0:
            raise ValueError('ideal_num_elements_n must be > 0')
        if not (0 < error_rate_p < 1):
            raise ValueError('error_rate_p must be between 0 and 1 exclusive')

        self.error_rate_p = error_rate_p
        self.ideal_num_elements_n = ideal_num_elements_n

        self.num_bits_m = BloomFilter.calculateNumBitsM(self.ideal_num_elements_n, self.error_rate_p)
        self.num_probes_k = BloomFilter.calculateNumProbesK(self.ideal_num_elements_n, self.num_bits_m)

        self.num_words = BloomFilter.calculateNumWords(self.num_bits_m)

        self.probegenerator = probegenerator or MurmurProbeGenerator()

        self.data = data or [long(0) for _ in xrange(self.num_words)]

    def get_data(self):
        return self.data

    def get_nr_of_probes(self):
        return self.num_probes_k

    def get_nr_of_bits(self):
        return self.num_bits_m

    def add(self, key):
        probes = list(self.probegenerator.get_probes(self.num_probes_k, self.num_bits_m, key))
        for bitno in probes:
            wordno, bit_within_wordno = divmod(bitno, 32)
            mask = 1 << bit_within_wordno
            self.data[wordno] |= mask

    def match_template(self, bfilter):
        return (
            self.num_bits_m == bfilter.get_nr_of_bits() and
            self.num_probes_k == bfilter.get_nr_of_probes()
        )

    def union(self, bfilter):
        if self.match_template(bfilter):
            self.data = [a | b for a, b in zip(self.data, bfilter.get_data())]
        else:
            # Union b/w two unrelated bloom filter raises this
            raise ValueError("Mismatched bloom filters")

    def intersection(self, bfilter):
        if self.match_template(bfilter):
            self.data = [a & b for a, b in zip(self.data, bfilter.get_data())]
        else:
            # Intersection b/w two unrelated bloom filter raises this
            raise ValueError("Mismatched bloom filters")

    def toJSON(self, compress=True):
        data_bytes = longArrayToByteArray(self.data)

        datahash = hash(data_bytes)

        if compress:
            data_bytes = zlib.compress(data_bytes)

        b64data = base64.encodestring(data_bytes)

        result = {
            "v": BloomFilter.VERSION,
            "n": self.ideal_num_elements_n,
            "p": self.error_rate_p,
            "zlib": compress,
            "data": b64data,
            "hash": datahash,
            "gen": self.probegenerator.get_name()
        }
        return json.dumps(result)

    @classmethod
    def fromJSON(cls, json_bf):
        result = json.loads(json_bf)
        v = result.get("v", None)
        n = result.get("n", None)
        p = result.get("p", None)
        gen = result.get("gen", None)
        datahash = result.get("hash", None)
        compressed = result.get("zlib", None)
        b64data = result.get("data", None)

        if not v or not n or not p or not datahash or not b64data or not gen:
            raise ValueError("Invalid BloomFilter JSON structure")

        if v != BloomFilter.VERSION:
            raise ValueError("Incompatible BloomFilter version")

        rawdata = base64.decodestring(b64data)
        if compressed:
            rawdata = zlib.decompress(rawdata)

        if hash(rawdata) != datahash:
            raise ValueError("Data integrity error")

        probegenerator = get_probegenerator(gen)

        data = byteArrayToLongArray(rawdata)
        return BloomFilter(ideal_num_elements_n=n, error_rate_p=p, probegenerator=probegenerator, data=data)

    def __contains__(self, key):
        probes = list(self.probegenerator.get_probes(self.num_probes_k, self.num_bits_m, key))
        for bitno in probes:
            wordno, bit_within_wordno = divmod(bitno, 32)
            mask = 1 << bit_within_wordno
            c = self.data[wordno] & mask
            if not c:
                return False
        return True

    @staticmethod
    def calculateNumBitsM(n, p):
        numerator = -1 * n * math.log(p)
        denominator = math.log(2) ** 2
        real_num_bits_m = numerator / denominator
        return int(math.ceil(real_num_bits_m))

    @staticmethod
    def calculateNumProbesK(n, m):
        real_num_probes_k = (m / n) * math.log(2)
        return int(math.ceil(real_num_probes_k))

    @staticmethod
    def calculateNumWords(m):
        return (m + 31) // 32