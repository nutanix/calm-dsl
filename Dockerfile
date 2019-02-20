FROM alpine:edge

# Alpine is not manylinux compatible, so any package containing C extensions
# must be built from source [PEP 513].

# Add required C extensions to packages.
ENV PACKAGES="\
	libxml2 \
	libxslt \
	libzmq \
	python3 \
	"

# Add build packages needed to compile from source
ENV BUILD_PACKAGES="\
	python3-dev \
	build-base \
	musl-dev \
	zeromq-dev \
	libxml2-dev \
	libxslt-dev \
	"

# Install base packages
RUN apk update && apk add --no-cache $PACKAGES

# Upgrade to latest pip and install setuptools
RUN pip3 install --no-cache-dir --upgrade pip setuptools

# Install build packages for building from source
RUN apk add --no-cache $BUILD_PACKAGES

# Install Jupyter requirements for GUI
COPY gui-requirements.txt /gui-requirements.txt
RUN pip3 install --no-cache-dir -r /gui-requirements.txt

# Use root env instead of virtualenv for installing requirements [PEP 370]
WORKDIR /root
RUN mkdir -p `python3 -m site --user-site`
COPY requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt --user

# TODO - Install calm.dsl package to root user-site

# Cleanup
RUN apk del $BUILD_PACKAGES
RUN rm /gui-requirements.txt
RUN rm /requirements.txt

EXPOSE 8888
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--allow-root"]
