cd $HOME
sudo apt upgrade -y
sudo apt update -y
sudo apt install -y build-essential libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev
wget https://www.python.org/ftp/python/3.11.1/Python-3.11.1.tgz
tar -zxvf Python-3.11.1.tgz
cd Python-3.11.1
./configure --enable-optimizations
sudo make altinstall
git clone https://github.com/MrTaco9001/wrx-digital-dashboard.git
cd $HOME/wrx-digital-dashboard
git config pull.rebase true
pip3.11 install -r requirements.txt
