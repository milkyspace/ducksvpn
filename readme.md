# 🦆 DUCKS VPN
## _The Best Telegram Vpn Service, Ever_

[![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/vpnducks_support)

DucksVPN is a system for VPN:
- Telegram bot for sales vpn subscribes
- DSM (Ducks Server Manager) https://github.com/milkyspace/ducks-server-manager

## Tech

Technically, the system now looks like this

![screenshot](readme.png)

And of course DUCKS VPN itself is open source with a public repository on GitHub.

## Installation

DUCKS VPN requires Docker and Python3 to run.\
You must create a bot in telegram via https://t.me/BotFather and create a store in YooKassa https://yookassa.ru/ to receive subscription payments

Install the dependencies and start the server.
You need to find out your ip address ($IP):
```sh
ip addr show
```

```sh
apt-get install git -y
git clone https://github.com/milkyspace/ducksvpn.git
cd ducksvpn
chmod u+x install.sh
./install.sh

mysql -u root -p
  # CREATE DATABASE ducksvpn;
  # GRANT ALL ON my_test_db.* TO 'admin'@'localhost' IDENTIFIED BY 'adminpassword' WITH GRANT OPTION;
  # FLUSH PRIVILEGES;
  # exit;

mysql -u admin -p adminpassword
  # use ducksvpn
  # CREATE TABLE IF NOT EXISTS userss (   id int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,   tgid varchar(50) UNIQUE,   subscription text,   banned BOOLEAN DEFAULT FALSE NOT NULL,   username varchar(50),   fullname varchar(50),  referrer_id int );
  # CREATE TABLE IF NOT EXISTS notions (   id int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,   tgid varchar(50) UNIQUE,   notion_type varchar(50) ,   complete BOOLEAN DEFAULT FALSE NOT NULL,  time DATETIME DEFAULT CURRENT_TIMESTAMP);
  # CREATE TABLE IF NOT EXISTS payments (  id int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,   tgid varchar(50),   bill_id text,   amount int,   time_to_add bigint,   mesid text , time DATETIME DEFAULT CURRENT_TIMESTAMP);
```

## Setting up a vpn server (any number)
You can use any server
- Install https://github.com/MHSanaei/3x-ui
- Use this https://dzen.ru/a/ZriA_y2iBCnoS7dT?ysclid=m1nfklo9j5716759728
- Then use this https://github.com/keivanipchihagh/x-ui#-optional-safety-first
- Then use this https://safereactor.cc/post/5761728
- Then use this https://github.com/DigneZzZ/dwg/blob/main/tools/block_torrent.sh
- Then use this https://github.com/keivanipchihagh/x-ui/blob/main/scripts/bbr.sh
- Then use this https://github.com/keivanipchihagh/x-ui/blob/main/scripts/ufw.sh (with extreme caution)

## Load balancing across servers
- Buy a domain on https://njal.la/ for a crypt
- Register on cloudflare.com
- Move domain from njal.la to cloudflare.com
- Get an SSL certificate for the domain
- Register one a-record per domain for each VPN server (do not turn on the CDN Cloudflare)

## DSM
Now you have to install DSM (Ducks Server Manager)
- https://github.com/milkyspace/ducks-server-manager
Setting up the DSM at .env
- Set VPN_DOMAIN_FOR_LINKS. Is the domain of previous step
- Add vpn servers to the panel

## Let's go back to setting up the telegram bot:
Change it .env: Enter your data using the example
```sh
mv .env.example .env
nano .env # or vim .env
```

**ADMIN_TG_ID_1** is tg id of first admin (go to @getmyid_bot)\
**ADMIN_TG_ID_2** is tg id of second admin  (go to @getmyid_bot)\
**ONE_MONTH_COST** is the price for 1 month\
**TRIAL_PERIOD** is days of trial period\
**COUNT_FREE_FROM_REFERRER** is count of months for referrer present\
**PERC_1** is calc price for 1 month\
**PERC_3** is calc price for 3 months\
**PERC_6** is calc price for 6 months\
**PERC_12** is calc price for 12 months\
**TG_TOKEN** is telegram bot token\
**TG_SHOP_TOKEN** is yookassa token\
**DB_HOST** is host of database
**DB_NAME** is name of database
**DB_USER** is user of database
**DB_PASSWORD** is password to user of database
**SERVER_MANAGER_URL** is url for server manager (for example DSM http://{IP}/api)
**SERVER_MANAGER_EMAIL** is login for server manager
**SERVER_MANAGER_PASSWORD** is password for server manager

Now you can start the telegram bot

```sh
sudo systemctl start ducksVpnTelegram
sudo systemctl status ducksVpnTelegram
```


## License

MIT

**Free Software**
