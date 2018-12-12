FROM jazzdd/alpine-flask:python3

RUN cd /app
RUN apk update
RUN pip install requests jsonify redis
RUN git clone https://github.com/cowbotic/aks-demo.git .
