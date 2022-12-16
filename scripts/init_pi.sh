cd $HOME
wget https://www.python.org/ftp/python/3.11.1/Python-3.11.1.tgz
tar -zxvf Python-3.11.1.tgz
cd Python-3.11.1
./configure --enable-optimizations
sudo apt update -y
sudo apt upgrade -y
sudo apt install -y build-essential libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev
sudo make altinstall
git clone https://github.com/MrTaco9001/wrx-digital-dashboard.git
