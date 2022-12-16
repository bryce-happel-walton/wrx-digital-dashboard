**Requires Python3.11+ (init script will auto install on RPi)**

install required libraries:

`python3.11 -m pip -r requirements.txt`

**On RPi**

`sudo nano /boot/config`

```
dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25
```

`sudo reboot`

```
cd $HOME
git clone https://github.com/MrTaco9001/wrx-digital-dashboard.git
cd wrx-digital-dashboard && chmod +x scripts/init_pi.sh && ./scripts/init_pi.sh
```
