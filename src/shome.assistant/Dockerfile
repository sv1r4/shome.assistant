FROM ubuntu:18.04 AS base
RUN apt-get update && apt-get install -y curl \
   libasound2-dev \
   libsndfile-dev \
   portaudio19-dev \
   python3 \
   python3-pip \
   ffmpeg \
   libavcodec-extra \
   python-gst-1.0
   
WORKDIR /app
RUN pip3 install pyaudio \
  soundfile \
  numpy \
  dialogflow \
  simpleaudio \
  playsound \
  pydub 

FROM base as final
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/df_key.json
ENV LANG=C.UTF-8
ENV SENSIVITY=1
COPY . .
CMD python3 app.py --keyword_file_paths resources/keyword_files/linux/alexa_linux.ppn --sensitivity $SENSIVITY