# Use the smallest Python-capable base image that's easily available.
FROM python:2-alpine

MAINTAINER Jean-Paul Calderone <exarkun@twistedmatrix.com>

# Set up a nice place to dump our source code.
WORKDIR /app

# Get the necessary build dependencies.  These all get leaked into the
# container which is a shame.  Oh well.
RUN apk add --no-cache build-base libffi-dev openssl-dev

# Get all of the source into the image.
COPY . .

# Install it and all its dependencies.
RUN pip install --no-cache-dir .

# Set the kubetop cli program as the entrypoint.  This lets arguments be
# passed by the user without too much trouble.  Just add the to the end of the
# `docker run ...` command.
ENTRYPOINT ["kubetop"]
