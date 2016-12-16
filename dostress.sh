for i in 0 0.01 0.05
do
    for j in 1 5 10 20 40 60 100 150 200
    do
        python stressmarathon.py 300 $j pypy 10000 $i
    done
done
