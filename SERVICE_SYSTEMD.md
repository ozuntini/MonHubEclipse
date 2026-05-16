# Service systemd

Crée un **service système** qui lance Accueil.py via Streamlit automatiquement au boot.

## Service systemd Streamlit en local

### Création du service

Créer le fichier monhubeclipse.service :
```bash
sudo nano /etc/systemd/system/monhubeclipse.service
```

Le compléter avec les paramêtres suivants :

```ini
[Unit]
Description=MonHubEclipse (Streamlit)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ozuntini
Group=ozuntini
WorkingDirectory=/home/ozuntini/Eclipse_Project/MonHubEclipse/

# Streamlit écoute en local seulement (sécurité), Nginx exposera le port 80
ExecStart=/home/ozuntini/eclipse_env/bin/streamlit run Accueil.py --server.address 127.0.0.1 --server.port 8501

Restart=always
RestartSec=3

# Un environnement un peu plus “propre” côté systemd
Environment=HOME=/home/ozuntini
Environment=PYTHONUNBUFFERED=1

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### activation du service

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now monhubeclipse.service
sudo systemctl restart monhubeclipse.service
```

### Vérification de l'activation
#### Vérification du status

```bash
sudo systemctl status monhubeclipse.service
```

Résultat :

```log
● monhubeclipse.service - MonHubEclipse (Streamlit)
     Loaded: loaded (/etc/systemd/system/monhubeclipse.service; enabled; preset: enabled)
     Active: active (running) since Sat 2026-05-16 21:33:51 CEST; 5min ago
 Invocation: 6886f4a4b8054600a9e1f5a5f09c33e8
   Main PID: 3536 (streamlit)
      Tasks: 5 (limit: 3967)
        CPU: 3.536s
     CGroup: /system.slice/monhubeclipse.service
             └─3536 /home/ozuntini/eclipse_env/bin/python3 /home/ozuntini/eclipse_env/bin/streamlit run Accueil.py --server.address 127.0.0.1 --server.port 8501

May 16 21:33:51 I-RaspEclipse systemd[1]: Started monhubeclipse.service - MonHubEclipse (Streamlit).
May 16 21:33:52 I-RaspEclipse streamlit[3536]: Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
May 16 21:33:53 I-RaspEclipse streamlit[3536]: 2026-05-16 21:33:53.471 Uvicorn server started on 127.0.0.1:8501
May 16 21:33:53 I-RaspEclipse streamlit[3536]:   You can now view your Streamlit app in your browser.
May 16 21:33:53 I-RaspEclipse streamlit[3536]:   URL: http://127.0.0.1:8501
```

#### Vérification de l'activation du service

```bash
journalctl -u monhubeclipse.service -e
```

Résultat :

```log
May 16 21:24:11 I-RaspEclipse streamlit[3450]: Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
May 16 21:24:11 I-RaspEclipse streamlit[3450]: 2026-05-16 21:24:11.572 Uvicorn server started on 127.0.0.1:8501
May 16 21:24:11 I-RaspEclipse streamlit[3450]:   You can now view your Streamlit app in your browser.
May 16 21:24:11 I-RaspEclipse streamlit[3450]:   URL: http://127.0.0.1:8501
```

#### Test en local

```bash
curl -I http://127.0.0.1:8501
```

Résultat :

```log
HTTP/1.1 200 OK
date: Sat, 16 May 2026 19:44:03 GMT
server: uvicorn
content-type: text/html; charset=utf-8
accept-ranges: bytes
content-length: 5381
last-modified: Sat, 16 May 2026 18:05:10 GMT
etag: "c2775d78108f52a2d0a68d3bff15c69c"
cache-control: no-cache
```

**Pour accéder à Accueil il faut activer un proxy** c.f. Utilisation d'un reverse proxy

## Service systemd Streamlit accessible en direct

Dans le fichier monhubeclipse.service modifier la ligne ExecStart.
```ini
# Streamlit écoute en local seulement (sécurité), Nginx exposera le port 80
ExecStart=/home/ozuntini/eclipse_env/bin/streamlit run Accueil.py --server.address 0.0.0.0 --server.port 8501
```

Reprendre le cycle d'activation et de vérification vue plus haut.

Vérification depuis au autre PC sur le même réseau :  
`http://IP_DU_PI:8501` dans un navigateur.

## Utilisation d'un reverse proxy

### Installation

```bash
sudo apt install -y nginx
```

### Création d'une configuration de site

```bash
sudo nano /etc/nginx/sites-available/monhubeclipse
```

Le compléter avec les paramêtres suivants :

```nginx
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Streamlit utilise du websocket
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

### Activer le site

```bash
sudo ln -s /etc/nginx/sites-available/monhubeclipse /etc/nginx/sites-enabled/monhubeclipse
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Vérification du fonctionnement

```bash
curl -I http://127.0.0.1
```

Résultat :

```log
HTTP/1.1 200 OK
...
```

Vérification depuis au autre PC sur le même réseau :  
`http://IP_DU_PI` dans un navigateur.

### Adaptation du nginx (optionnel)

Récupérer le hostname du PI
```bash
hostname
```

Modifier la conf du site
```nginx
server_name hostname.local;
```

```bash
curl -I http://hostname.local
```