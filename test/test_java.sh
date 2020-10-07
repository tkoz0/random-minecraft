#!/bin/bash
java JavaRandom out_nextBytes_1_java.bin 10000 95876265768466 nextBytes 257
java JavaRandom out_nextBytes_2_java.bin 20000 65882587452163 nextBytes 128
java JavaRandom out_nextInt_java.bin 1048576 -3865984986348818578 nextInt
java JavaRandom out_nextInt_1_java.bin 1048576 8645836755261 nextInt 10
java JavaRandom out_nextInt_2_java.bin 1048576 -73865865 nextInt 1073741825
java JavaRandom out_nextLong_java.bin 1048576 7348635979463856121 nextLong
java JavaRandom out_nextBoolean_java.bin 1048576 -735785672572 nextBoolean
java JavaRandom out_nextFloat_java.bin 1048576 6248685 nextFloat
java JavaRandom out_nextDouble_java.bin 1048576 -7158636 nextDouble
java JavaRandom out_nextGaussian_java.bin 1048576 186586357641 nextGaussian
