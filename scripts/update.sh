cd ~/wrx-digital-dashboard
git reset --hard
git clean -f -X -d
git pull
python3.11 scripts/pi_script_activate.py
pip3.11 install -r requirements.txt
