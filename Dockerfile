FROM ubuntu

RUN mkdir /code
ADD . /code

RUN apt update && \
    apt install -y cron wget python3 python3-pip zip && \
    pip3 install boto3 && \
    touch /current_cron && \
    echo "* 11 * * * python3 /code/backup_today_data.py" >> /current_cron && \
    crontab /current_cron && \
    rm /current_cron 

EXPOSE 80
CMD /usr/sbin/cron
