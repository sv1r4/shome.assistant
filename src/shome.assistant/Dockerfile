FROM ubuntu:18.04 AS base
RUN apt-get update && apt-get install -y curl \
   libasound2-dev \
   libsndfile-dev \
   portaudio19-dev \
   python3-pyaudio \
   software-properties-common
RUN add-apt-repository -y ppa:deadsnakes/ppa

ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt-get install -y python3.9 \
  python3.9-dev \
  python3-pip \
  python3.9-distutils
   
WORKDIR /app
RUN python3.9 -m pip install --ignore-installed --upgrade \
    setuptools \
    pip \
    six \
    distlib
RUN python3.9 -m pip install --ignore-installed --upgrade \
  pyaudio \
  soundfile \
  numpy \
  dialogflow \
  simpleaudio \
  paho-mqtt \
  google-cloud-datastore

FROM base as final
RUN apt-get update && apt-get install -y curl \
   sox
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/service_key.json
ENV LANG=C.UTF-8
ENV SENSIVITY=1
#ENV KEYWORD_FILE_PATHS=resources/keyword_files/linux/alexa_linux_compressed.ppn
ENV KEYWORD_FILE_PATHS=resources/keyword_files/linux/alexa_linux.ppn
ENV MODEL_FILE_PATH=./lib/common/porcupine_params.pv
COPY . .
CMD python3.9 app.py --keyword_file_paths $KEYWORD_FILE_PATHS \
   --model_file_path $MODEL_FILE_PATH \
   --sensitivity $SENSIVITY \
   --project_id $PROJECT_ID \
   --mqtt_host $MQTT_HOST \
   --mqtt_port $MQTT_PORT