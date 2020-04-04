# RSSReader

Add as a cronjob at 15m interval:

```sh
chmod u+x main.py
crontab -e
*/15 * * * * /home/pi/RSSReader/main.py
```
