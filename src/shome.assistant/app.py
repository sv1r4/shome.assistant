# encoding=utf8
import sys

#sys.setdefaultencoding('utf8')

import argparse
import os
import platform
import struct

import time
from datetime import datetime
from threading import Thread

from six.moves import queue

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
            sensitivity=0.6,
            input_device_index=None):

        super(ShomeAssistant, self).__init__()

        self._library_path = library_path
        self._model_file_path = model_file_path
        self._keyword_file_paths = keyword_file_paths
        self._sensitivity = float(sensitivity)
        self._input_device_index = input_device_index
            
        
            

    _AUDIO_DEVICE_INFO_KEYS = ['index', 'name', 'defaultSampleRate', 'maxInputChannels']

#todo init in constructor
    _porcupine = None
    _pa = None
    _audio_stream = None
    _isHotwordDetect = False
    _isIntentDetect = False
    _buff = queue.Queue()


    def stopDetectHotword(self):
        print("stop hotword detect")
        self._isHotwordDetect = False
        try:
            if self._audio_stream is not None:
               # self._audio_stream.stop_stream()
               self._audio_stream.close()
            #if self._pa is not None:
            #    self._pa.terminate()
        
        except:
            print("stream error")
        finally:
            self.runDetectIntent()
    
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
        finally:
            self.runDetectHotword()
    
    def runDetectIntent(self):
        print("run detect intent")
        self._isIntentDetect = True

        session_client = dialogflow.SessionsClient()
        audio_encoding = dialogflow.enums.AudioEncoding.AUDIO_ENCODING_LINEAR_16
        sample_rate_hertz = 16000
        language_code = 'ru-RU'
        session_id = '1'
        project_id = '***REMOVED***'

        session_path = session_client.session_path(project_id, session_id)
        print('Session path: {}\n'.format(session_path))
      
        def _audio_callback_intent(in_data, frame_count, time_info, status):
            print("audio callback frame_count={0} status={1}".format(frame_count, status))
            self._buff.put(in_data)            
            return None, pyaudio.paContinue

            
        try:
            num_channels = 1
            audio_format = pyaudio.paInt16
            frame_length = 4096 #self._porcupine.frame_length

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

            print("Started detect intent with following settings:")
            if self._input_device_index:
                print("Input device: %d (check with --show_audio_devices_info)" % self._input_device_index)
            else:
                print("Input device: default (check with --show_audio_devices_info)")
            print("Sample-rate: %d" % sample_rate_hertz)
            print("Channels: %d" % num_channels)
            print("Format: %d" % audio_format)
            print("Frame-length: %d" % frame_length)
            print("Waiting for command ...\n")

            def request_generator(audio_config):
                query_input = dialogflow.types.QueryInput(audio_config=audio_config)

                # The first request contains the configuration.
                yield dialogflow.types.StreamingDetectIntentRequest(
                    session=session_path, query_input=query_input, single_utterance=True)

                while True:
                    #try:
                        chunk = self._buff.get()
                        if chunk is None:
                            print("chunk none")
                            return
                        if not self._isIntentDetect:
                            print("done intent")
                            return
                        print("stream chunk")
                        yield dialogflow.types.StreamingDetectIntentRequest(
                            input_audio=chunk)  
                    #except queue.Empty:
                      #  print("queue empty")
                      #  break

                         
            requests = request_generator(audio_config)
            responses = session_client.streaming_detect_intent(requests)

            print('=' * 20)
            for response in responses:
                print('Stream response {0}'.format(response))
                if response.recognition_result.is_final:
                    self._isIntentDetect = False

            self.stopDetectIntent()    

           
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
        print("run detect hotword")
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
                    self.stopDetectHotword()
                    # add your own code execution here ... it will not block the recognition
                elif num_keywords > 1 and result >= 0:
                    print('[%s] detected %s' % (str(datetime.now()), keyword_names[result]))
                    # or add it here if you use multiple keywords
                    self.stopDetectHotword()

                
            return None, pyaudio.paContinue

        
        sample_rate = None
        try:
            self._porcupine = Porcupine(
                library_path=self._library_path,
                model_file_path=self._model_file_path,
                keyword_file_paths=self._keyword_file_paths,
                sensitivities=[self._sensitivity] * num_keywords)

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

            print("Started porcupine with following settings:")
            if self._input_device_index:
                print("Input device: %d (check with --show_audio_devices_info)" % self._input_device_index)
            else:
                print("Input device: default (check with --show_audio_devices_info)")
            print("Sample-rate: %d" % sample_rate)
            print("Channels: %d" % num_channels)
            print("Format: %d" % audio_format)
            print("Frame-length: %d" % frame_length)
            print("Keyword file(s): %s" % self._keyword_file_paths)
            print("Waiting for keywords ...\n")

            while True:
                if not self._isHotwordDetect:
                    break
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
        #self.runDetectHotword()
        self.runDetectIntent()

    @classmethod
    def show_audio_devices_info(cls):
        """ Provides information regarding different audio devices available. """

        pa = pyaudio.PyAudio()

        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            print(', '.join("'%s': '%s'" % (k, str(info[k])) for k in cls._AUDIO_DEVICE_INFO_KEYS))

        pa.terminate()


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

    parser.add_argument('--keyword_file_paths', help='comma-separated absolute paths to keyword files', type=str)

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

  

    parser.add_argument('--show_audio_devices_info', action='store_true')

    args = parser.parse_args()

    if args.show_audio_devices_info:
        ShomeAssistant.show_audio_devices_info()
    else:
        if not args.keyword_file_paths:
            raise ValueError('keyword file paths are missing')

        ShomeAssistant(
            library_path=args.library_path if args.library_path is not None else _default_library_path(),
            model_file_path=args.model_file_path,
            keyword_file_paths=[x.strip() for x in args.keyword_file_paths.split(',')],
            sensitivity=args.sensitivity,
            input_device_index=args.input_audio_device_index
        ).run()