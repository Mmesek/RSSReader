docker stop RSS RSS_Client
docker rm RSS RSS_Client
docker build -f ./.docker/Dockerfile -t rss:latest .
docker image prune
docker create --link postgres --name RSS rss:latest
docker create --link postgres --name RSS_Client --entrypoint python rss:latest -m rss.client
docker start RSS