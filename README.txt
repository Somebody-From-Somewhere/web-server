To run server in docker container locally you need docker installed

And run next comands in directory with Dockerfile

docker build . --tag server
docker run -dp 127.0.0.1:You_port:53210 server

After that you can send you request with netcat:

nc localhost you_port
GET /card/card_number HTTP/1.1
Host: example.local


If you want to run server with another Host_name(default=example.local) and another internal_port(default=53210) change this parameters in Dockerfile
