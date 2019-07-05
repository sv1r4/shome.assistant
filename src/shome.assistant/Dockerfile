FROM ubuntu:18.04 AS base
RUN apt-get update && apt-get install -y curl \
   libasound2-dev \
   libsndfile-dev \
   portaudio19-dev \
   python3 \
   python3-pip
WORKDIR /app
RUN pip3 install pyaudio \
  soundfile \
  numpy
# RUN curl -sL https://deb.nodesource.com/setup_12.x | bash -
# RUN apt-get update && apt-get install -y \
#   nodejs \
#   sox \
#   libatlas-base-dev \
#   mplayer
# WORKDIR /app


# FROM base as node-deps
# RUN apt-get update && apt-get install -y git \
#    libmagic-dev \
#    libatlas-base-dev \
#    make \
#    g++ \
#    node-gyp \
#    node-pre-gyp
# RUN git clone https://github.com/Kitt-AI/snowboy.git
# WORKDIR /app/snowboy
# RUN npm install
# RUN ./node_modules/node-pre-gyp/bin/node-pre-gyp clean configure build
# RUN npm run prepublish 

# WORKDIR /app
# COPY package.json .
# RUN npm install --only=production 

FROM base as final
# COPY --from=node-deps /app/node_modules ./node_modules
# COPY --from=node-deps /app/snowboy ./node_modules/snowboy
COPY . .
CMD python3 app.py