FROM python:3.6.5-stretch

ENV http_proxy http://proxy-chain.intel.com:911
ENV https_proxy http://proxy-chain.intel.com:911

RUN mkdir /vRAclient

COPY docker /vRAclient/docker

RUN mkdir -p /etc/ssl/certs
RUN cp /vRAclient/docker/cabundle.pem /etc/ssl/certs/cabundle.pem
RUN cp /vRAclient/docker/apt.conf /etc/apt/apt.conf

COPY . /vRAclient/

WORKDIR /vRAclient

RUN ./build.sh no_venv
RUN pyb install_dependencies
RUN pyb install

# ENV http_proxy=
# ENV https_proxy=

WORKDIR /vRAclient
CMD echo 'DONE'
