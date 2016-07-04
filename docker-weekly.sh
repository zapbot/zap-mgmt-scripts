cd ../zaproxy
docker build --no-cache -t owasp/zap2docker-weekly -f build/docker/Dockerfile-weekly build/docker/
docker push owasp/zap2docker-weekly
