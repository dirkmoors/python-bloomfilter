#!/usr/bin/env python
"""
bloomfilter.py: A pure python implementation of a bloom filter

sources:
http://code.activestate.com/recipes/577686-bloom-filter/
http://stromberg.dnsalias.org/svn/bloom-filter/trunk/bloom_filter_mod.py

Modified by Dirk Moors
"""

import math
import random
import base64
import json
import zlib
import struct

def longArrayToByteArray(longArray):
    fmt = '!%s'%('q'*len(longArray))
    return struct.pack(fmt, *longArray)

def byteArrayToLongArray(byteArray):
    fmt = '!%s'%('q'*(len(byteArray)/8))
    return [long(i) for i in struct.unpack(fmt, byteArray)]

def assertListEquals(l1, l2):
    assert len(l1) == len(l2)
    for i in xrange(len(l1)):
        assert l1[i] == l2[i]

class BloomFilterProbeGenerator(object):
    def get_probes(self, num_probes_k, num_bits_m, key):
        raise NotImplementedError("Should be implemented in subclass")

class RandomProbeGenerator(BloomFilterProbeGenerator):
    def get_probes(self, num_probes_k, num_bits_m, key):
        hasher = random.Random(key).randrange
        for dummy in range(num_probes_k):
            bitno = hasher(num_bits_m)
            yield bitno % num_bits_m

class MersennesProbeGenerator(BloomFilterProbeGenerator):
    MERSENNES1 = [2 ** x - 1 for x in [17, 31, 127]]
    MERSENNES2 = [2 ** x - 1 for x in [19, 67, 257]]

    def get_probes(self, num_probes_k, num_bits_m, key):
        '''Apply num_probes_k hash functions to key.  Generate the array index and bitmask corresponding to each result'''

        # This one assumes key is either bytes or str (or other list of integers)

        # I'd love to check for long too, but that doesn't exist in 3.2, and 2.5 doesn't have the numbers.Integral base type
        if hasattr(key, '__divmod__'):
            int_list = []
            temp = key
            while temp:
                quotient, remainder = divmod(temp, 256)
                int_list.append(remainder)
                temp = quotient
        elif hasattr(key[0], '__divmod__'):
            int_list = key
        elif isinstance(key[0], str):
            int_list = [ord(char) for char in key]
        else:
            raise TypeError('Sorry, I do not know how to hash this type')

        hash_value1 = self.hash1(int_list)
        hash_value2 = self.hash2(int_list)

        # We're using linear combinations of hash_value1 and hash_value2 to obtain num_probes_k hash functions
        for probeno in range(1, num_probes_k + 1):
            bit_index = hash_value1 + probeno * hash_value2
            yield bit_index % num_bits_m

    def simple_hash(self, int_list, prime1, prime2, prime3):
        '''Compute a hash value from a list of integers and 3 primes'''
        result = 0
        for integer in int_list:
            result += ((result + integer + prime1) * prime2) % prime3
        return result

    def hash1(self, int_list):
        '''Basic hash function #1'''
        return self.simple_hash(int_list,
                                MersennesProbeGenerator.MERSENNES1[0],
                                MersennesProbeGenerator.MERSENNES1[1],
                                MersennesProbeGenerator.MERSENNES1[2])

    def hash2(self, int_list):
        '''Basic hash function #2'''
        return self.simple_hash(int_list,
                                MersennesProbeGenerator.MERSENNES2[0],
                                MersennesProbeGenerator.MERSENNES2[1],
                                MersennesProbeGenerator.MERSENNES2[2])

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

        self.probegenerator = probegenerator or MersennesProbeGenerator()

        self.data = data or [long(0) for _ in xrange(self.num_words)]

    def get_data(self):
        return self.data

    def get_nr_of_probes(self):
        return self.num_probes_k

    def get_nr_of_bits(self):
        return self.num_bits_m

    def add(self, key):
        for bitno in self.probegenerator.get_probes(self.num_probes_k, self.num_bits_m, key):
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
        if compress:
            data_bytes = zlib.compress(data_bytes)

        result = {
            "v": BloomFilter.VERSION,
            "n": self.ideal_num_elements_n,
            "p": self.error_rate_p,
            "zlib": compress,
            "data": base64.encodestring(data_bytes)
        }
        return json.dumps(result)

    @classmethod
    def fromJSON(cls, json_bf):
        result = json.loads(json_bf)
        v = result.get("v", None)
        n = result.get("n", None)
        p = result.get("p", None)
        compressed = result.get("zlib", None)
        b64data = result.get("data", None)

        if not v or not n or not p or not b64data:
            raise ValueError("Invalid BloomFilter JSON structure")

        if v != BloomFilter.VERSION:
            raise ValueError("Incompatible BloomFilter version")

        rawdata = base64.decodestring(b64data)
        if compressed:
            rawdata = zlib.decompress(rawdata)

        data = byteArrayToLongArray(rawdata)
        return BloomFilter(ideal_num_elements_n=n, error_rate_p=p, data=data)

    def __contains__(self, key):
        for bitno in self.probegenerator.get_probes(self.num_probes_k, self.num_bits_m, key):
            wordno, bit_within_wordno = divmod(bitno, 32)
            mask = 1 << bit_within_wordno
            if not self.data[wordno] & mask:
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

if __name__ == '__main__':
    from random import sample
    from string import ascii_letters

    states = '''Alabama Alaska Arizona Arkansas California Colorado Connecticut
        Delaware Florida Georgia Hawaii Idaho Illinois Indiana Iowa Kansas
        Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota
        Mississippi Missouri Montana Nebraska Nevada NewHampshire NewJersey
        NewMexico NewYork NorthCarolina NorthDakota Ohio Oklahoma Oregon
        Pennsylvania RhodeIsland SouthCarolina SouthDakota Tennessee Texas Utah
        Vermont Virginia Washington WestVirginia Wisconsin Wyoming'''.split()

    bf1 = BloomFilter(ideal_num_elements_n=1000000, error_rate_p=0.001)
    for state in states:
        bf1.add(state)

    json_bf = bf1.toJSON()

    print "##################"
    print json_bf
    print "##################"

    len_json = len(json_bf)
    print "data size: %s bytes"%len_json

    bf2 = BloomFilter.fromJSON(json_bf)
    assertListEquals(bf1.data, bf2.data)

    new_data = bf2.get_data()

    m = sum(state in bf2 for state in states)
    print('%d true positives out of %d trials' % (m, len(states)))

    trials = 100000
    fp = 0
    for trial in range(trials):
        while True:
            candidate = ''.join(sample(ascii_letters, 5))
            # If we accidentally found a real state, try again
            if candidate in states:
                continue
            if candidate in bf2:
                fp += 1
            break
    print('%d true negatives and %d false positives out of %d trials'
          % (trials-fp, fp, trials))
