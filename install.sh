function installServer() {
  apt-get install sudo
  curl -sSL https://get.docker.com | sh
  sudo usermod -aG docker $(whoami)
  docker pull vkolesnev/amneziavpn:latest
  docker run -d \
    --name=ducksvpn \
    -e LANG=en \
    -e WG_HOST=$1 \
    -e PASSWORD=$2 \
    -e UI_TRAFFIC_STATS=true \
    -e UI_CHART_TYPE=1 \
    -e WG_MTU=1332 \
    -v ~/.vpnducks:/etc/wireguard \
    -p 51820:51820/udp \
    -p 51821:51821/tcp \
    --cap-add=NET_ADMIN \
    --cap-add=SYS_MODULE \
    --sysctl="net.ipv4.conf.all.src_valid_mark=1" \
    --sysctl="net.ipv4.ip_forward=1" \
    --device=/dev/net/tun:/dev/net/tun \
    --restart unless-stopped \
    vkolesnev/amneziavpn:latest

  set firewall name WAN_LOCAL rule 30 action accept
  set firewall name WAN_LOCAL rule 30 description 'Accept Wireguard VPN server connections'
  set firewall name WAN_LOCAL rule 30 destination port 51820
  set firewall name WAN_LOCAL rule 30 log disable
  set firewall name WAN_LOCAL rule 30 protocol udp
  set firewall name WAN_LOCAL rule 30 source address 0.0.0.0/0
  set firewall name WAN_LOCAL rule 30 state established enable
  set firewall name WAN_LOCAL rule 30 state new enable
  set firewall name WAN_LOCAL rule 30 state related enable

  clear
  echo "Installed WG Amnezia DUCK VPN Server"
  echo "Admin panel of WG Amnezia DUCK VPN on http://$1:51821/"
}

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
  sudo apt-get install sqlite3 -y
  sqlite3 data.sqlite < schema_db.sql
  mkdir data
  clear
  echo "Installed TG"
  echo "Congratulations! Now you must configure the .env (copy .env.example to .env) configuration file at .env"
}

installServer $1 $2
installTg $1 $2
