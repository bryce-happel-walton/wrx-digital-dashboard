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

clone this repo to `$HOME`

```
cd $HOME && chmod +x wrx-digital-dashboard/scripts/init_pi.sh && ./wrx-digital-dashboard/scripts/init_pi.sh

```
