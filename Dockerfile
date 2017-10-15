FROM ubuntu:16.04

 
# Install dependencies
RUN apt-get update && apt-get -y upgrade
RUN apt-get -y install build-essential libevent-dev libssl-dev tor git curl vim
RUN apt-get -y install python python3 python3-dev python-pip python-virtualenv
RUN apt-get -y install nginx npm
RUN apt-get -y install libcurl4-openssl-dev libxml2-dev libxslt1-dev
RUN apt-get -y install postgresql postgresql-contrib
RUN update-alternatives --install /usr/bin/node node /usr/bin/nodejs 10


# Setup postgres
RUN service postgresql start
COPY misc/setup-db.sh /tmp/
COPY misc/setup_db.sql /tmp/
RUN /tmp/setup-db.sh


# Setup illume
RUN mkdir -p /app/unshadow/unshadow/data
COPY unshadow /app/unshadow/unshadow/
COPY static /app/unshadow/static/
COPY README.md /app/unshadow/
COPY requirements.txt /app/unshadow/
COPY unshadow-crawler /app/unshadow/
COPY unshadow-metrics /app/unshadow/
COPY misc/seed /app/unshadow/unshadow/data/fetcher_inbox/
WORKDIR "/app/unshadow"
RUN virtualenv -p `which python3` env
RUN . env/bin/activate && pip install -r requirements.txt
RUN . env/bin/activate && python -m nltk.downloader -d /usr/local/share/nltk_data all
#RUN . env/bin/activate && python setup.py test

# Set up web server
WORKDIR "/app/unshadow/static"
RUN npm install -g gulp
RUN npm install
RUN gulp

COPY misc/nginx.conf /etc/nginx/
COPY misc/entrypoint.sh  /app/unshadow/
RUN echo "local all all trust" > /etc/postgresql/9.5/main/pg_hba.conf
RUN echo "host all all 127.0.0.1/32 trust" >> /etc/postgresql/9.5/main/pg_hba.conf
RUN echo "host all all ::1/128 trust" >> /etc/postgresql/9.5/main/pg_hba.conf
WORKDIR "/app/unshadow"

# Set up cron
COPY misc/cron /etc/cron.d/
COPY misc/backup /app/unshadow/backup


RUN service nginx start
RUN service postgresql start
EXPOSE 5432
EXPOSE 80
CMD ["/app/unshadow/entrypoint.sh"]
