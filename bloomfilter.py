#!/usr/bin/env python
"""
bloomfilter.py: A pure python implementation of a bloom filter

source: http://code.activestate.com/recipes/577686-bloom-filter/

Modified by Dirk Moors
"""

import math
import array
import random
import base64
import json
import zlib

def get_probes(bfilter, key):
    hasher = random.Random(key).randrange
    for _ in xrange(bfilter.get_nr_of_probes()):
        array_index = hasher(len(bfilter.get_data()))
        bit_index = hasher(32)
        yield array_index, 1 << bit_index

class BloomFilter(object):
    def __init__(self, ideal_num_elements_n, error_rate_p, data=None, probe_func=get_probes):
        if ideal_num_elements_n <= 0:
            raise ValueError('ideal_num_elements_n must be > 0')
        if not (0 < error_rate_p < 1):
            raise ValueError('error_rate_p must be between 0 and 1 exclusive')

        self.error_rate_p = error_rate_p
        self.ideal_num_elements_n = ideal_num_elements_n
        self.probe_func = probe_func

        self.num_bits_m = self._calculate_m(self.ideal_num_elements_n, self.error_rate_p)
        self.num_probes_k = self._calculate_k(self.ideal_num_elements_n, self.num_bits_m)

        number_of_words = self._calculate_num_words(self.num_bits_m)
        self.data = data or array.array('L', [0]) * number_of_words

    def toJSON(self, compress=True):
        result = {
            "n": self.ideal_num_elements_n,
            "p": self.error_rate_p,
            "zlib": compress
        }

        if not compress:
            result["data"] = base64.encodestring(self.data.tostring())
        else:
            result["data"] = base64.encodestring(zlib.compress(self.data.tostring()))

        return json.dumps(result)

    def get_data(self):
        return self.data

    def get_nr_of_probes(self):
        return self.num_probes_k

    def get_nr_of_bits(self):
        return self.num_bits_m

    def add(self, key):
        for i, mask in self.probe_func(self, key):
            self.data[i] |= mask

    def match_template(self, bfilter):
        return (
            self.num_bits_m == bfilter.get_nr_of_bits() and
            self.num_probes_k == bfilter.get_nr_of_probes() and
            self.probe_func == bfilter.probe_func
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

    def _calculate_m(self, n, p):
        numerator = -1 * n * math.log(p)
        denominator = math.log(2) ** 2
        #self.num_bits_m = - int((self.ideal_num_elements_n * math.log(self.error_rate_p)) / (math.log(2) ** 2))
        real_num_bits_m = numerator / denominator
        return int(math.ceil(real_num_bits_m))

    def _calculate_k(self, n, m):
        real_num_probes_k = (m / n) * math.log(2)
        return int(math.ceil(real_num_probes_k))

    def _calculate_num_words(self, m):
        return (m + 31) // 32

    def __contains__(self, key):
        return all(self.data[i] & mask for i, mask in self.probe_func(self, key))

    @staticmethod
    def fromJSON(json_bf):
        result = json.loads(json_bf)
        n = result.get("n", None)
        p = result.get("p", None)
        compressed = result.get("zlib", None)
        b64data = result.get("data", None)

        if not n or not p or not b64data or not zlib:
            raise ValueError("Invalid BloomFilter JSON structure")

        rawdata = base64.decodestring(b64data)
        if compressed:
            rawdata = zlib.decompress(rawdata)

        data = array.array("L")
        data.fromstring(rawdata)
        return BloomFilter(ideal_num_elements_n=n, error_rate_p=p, data=data)

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

    orig_data = bf1.get_data()

    json_bf = bf1.toJSON()

    len_json = len(json_bf)
    print "data size: %s bytes"%len_json

    bf2 = BloomFilter.fromJSON(json_bf)

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
