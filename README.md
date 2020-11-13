# RSSReader

Add as a cronjob at 15m interval:

```sh
chmod u+x main.py
crontab -e
*/15 * * * * /home/pi/RSSReader/main.py
```

cronjob at 12:05 for Spotify

```sh
5 12 * * * /home/pi/RSSReader/Spotify.py
```

cronjob at 6 for daily:

```sh
0 6 * * * /home/pi/RSSReader/daily.py
```
