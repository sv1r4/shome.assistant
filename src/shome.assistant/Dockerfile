FROM ubuntu:18.04 AS base
RUN apt-get update && apt-get install -y \
  nodejs \
  sox \
 # portaudio \
  libatlas-base-dev
WORKDIR /app

FROM base as node-deps
RUN apt-get update && apt-get install -y npm
COPY package.json .
RUN npm set progress=false && npm config set depth 0
RUN npm install --only=production 

FROM base as final
COPY --from=node-deps /app/node_modules ./node_modules
COPY . .
CMD node app.js