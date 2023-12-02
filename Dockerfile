FROM python:3.11-slim-bullseye

RUN apt-get update && apt-get install -y \
        build-essential \
        libaio1 \
        libldap2-dev \
        libsasl2-dev \
        libssl-dev \
        python-dev \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /cac
COPY . /cac/
RUN rm -rf /cac/entrypoint.sh

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN pip install -r /cac/REQUIREMENTS.txt

RUN mkdir /data

ENV APP_PORT 5000
ENV APP_DEBUG false
ENV APP_HOST 0.0.0.0
ENV APP_NAME "Edit"
ENV DATABASE_DIR /cac/files/uploads

EXPOSE 5000

ENTRYPOINT ["/entrypoint.sh"]
WORKDIR /cac
CMD ["cac"]
