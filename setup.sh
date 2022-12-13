cd
wget https://github.com/legorovers/pirover_simulator/archive/refs/heads/master.zip
unzip master.zip
mv pirover_simulator-master pirover_simulator
echo "export PYTHONPATH=$PYTHONPATH:~/pirover_simulator" > tmp.txt
cat .bashrc tmp.txt > tmp2.txt
mv tmp2.txt .bashrc
rm tmp.txt
source .bashrc
