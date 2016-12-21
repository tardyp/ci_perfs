#!/bin/bash
python marathon.py master 1
sleep 300
for i in 0 0.005
do
    for j in 20 30 50 80 100 125 150 170 200
    do
        python stressmarathon.py 300 $j pypy 10000 $i
    done
done
