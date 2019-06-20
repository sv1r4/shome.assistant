FROM ubuntu:18.04 AS base
RUN apt-get update && apt-get install -y curl
RUN curl -sL https://deb.nodesource.com/setup_12.x | bash -
RUN apt-get update && apt-get install -y \
  nodejs \
  sox \
  libatlas-base-dev
WORKDIR /app


FROM base as node-deps
RUN apt-get update && apt-get install -y git \
   libmagic-dev \
   libatlas-base-dev \
   make \
   g++ \
   node-gyp \
   node-pre-gyp
COPY package.json .
RUN npm install --only=production 

RUN git clone https://github.com/Kitt-AI/snowboy.git
WORKDIR /app/snowboy
RUN npm install
RUN ./node_modules/node-pre-gyp/bin/node-pre-gyp clean configure build
RUN npm run prepublish 

FROM base as final
COPY --from=node-deps /app/node_modules ./node_modules
COPY --from=node-deps /app/snowboy ./node_modules/snowboy
COPY ./secrets ./secrets
COPY . .
CMD node app.js