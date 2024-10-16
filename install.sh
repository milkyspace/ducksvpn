function installTg() {
  apt-get install unzip -y
  apt-get install python3 -y
  apt-get install pip -y
  sudo pip3 install -r requirements.txt --break-system-packages
  echo "[Unit]
        Description=Telegram bot for DUCK VPN
        After=multi-user.target

        [Service]
        Type=simple
        Restart=always
        RestartSec=15
        WorkingDirectory=$(pwd)
        ExecStart=/usr/bin/python3 $(pwd)/main.py
        User=root

        [Install]
        WantedBy=multi-user.target">"/etc/systemd/system/ducksVpnTelegram.service"
  systemctl daemon-reload
  sudo systemctl enable ducksVpnTelegram.service
  sudo apt-get install mariadb-server -y
  clear
  echo "Installed TG"
  echo "Congratulations! Now you must configure database and the .env (copy .env.example to .env) configuration file"
}

installTg
