sudo /sbin/ip link set can0 down
sudo /sbin/ip link set can0 up type can bitrate 500000
python3.11 -m can.viewer -i socketcan -c can0 -b 500000
