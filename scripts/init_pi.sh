cd $HOME
sudo apt update -y
sudo apt install -y build-essential libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev
sudo apt install -y qtbase5-dev qt5-qmake
wget https://www.python.org/ftp/python/3.11.1/Python-3.11.1.tgz
tar -zxvf Python-3.11.1.tgz
cd Python-3.11.1
sudo ./configure --enable-optimizations
sudo make -j
sudo make altinstall
sudo rm -r ~/Python-3.11.1
sudo rm -r ~/Python-3.11.1.tgz
git clone https://github.com/MrTaco9001/wrx-digital-dashboard.git
cd $HOME/wrx-digital-dashboard
git config pull.rebase true
python3.11 -m pip install pyqt5-tools
python3.11 -m pip install PyQt5==5.15.7 --config-settings --confirm-license= --verbose
python3.11 -m pip install -r requirements.txt
cd scripts
sudo chmod +x start_can.sh
sudo chmod +x start_dash.sh
sudo chmod +x update.sh
sudo systemctl disable raspi-config.service rng-tools-debian.service
