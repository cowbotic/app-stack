FROM alpine
MAINTAINER Cowbotic cowbotic@protonmail.com

# basic flask environment
RUN apk add --no-cache gcc linux-headers musl-dev python3-dev nginx uwsgi uwsgi-python3 bash git\
        && pip3 install --upgrade pip\
        && pip3 install flask
RUN apk update

# application folder
ENV APP_DIR /flask-app

# app dir
RUN mkdir ${APP_DIR} \
        && chown -R nginx:nginx ${APP_DIR} \
        && chmod 777 /run/ -R

VOLUME [${APP_DIR}]
WORKDIR ${APP_DIR}
RUN git clone https://github.com/cowbotic/app-stack.git ${APP_DIR}

# copy config files into filesystem
COPY config_files/flask_app.ini /flask_app.ini
COPY config_files/nginx.conf /etc/nginx/nginx.conf
COPY config_files/start_flask_app.sh /start_flask_app.sh

COPY config_files/os_packets.txt ${APP_DIR}/os_packets.txt
COPY config_files/python_libraries.txt ${APP_DIR}/python_libraries.txt


# Expose port 80 on container
EXPOSE 80

# exectute start up script
ENTRYPOINT ["bash","/start_flask_app.sh"]