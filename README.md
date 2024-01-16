# RSSReader

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![CodeFactor Grade](https://img.shields.io/codefactor/grade/github/Mmesek/RSSReader)](https://www.codefactor.io/repository/github/mmesek/rssreader/overview/main)
[![Lines of code](https://sloc.xyz/github/Mmesek/RSSReader)]()
[![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/Mmesek/RSSReader)]()
[![GitHub repo size](https://img.shields.io/github/repo-size/Mmesek/RSSReader)]()

[![GitHub issues](https://img.shields.io/github/issues/Mmesek/RSSReader)](../../issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/Mmesek/RSSReader)](../../pulls)
[![GitHub contributors](https://img.shields.io/github/contributors/Mmesek/RSSReader)](../../graphs/contributors)
[![Discord](https://img.shields.io/discord/517445947446525952)](https://discord.gg/RPHnebgZDs)

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

RSS feed parser sending entries as embeds via webhooks to Discord Channels

## Installation

```sh
git clone https://github.com/Mmesek/RSSReader.git
cd RSSReader
python -m pip install -r requirements.txt
```

## Configuration

Feeds & Webhooks are stored in database

Database configuration can be specified as either connection string as environment variable `DATABASE_URL`:

Unix/Shell:
```sh
set DATABASE_URL="postgresql+psycopg2://postgres:PASSWORD:5432/public"
```

Windows/Powershell:
```powershell
$env:DATABASE_URL = "dialect+driver://user:PASSWORD:port/database"
```
*Note that environment variable is temporary (until terminal session is closed)*


or as `config.ini` with flag `--cfg=config.ini`:
```ini
[Database]
db = postgresql+psycopg2
user = postgres
password = PASSWORD
location = 127.0.0.1
port = 5432
name = public
```

## Database Tables
### Feed
There are stored tracked feeds:
 - `URL` to feed.
 - `last_post` being a timestamp of last entry in this feed.
 - `refresh_rate` when set, it won't attempt to fetch this feed again unless it's changed. Set to 0:00:00 to disable.

### Feed_Component
Processing of feeds for each entry can be customized there. Available components can be found in `processors.py`

### Subscription
This is many-to-many relationship between `Feed` and `Webhook` tables.

### Webhook
Webhook's `ID` and `Token` are stored here

## Running

Whole package is a run-once script, therefore if you want to run it more often, you'll need to setup cronjob to start it manually

Run once:
```sh
python -m RSS
```

As a cronjob at 15m interval:
```sh
*/15 * * * * python -m RSS
```

Alternatively if you deploy to Heroku, you can trigger it by restarting (deleting) Dyno with curl request:
```sh
curl -n -X DELETE https://api.heroku.com/apps/{APP_NAME}/dynos -H "Content-Type: application/json" -H "Accept: application/vnd.heroku+json; version=3" -H "Authorization: Bearer {TOKEN}"
```

## Caveats

Code has been tested in production against PostgreSQL. Free tier on either Heroku or Supabase should be well more than enough for simple use case. 

MySQL was tested in limited capacity and requires code modifications: 
- Removing `.filter()` from `Feed.get()` method
- Adding length to all string based columns in `models.py` by replacing `sa.String` with for example `sa.String(100)`
- Due to lack of `Interval` type, `refresh_rate` *may* not work there
