cd ../zaproxy
docker build --no-cache -t owasp/zap2docker-weekly -f docker/Dockerfile-weekly docker/
docker push owasp/zap2docker-weekly
