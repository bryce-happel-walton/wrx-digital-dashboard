**Requires Python3.11+ (init script will auto install on RPi)**

**On Apple Silicon Macs, you must install PyQt5 using a rosetta environment.** This environment is provided in the .vscode profile. You do not need to do anything more.

Add PiCan device overlay

`sudo nano /boot/config`

```sh
dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25
```

`sudo reboot`

The init script installs Python and PyQt5.

**This will take a few hours to finish.**

```sh
cd ~
git clone https://github.com/MrTaco9001/wrx-digital-dashboard.git
cd wrx-digital-dashboard && chmod +x scripts/init_pi.sh && ./scripts/init_pi.sh
```

Recommendations:

- Raspberry Pi OS 64-Bit
- Overclock RPi to 2Ghz CPU 750Mhz GPU
- Force boost
- USB boot device
