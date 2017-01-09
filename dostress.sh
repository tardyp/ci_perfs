#!/bin/bash
#python marathon.py master 1
#sleep 300
for k in 0 0.005 0.01 0.05
do
for i in 70000 5000 10000 20000 30000 40000 50000 60000  100 1000
do
for j in 150 30 50 80 100 125 170 200 300
do
python stressmarathon.py 300 $j 10pypy $i $k || exit
done
done
done
