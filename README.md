# DaTra - Dein Tool für Datentransparenz und Datensicherheit
DaTra ist eine Webplattform, welche es Nutzer:innen ermöglicht herauszufinden, welche Daten im Internet über sie gespeichert sind. 

## Aufbau der Plattform
Die einzelnen Komponenten von DaTra laufen in unterschiedlichen Docker-Containern, welche wir mittels Docker Compose verwalten. Wir stellen zwei docker-compose-Konfigurationen bereit, eine für die Development-Umgebung und eine für das Produktivsystem. 

Die eigentlich Webapplikation ist in Flask geschrieben. Für die Produktionsumgebung nutzen wir gunicorn, einen Python WSGI Webserver, welchen wir hinter einen Reverse Proxy auf Basis von nginx gestellt haben. Für die verschlüsselte HTTPS-Verbindung zum Server nutzen wir Let’s Encrypt, wobei certbot sich um die automatische Beantragung der Zertifikate kümmert.

Das Suchen von weiteren Social-Media-Account mit dem OSINT-Tool Sherlock kann mehrere Minuten in Anspruch nehmen und wird direkt nach dem Einloggen in die DaTra-Plattform über die asynchrone Aufgabenwarteschlange celery gestartet und die Ergebnisse nach Abschluss der Analyse direkt in der Auswertungsseite von DaTra dargestellt. Als Nachrichtenbroker verwenden wir dazu RabbitMQ.

## Deployment
Für das Hosten von DaTra sind einige Konfigurationsschritte erforderlich.

### Social Logins
DaTra unterstützt die Social Logins von Google, LinkedIn und Facebook. Um DaTra selbst zu hosten, müssen zuvor auf den drei Plattformen Social Login Applikationen erstellt werden. Die dabei erzeugten Client-IDs sowie Client- und App-Secrets werden in den beiden .env-Dateien eingetragen. Auch die REDIRECT_URI von LinkedIn muss an die eigene Domain angepasst werden. 

### Domain
Auch in services/nginx/nginx.conf muss die Domain bei den Konfigurationsparametern upstream, server_name, ssl_certificate, ssl_certificate_key und proxy_pass ensprechend definiert werden.

### SQLite-Datenbank
Die erforderliche SQLite-Datenbank wird beim ersten Start von DaTra automatisch angelegt und außerhalb der Container persistent im Dateisystem gespeichert.

### Docker Compose
Um die Container zu bauen und DaTra zu starten, kann die docker-compose-Datei genutzt werden:
`docker-compose -f docker-compose.prod.yaml up -d --build`

### Logging
Logs können einfach mit `docker-compose -f docker-compose.prod.yaml logs -f` angezeigt werden.
