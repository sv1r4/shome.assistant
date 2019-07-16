# encoding=utf8
import sys

#sys.setdefaultencoding('utf8')

import argparse
import os
import platform
import struct
import subprocess

import time
from datetime import datetime
from threading import Thread

from six.moves import queue

import simpleaudio as sa
import wave
#from Tkinter import *
#import tkSnack

import numpy as np
import pyaudio
import soundfile

import dialogflow_v2 as dialogflow

sys.path.append(os.path.join(os.path.dirname(__file__), './binding/python'))

from porcupine import Porcupine


class ShomeAssistant(Thread):
    """
    Demo class for wake word detection (aka Porcupine) library. It creates an input audio stream from a microphone,
    monitors it, and upon detecting the specified wake word(s) prints the detection time and index of wake word on
    console. It optionally saves the recorded audio into a file for further review.
    This is the non-blocking version that uses the callback function of PyAudio.
    """

    def __init__(
            self,
            library_path,
            model_file_path,
            keyword_file_paths,
            project_id,
            sensitivity=0.6,
            input_device_index=None):

        super(ShomeAssistant, self).__init__()

        self._library_path = library_path
        self._model_file_path = model_file_path
        self._keyword_file_paths = keyword_file_paths
        self._sensitivity = float(sensitivity)
        self._input_device_index = input_device_index
        self._wake_sound_file = "./resources/sounds/med_ui_wakesound_touch.wav"
        self._project_id = project_id
     
    _AUDIO_DEVICE_INFO_KEYS = ['index', 'name', 'defaultSampleRate', 'maxInputChannels']

#todo init in constructor
    _porcupine = None
    _pa = None
    _audio_stream = None
    _isHotwordDetect = False
    _isIntentDetect = False
    _buff = queue.Queue()
    _session_counter = 0
    _hotword_counter = 0
    _is_playing = False


    def stopDetectHotword(self):
        print("stop hotword detect")
        self._isHotwordDetect = False
        try:            
            if self._audio_stream is not None:
              # self._audio_stream.stop_stream()
               self._audio_stream.close()
            if self._pa is not None:
                self._pa.terminate()
        
        except:
            print("stream error")
    
    def stopDetectIntent(self):
        print("stop intent detect")
        self._isIntentDetect = False
        try:
            if self._audio_stream is not None:
                self._audio_stream.stop_stream()
                self._audio_stream.close()                                        
            if self._pa is not None:
                self._pa.terminate()
        except:
            print("stream error")

    def playSound(self, file, isSync = True):
        if self._is_playing:
            print("already playing")
            return
        try:
            self._is_playing = True
            wave_obj = sa.WaveObject.from_wave_file(file)
            play_obj = wave_obj.play()
            if isSync:
                play_obj.wait_done()
        
        except:
            print("error playback")
        self._is_playing = False

    def playSoundResponse(self, filename):
        if self._is_playing:
            print("already playing")
            return
        try:
            self._is_playing = True
            args = ("play", filename)
            #play in background
            #subprocess.Popen(args, stdout=subprocess.PIPE)
            #Or just:
            #args = "bin/bar -c somefile.xml -d text.txt -r aString -f anotherString".split()
            popen = subprocess.Popen(args, stdout=subprocess.PIPE)
            popen.wait()
            output = popen.stdout.read()
            print(output)
          
        
        except error:
            print(error)
        self._is_playing = False 

    def playSoundResponseBask(self, filename):
        if self._is_playing:
            print("already playing")
            return
        try:
            self._is_playing = True

            # Set chunk size of 1024 samples per data frame
            chunk = 1024  

            # Open the sound file 
            wf = wave.open(filename, 'rb')

            # Create an interface to PortAudio
            p = pyaudio.PyAudio()

            # Open a .Stream object to write the WAV file to
            # 'output = True' indicates that the sound will be played rather than recorded
            stream = p.open(format = p.get_format_from_width(wf.getsampwidth()),
                            channels = wf.getnchannels(),
                            rate = wf.getframerate(),
                            output = True)

            # Read data in chunks
            data = wf.readframes(chunk)

            # Play the sound by writing the audio data to the stream
            while len(data) > 0:
                stream.write(data)
                data = wf.readframes(chunk)

            # Close and terminate the stream
            stream.stop_stream()
            stream.close()
            p.terminate()
        
        except:
            print("play error")
        self._is_playing = False 


    def runDetectIntent(self, session_id):
        print("run detect intent")
        self._isIntentDetect = True

        session_client = dialogflow.SessionsClient()
        audio_encoding = dialogflow.enums.AudioEncoding.AUDIO_ENCODING_LINEAR_16
        sample_rate_hertz = 16000
        language_code = 'ru-RU'
        session_id = '{}'.format(session_id)
        print("session #{}".format(session_id))
        endpointing_file = "./resources/sounds/med_ui_endpointing.wav"

        session_path = session_client.session_path(self._project_id, session_id)
        print('Session path: {}\n'.format(session_path))
      
        def _audio_callback_intent(in_data, frame_count, time_info, status):
            #print("audio callback frame_count={0} status={1}".format(frame_count, status))            
            if not self._is_playing:
                self._buff.put(in_data)            
            return None, pyaudio.paContinue

            
        try:
            num_channels = 1
            audio_format = pyaudio.paInt16
            frame_length = 4096

            audio_config = dialogflow.types.InputAudioConfig(
            audio_encoding=audio_encoding, language_code=language_code,
            sample_rate_hertz=sample_rate_hertz)
           
            
            self._pa = pyaudio.PyAudio()
            self._audio_stream = self._pa.open(
                rate=sample_rate_hertz,
                channels=num_channels,
                format=audio_format,
                input=True,
                frames_per_buffer=frame_length,
                input_device_index=self._input_device_index,
                stream_callback=_audio_callback_intent)

            self._audio_stream.start_stream()

            print("Waiting for command ...\n")

            def request_generator(audio_config):
                query_input = dialogflow.types.QueryInput(audio_config=audio_config)
                output_audio_config = dialogflow.types.OutputAudioConfig(
                    audio_encoding=dialogflow.enums.OutputAudioEncoding.OUTPUT_AUDIO_ENCODING_LINEAR_16)


                # The first request contains the configuration.
                yield dialogflow.types.StreamingDetectIntentRequest(
                    session=session_path, query_input=query_input,
                    single_utterance=True,
                    output_audio_config=output_audio_config)
                

                while True:
                    chunk = self._buff.get()
                    if chunk is None:
                        print("chunk none")
                        return
                    if not self._isIntentDetect:
                        print("done intent")
                        return
                    yield dialogflow.types.StreamingDetectIntentRequest(input_audio=chunk)  
                

                         
            requests = request_generator(audio_config)
            
            
            responses = session_client.streaming_detect_intent(requests)

            print('=' * 20)
            isEndConversation = True
            for response in responses:
                transcript = response.recognition_result.transcript
               
                print("intermediate transcript {0}".format(transcript))
               # print('Stream response reognition result {0}'.format(response.recognition_result))
                if response.recognition_result.is_final:
                    self.playSound(endpointing_file, False)
                    self._isIntentDetect = False
                intent = response.query_result.intent.display_name 
                if intent is not None and intent != "":
                    print("intent {0}".format(intent    ))
                if response.output_audio is not None and len(response.output_audio) > 0:
                    print("got audio response")
                    #self.playSoundResponse(response.output_audio)
                    
                    wav_file = 'output.wav'
                    with open(wav_file, 'wb') as out:
                        out.write(response.output_audio)  

                    self.playSoundResponse(wav_file)
                
            self.stopDetectIntent()   
           
            if isEndConversation:
                print('end conversation')                
                self.runDetectHotword()
            else:      
                self.playSound(self._wake_sound_file)          
                print('conversation continue')
                self.runDetectIntent(self._session_counter)


           
        except KeyboardInterrupt:
            print('stopping ...')
        finally:
            if self._audio_stream is not None:
                self._audio_stream.stop_stream()
                self._audio_stream.close()

            # if self._pa is not None:
            #     self._pa.terminate()

            # delete Porcupine last to avoid segfault in callback.
            if self._porcupine is not None:
                self._porcupine.delete()
            
     
        # # Note: The result from the last response is the final transcript along
        # # with the detected content.
        # query_result = response.query_result

        # print('=' * 20)
        # print('Query text: {}'.format(query_result.query_text))
        # print('Detected intent: {} (confidence: {})\n'.format(
        #     query_result.intent.display_name,
        #     query_result.intent_detection_confidence))
        # print('Fulfillment text: {}\n'.format(
        #     query_result.fulfillment_text))



    def runDetectHotword(self):
        self._hotword_counter += 1
        print("run detect hotword #{}".format(self._hotword_counter))
        self._isHotwordDetect = True
        num_keywords = len(self._keyword_file_paths)

        keyword_names =\
            [os.path.basename(x).strip('.ppn').strip('_compressed').split('_')[0] for x in self._keyword_file_paths]

        def _audio_callback(in_data, frame_count, time_info, status):
            if frame_count >= self._porcupine.frame_length:
                pcm = struct.unpack_from("h" * self._porcupine.frame_length, in_data)
                result = self._porcupine.process(pcm)
                if num_keywords == 1 and result:
                    print('[%s] detected keyword' % str(datetime.now()))    
                    self.playSound(self._wake_sound_file, False)   
                    self.stopDetectHotword()                    
                    self._session_counter+=1
                    self.runDetectIntent(self._session_counter)
               # elif num_keywords > 1 and result >= 0:
               #     print('[%s] detected %s' % (str(datetime.now()), keyword_names[result]))
                    # or add it here if you use multiple keywords
               #     self.stopDetectHotword()
                   # self.runDetectHotword()

                
            return None, pyaudio.paContinue

        
        sample_rate = None
        try:
            self._porcupine = Porcupine(
                library_path=self._library_path,
                model_file_path=self._model_file_path,
                keyword_file_paths=self._keyword_file_paths,
                sensitivities=[self._sensitivity] * num_keywords)
            print("purcipine sensivity {}".format(self._sensitivity))
            sample_rate = self._porcupine.sample_rate
            num_channels = 1
            audio_format = pyaudio.paInt16
            frame_length = self._porcupine.frame_length
            
            self._pa = pyaudio.PyAudio()
            self._audio_stream = self._pa.open(
                rate=sample_rate,
                channels=num_channels,
                format=audio_format,
                input=True,
                frames_per_buffer=frame_length,
                input_device_index=self._input_device_index,
                stream_callback=_audio_callback)

            self._audio_stream.start_stream()

            # print("Started porcupine with following settings:")
            # if self._input_device_index:
            #     print("Input device: %d (check with --show_audio_devices_info)" % self._input_device_index)
            # else:
            #     print("Input device: default (check with --show_audio_devices_info)")
            # print("Sample-rate: %d" % sample_rate)
            # print("Channels: %d" % num_channels)
            # print("Format: %d" % audio_format)
            # print("Frame-length: %d" % frame_length)
            print("Keyword file(s): %s" % self._keyword_file_paths)
            print("Waiting for keywords ...\n")

            while True:
                #print("loop")
                #if not self._isHotwordDetect and not self._isIntentDetect:                                        
                   # self.playSound(self._wake_sound_file)
                    
                time.sleep(0.1)

        except KeyboardInterrupt:
            print('stopping ...')
        finally:
            if self._audio_stream is not None:
                self._audio_stream.stop_stream()
                self._audio_stream.close()

            if self._pa is not None:
                self._pa.terminate()

            # delete Porcupine last to avoid segfault in callback.
            if self._porcupine is not None:
                self._porcupine.delete()

           

    def run(self):
        self.runDetectHotword()
       # self.runDetectIntent(self._session_counter)
 

def _default_library_path():
    system = platform.system()
    machine = platform.machine()

    if system == 'Darwin':
        return os.path.join(os.path.dirname(__file__), './lib/mac/%s/libpv_porcupine.dylib' % machine)
    elif system == 'Linux':
        if machine == 'x86_64' or machine == 'i386':
            return os.path.join(os.path.dirname(__file__), './lib/linux/%s/libpv_porcupine.so' % machine)
        else:
            raise Exception('cannot autodetect the binary type. Please enter the path to the shared object using --library_path command line argument.')
    elif system == 'Windows':
        if platform.architecture()[0] == '32bit':
            return os.path.join(os.path.dirname(__file__), '.\\lib\\windows\\i686\\libpv_porcupine.dll')
        else:
            return os.path.join(os.path.dirname(__file__), '.\\lib\\windows\\amd64\\libpv_porcupine.dll')
    raise NotImplementedError('Porcupine is not supported on %s/%s yet!' % (system, machine))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--keyword_file_paths',
        help='comma-separated absolute paths to keyword files',
        type=str)

    parser.add_argument(
        '--library_path',
        help="absolute path to Porcupine's dynamic library",
        type=str)

    parser.add_argument(
        '--model_file_path',
        help='absolute path to model parameter file',
        type=str,
        default=os.path.join(os.path.dirname(__file__), './lib/common/porcupine_params.pv'))

    parser.add_argument('--sensitivity', help='detection sensitivity [0, 1]', default=0.5)
    parser.add_argument('--input_audio_device_index', help='index of input audio device', type=int, default=None)

    parser.add_argument('--project_id', help="google dialogflow project id", type=str)

    args = parser.parse_args()

    if not args.keyword_file_paths:
        raise ValueError('keyword file paths are missing')
    if not args.project_id:
        raise ValueError('google project id is missing')

    ShomeAssistant(
        library_path=args.library_path if args.library_path is not None else _default_library_path(),
        model_file_path=args.model_file_path,
        keyword_file_paths=[x.strip() for x in args.keyword_file_paths.split(',')],
        sensitivity=args.sensitivity,
        input_device_index=args.input_audio_device_index,
        project_id=args.project_id
    ).run()
