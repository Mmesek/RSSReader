docker stop RSS RSS_Client
docker rm RSS RSS_Client
docker build -f ./.docker/Dockerfile -t rss:latest .
docker image prune
docker create --network database --name RSS -p 8081:8080 rss:latest
docker create --network database --name RSS_Client --entrypoint python rss:latest -m RSS.client
docker start RSS