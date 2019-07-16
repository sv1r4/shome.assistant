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
  numpy \
  dialogflow \
  simpleaudio

FROM base as final
RUN apt-get update && apt-get install -y curl \
   sox
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/df_key.json
ENV LANG=C.UTF-8
ENV SENSIVITY=1
ENV KEYWORD_FILE_PATHS=resources/keyword_files/linux/alexa_linux_compressed.ppn
#ENV KEYWORD_FILE_PATHS=resources/keyword_files/linux/alexa_linux.ppn
ENV MODEL_FILE_PATH=./lib/common/porcupine_compressed_params.pv
#ENV MODEL_FILE_PATH=./lib/common/porcupine_params.pv
COPY . .
CMD python3 app.py --keyword_file_paths $KEYWORD_FILE_PATHS \
   --model_file_path $MODEL_FILE_PATH \
   --sensitivity $SENSIVITY \
   --project_id $PROJECT_ID