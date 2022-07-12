FROM python:3.7-alpine

# Upgrade to latest pip and install setuptools
RUN pip3 install --no-cache-dir --upgrade pip setuptools

# Alpine is not manylinux compatible, so any package containing C extensions
# must be built from source [PEP 513].
# Add build packages needed to compile from source
ENV BUILD_PACKAGES="\
        build-base \
        openssl-dev \
        libxml2-dev \
        jpeg-dev \
        sqlite-dev \
        ncurses-dev \
	"

# Install build packages for building from source
RUN apk update && apk add --no-cache $BUILD_PACKAGES

# Install calm.dsl requirements
COPY requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt && rm /requirements.txt

# Remove build packages
RUN apk del $BUILD_PACKAGES

# Install calm.dsl
COPY dist/calm.dsl*.whl .
RUN pip3 install --no-cache-dir calm.dsl*.whl && rm calm.dsl*.whl

# Install bash and auto-completion for calm commands
RUN apk add --no-cache bash bash-completion
COPY .bashrc /root/.bashrc
COPY .bash_completion /root/.bash_completion

ARG tag
ENV CALM_DSL_TAG=$tag

CMD ["bash"]
