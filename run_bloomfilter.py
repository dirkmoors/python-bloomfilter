#!/usr/bin/env python
"""
bloomfilter.py: A pure python implementation of a bloom filter

sources:
http://code.activestate.com/recipes/577686-bloom-filter/
http://stromberg.dnsalias.org/svn/bloom-filter/trunk/bloom_filter_mod.py

Modified by Dirk Moors
"""

from bloomfilter import BloomFilter
from bloomfilter.probegenerators import get_probegenerator

def assertListEquals(l1, l2):
    assert len(l1) == len(l2)
    for i in xrange(len(l1)):
        assert l1[i] == l2[i]

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

    bf1 = BloomFilter(ideal_num_elements_n=100000, error_rate_p=0.001, probegenerator=get_probegenerator("MURMUR"))
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
