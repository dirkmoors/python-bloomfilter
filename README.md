python-bloomfilter
==================

A pure python bloomfilter implementation with JSON (de)serialisation and (zlib) compression

Example:
```
bf1 = BloomFilter(ideal_num_elements_n=1000000, error_rate_p=0.001)
bf1.add("Alabama")
bf1.add("Illinois")
bf1.add("Nevada")
bf1.add("RhodeIsland")

serialized_bloomfilter = bf1.toJSON()

#You can transmit the serialized_bloomfilter easily accross the network

bf2 = BloomFilter.fromJSON(serialized_bloomfilter)

for state in ("Alabama", "Illinois", "Nevada", "RhodeIsland"):
  #Verify that the state MIGHT be in the bloomfilter
  assert state in bf2
  
for state in ("Vermont", "Louisiana", "Mississippi", "Texas"):
  #Verify that the state is DEFINITLY NOT in the bloomfilter
  assert state not in bf2
```
