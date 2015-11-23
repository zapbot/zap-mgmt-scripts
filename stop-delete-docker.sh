# Stops and deletes all docker containers

docker stop `docker ps -q`
docker rm --force `docker ps -aq`
docker rmi `docker images -aq`
