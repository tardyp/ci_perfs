# -l/bin/bash
#python marathon.py master 1
#sleep 300
for k in 0.005 0.01
do
for i in 10000 40000 100
do
for j in 100 200 300 
do
python stressmarathon.py 300 $j 4pypy $i $k || exit
done
done
done
