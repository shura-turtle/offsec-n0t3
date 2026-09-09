---
title: "Proxy Mnipu"
weight: 1
# bookFlatSection: false
# bookToc: true
# bookHidden: false
# bookCollapseSection: false
# bookComments: false
# bookSearchExclude: false
# bookHref: ''
# bookIcon: ''
---


```yml
question:

geoip2 /etc/nginx/GeoLite2-Country.mmdb {
    $geoip2_data_country_code default=ZZ country iso_code;
}
location / {
    if ($geoip2_data_country_code = IS) {
        proxy_pass http://south;
    }
    proxy_pass http://north;
}

solution:

sudo apt-get install tor
sudo systemctl start tor

sudo nano /etc/tor/torrc
|___ ExitNodes {Is}
     StrictNodes 1

sudo systemctl restart tor

curl --socks5-hostname 127.0.0.1:9050 https://ipwho.is/ -> check first

curl --socks5 127.0.0.1:9050 [target_host]
```