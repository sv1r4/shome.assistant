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

FROM base as final
COPY . .
CMD python3 app.py --keyword_file_paths resources/keyword_files/linux/alexa_linux.ppn