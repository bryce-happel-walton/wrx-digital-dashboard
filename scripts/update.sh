cd $HOME
cd wrx-digital-dashboard
git reset --hard
git clean -fxd
git pull
python3.11 scripts/pi_script_activate.py
