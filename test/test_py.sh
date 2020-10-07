#!/bin/bash
python3 java_random.py out_nextBytes_1_py.bin 10000 95876265768466 nextBytes 257
python3 java_random.py out_nextBytes_2_py.bin 20000 65882587452163 nextBytes 128
python3 java_random.py out_nextInt_py.bin 1048576 -3865984986348818578 nextInt
python3 java_random.py out_nextInt_1_py.bin 1048576 8645836755261 nextInt 10
python3 java_random.py out_nextInt_2_py.bin 1048576 -73865865 nextInt 1073741825
python3 java_random.py out_nextLong_py.bin 1048576 7348635979463856121 nextLong
python3 java_random.py out_nextBoolean_py.bin 1048576 -735785672572 nextBoolean
python3 java_random.py out_nextFloat_py.bin 1048576 6248685 nextFloat
python3 java_random.py out_nextDouble_py.bin 1048576 -7158636 nextDouble
python3 java_random.py out_nextGaussian_py.bin 1048576 186586357641 nextGaussian
