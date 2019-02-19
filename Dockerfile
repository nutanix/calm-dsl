FROM alpine:edge

RUN apk update && apk add --no-cache build-base musl-dev python3 python3-dev py3-zmq py3-libxml2 py3-lxml

RUN pip3 install --no-cache-dir --upgrade pip setuptools

COPY gui-requirements.txt /gui-requirements.txt
RUN pip3 install -r /gui-requirements.txt

# PEP 370 (Using user env instead of virtualenv)
WORKDIR /root
RUN mkdir -p `python3 -m site --user-site`
COPY requirements.txt /requirements.txt
RUN pip3 install --user -r /requirements.txt

# reduce image size by cleaning up the build packages
RUN apk del build-base musl-dev python3-dev

EXPOSE 8888
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--allow-root"]
