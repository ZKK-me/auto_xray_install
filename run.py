import os 

if  __name__=="__main__":
    url = "www.my.com"

    # 建立网站
    os.system("sudo apt update && sudo apt install nginx")
    os.system("mkdir -p /home/www/web/")

    web_content = """<html lang="">
  <!-- Text between angle brackets is an HTML tag and is not displayed.
        Most tags, such as the HTML and /HTML tags that surround the contents of
        a page, come in pairs; some tags, like HR, for a horizontal rule, stand
        alone. Comments, such as the text you're reading, are not displayed when
        the Web page is shown. The information between the HEAD and /HEAD tags is
        not displayed. The information between the BODY and /BODY tags is displayed.-->
  <head>
    <title>Enter a title, displayed at the top of the window.</title>
  </head>
  <!-- The information between the BODY and /BODY tags is displayed.-->
  <body>
    <h1>Enter the main heading, usually the same as the title.</h1>
    <p>Be <b>bold</b> in stating your key points. Put them in a list:</p>
    <ul>
      <li>The first item in your list</li>
      <li>The second item; <i>italicize</i> key words</li>
    </ul>
    <p>Improve your image by including an image.</p>
    <p>
      <img src="https://i.imgur.com/SEBww.jpg" alt="A Great HTML Resource" />
    </p>
    <p>
      Add a link to your favorite
      <a href="https://www.dummies.com/">Web site</a>. Break up your page
      with a horizontal rule or two.
    </p>
    <hr />
    <p>
      Finally, link to <a href="page2.html">another page</a> in your own Web
      site.
    </p>
    <!-- And add a copyright notice.-->
    <p>&#169; Wiley Publishing, 2011</p>
  </body>
</html>
    """

    with open("/home/www/web/index.html", "w") as f:
        f.write(web_content)

    os.system("chmod 777 /home -R")

    nginx_content = f"""
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {{
	worker_connections 768;
	# multi_accept on;
}}

http {{
	##
	# Basic Settings
	##

	sendfile on;
	tcp_nopush on;
	tcp_nodelay on;
	keepalive_timeout 65;
	types_hash_max_size 2048;
	# server_tokens off;

	include /etc/nginx/mime.types;
	default_type application/octet-stream;

	ssl_protocols TLSv1 TLSv1.1 TLSv1.2; # Dropping SSLv3, ref: POODLE
	ssl_prefer_server_ciphers on;

	access_log /var/log/nginx/access.log;
	error_log /var/log/nginx/error.log;

	gzip on;

	include /etc/nginx/conf.d/*.conf;
	include /etc/nginx/sites-enabled/*;

	server {{
                listen 80;
                server_name {url};
                root /home/www/web;
                index index.html;
    }}

}}

    """
    with open("/etc/nginx/nginx.conf", "w") as f:
        f.write(nginx_content)

    os.system("systemctl reload nginx")

    os.system("wget -O -  https://get.acme.sh | sh")
    os.system("source /root/.bashrc")
    os.system("acme.sh --upgrade --auto-upgrade")
    os.system("acme.sh --set-default-ca --server letsencrypt")
    os.system(f"acme.sh --issue -d {url} -w /home/www/web --keylength ec-256 --force")
    os.system(f"mkdir /home/cert")
    os.system("chmod 777 /home -R")

    os.system(f"acme.sh --installcert -d {url} --cert-file /home/cert/cert.crt --key-file /home/cert/cert.key --fullchain-file /home/cert/fullchain.crt --ecc")
    os.system("wget https://github.com/XTLS/Xray-install/raw/main/install-release.sh")
    os.system("sudo bash install-release.sh")
    os.system("chmod 777 /home -R")
    os.system("mkdir /home/xray_cert")
    os.system("chmod 777 /home -R")
    os.system(f"acme.sh --install-cert -d {url} --ecc --fullchain-file /home/xray_cert/xray.crt --key-file /home/xray_cert/xray.key")
    os.system("chmod 777 /home -R")

    renew_content = f"""#!/bin/bash

/root/.acme.sh/acme.sh --install-cert -d {url} --ecc --fullchain-file /home/xray_cert/xray.crt --key-file /home/xray_cert/xray.key
echo "Xray Certificates Renewed"

chmod +r /home/xray_cert/xray.key
echo "Read Permission Granted for Private Key"

sudo systemctl restart xray
echo "Xray Restarted"
    """

    with open("/home/xray_cert/xray-cert-renew.sh", "w") as f:
        f.write(renew_content)

    os.system("chmod 777 /home -R")

    os.system("crontab -e")
    crontab_content = f"""# 1:00am, 1st day each month, run `xray-cert-renew.sh`
0 1 1 * *   bash /home/xray_cert/xray-cert-renew.sh
"""

    os.system("xray uuid")
    input("复制上面的uuid，然后按回车继续")

    os.system("chmod 777 /home -R")
    os.system("mkdir /home/xray_log")
    os.system("touch /home/xray_log/access.log && touch /home/xray_log/error.log")
    os.system("chmod 777 /home -R")

    uuid = input("请输入上面的uuid：")
    config_content = f"""
{{
  "log": {{
    "loglevel": "warning",
    "access": "/home/xray_log/access.log",
    "error": "/home/xray_log/error.log"
  }},
  "dns": {{
    "servers": [
      "https+local://1.1.1.1/dns-query",
      "localhost"
    ] 
  }},
  "routing": {{
    "domainStrategy": "IPIfNonMatch",
    "rules": [
      {{
        "type": "field",
        "ip": [
          "geoip:private"
        ],
        "outboundTag": "block"
      }},
      {{
        "type": "field",
        "ip": ["geoip:cn"],
        "outboundTag": "block"
      }},
      {{
        "type": "field",
        "domain": [
          "geosite:category-ads-all"
        ],
        "outboundTag": "block"
      }}
    ]
  }},
  "inbounds": [
    {{
      "port": 443,
      "protocol": "vless",
      "settings": {{
        "clients": [
          {{
            "id": "{uuid}", // 填写你的 UUID
            "flow": "xtls-rprx-vision",
            "level": 0,
            "email": "myemail@163.com"
          }}
        ],
        "decryption": "none",
        "fallbacks": [
          {{
            "dest": 8080
          }}
        ]
      }},
      "streamSettings": {{
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {{
          "alpn": "http/1.1",
          "certificates": [
            {{
              "certificateFile": "/home/xray_cert/xray.crt",
              "keyFile": "/home/xray_cert/xray.key"
            }}
          ]
        }}
      }}
    }}
  ],
  "outbounds": [
    {{
      "tag": "direct",
      "protocol": "freedom"
    }},
    {{
      "tag": "block",
      "protocol": "blackhole"
    }}
  ]
}}
"""
    with open("/usr/local/etc/xray/config.json", "w") as f:
        f.write(config_content)

    os.system("sudo systemctl start xray")
    os.system("sudo systemctl enable xray")

    nginx_content = f"""
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {{
	worker_connections 768;
	# multi_accept on;
}}

http {{
	##
	# Basic Settings
	##

	sendfile on;
	tcp_nopush on;
	tcp_nodelay on;
	keepalive_timeout 65;
	types_hash_max_size 2048;
	# server_tokens off;

	include /etc/nginx/mime.types;
	default_type application/octet-stream;

	ssl_protocols TLSv1 TLSv1.1 TLSv1.2; # Dropping SSLv3, ref: POODLE
	ssl_prefer_server_ciphers on;

	access_log /var/log/nginx/access.log;
	error_log /var/log/nginx/error.log;

	gzip on;

	include /etc/nginx/conf.d/*.conf;
	include /etc/nginx/sites-enabled/*;

	server {{
                listen 80;
                server_name {url};
                location ~ .*\\.(jpg|jpeg|gif|png|ico|css|js|pdf|txt)$ {{
                    root /home/www/web;
                }}
				return 301 https://$http_host$request_uri;
    }}

    server {{
       listen 127.0.0.1:8080;
       root /home/www/web;

       index index.html;
       add_header Strict-Transport-Security "max-age=63072000" always;

    }}

}}

    """
    with open("/etc/nginx/nginx.conf", "w") as f:
        f.write(nginx_content)
    
    os.system("sudo systemctl restart nginx")