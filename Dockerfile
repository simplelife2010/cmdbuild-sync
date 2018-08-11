FROM python:3.7.0-stretch

LABEL maintainer="bruno.vetter@deutschebahn.com"

ENV APPLICATION_NAME cmdbuild-sync
ENV INSTALLATION_DIR /usr/local/bin/${APPLICATION_NAME}
ENV CONFIG_DIR /etc/${APPLICATION_NAME}

RUN pip install pychef==0.3.0 && \
    pip install psycopg2==2.7.5 && \
    mkdir -p ${INSTALLATION_DIR} && \
	mkdir -p ${CONFIG_DIR}
	
COPY ${APPLICATION_NAME}.py ${INSTALLATION_DIR}/
COPY ${APPLICATION_NAME}.pem ${CONFIG_DIR}/