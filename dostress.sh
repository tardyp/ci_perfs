# -l/bin/bash
#python marathon.py master 1
#sleep 300
for masters in 1 2 3 4
do
for sleeptime in 0 
do
for numlines in 10000 40000 100
do
for workers in 100 200 300 
do
python stressmarathon.py 300 $workers $masters pypy $numlines $sleeptime || exit
done
done
done
done
