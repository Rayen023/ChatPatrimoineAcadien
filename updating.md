docker stop patrimoine-container
docker rm patrimoine-container
docker system prune -a -f
docker build -t patrimoine .
docker tag patrimoine:latest rayengh01/patrimoine:latest
docker push rayengh01/patrimoine:latest
docker run -d --restart always --gpus all -p 8085:8085 --name patrimoine-container rayengh01/patrimoine
docker restart patrimoine-container