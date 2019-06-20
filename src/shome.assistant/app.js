const record = require('node-record-lpcm16');
const Detector = require('snowboy').Detector;
const Models = require('snowboy').Models;
const config = require('./config');
const dialogflow = require('dialogflow');
const pump = require('pump');
const through2 = require('through2');

const projectId = process.env.Dialogflow__ProjectId || config.dialogflow.projectId;
const sessionId = "todo-gen-session";
// Instantiates a session client
const sessionClient = new dialogflow.SessionsClient();
// The path to the local file on which to perform speech recognition, e.g.
// /path/to/audio.raw const filename = '/path/to/audio.raw';

// The encoding of the audio file, e.g. 'AUDIO_ENCODING_LINEAR_16'
 const encoding = 'AUDIO_ENCODING_LINEAR_16';

// The sample rate of the audio file in hertz, e.g. 16000
 const sampleRateHertz = 16000;

// The BCP-47 language code to use, e.g. 'en-US'
const languageCode = 'ru-RU';
const sessionPath = sessionClient.sessionPath(projectId, sessionId);

const initialStreamRequest = {
  session: sessionPath,
  queryParams: {
    session: sessionClient.sessionPath(projectId, sessionId),
  },
  queryInput: {
    audioConfig: {
      audioEncoding: encoding,
      sampleRateHertz: sampleRateHertz,
      languageCode: languageCode,
    },
    singleUtterance: true,
  },
};

// Create a stream for the streaming request.
const detectStream = sessionClient
  .streamingDetectIntent()
  .on('error', console.error)
  .on('data', data => {
    if (data.recognitionResult) {
      console.log(
        `Intermediate transcript: ${data.recognitionResult.transcript}`
      );
    } else {
      console.log(`Detected intent:`);
      logQueryResult(sessionClient, data.queryResult);
    }
  });

  // Write the initial stream request to config for audio input.
detectStream.write(initialStreamRequest);
console.log('snow');

//snowboy:

const models = new Models();

models.add({
  file: process.env.Model__File || config.model.file,
  sensitivity: process.env.Model__Sensitivity || config.model.sensitivity,
  hotwords : process.env.Model__Hotwords || config.model.hotwords
});

const detector = new Detector({
  resource: "resources/common.res",
  models: models,
  audioGain: 2.0,
  applyFrontend: true
});

detector.on('silence', function () {
  console.log('silence');
});

detector.on('sound', function (buffer) {
  // <buffer> contains the last chunk of the audio that triggers the "sound"
  // event. It could be written to a wav stream.
  console.log('sound');
});

detector.on('error', function () {
  console.log('error');
});

detector.on('hotword', function (index, hotword, buffer) {
  // <buffer> contains the last chunk of the audio that triggers the "hotword"
  // event. It could be written to a wav stream. You will have to use it
  // together with the <buffer> in the "sound" event if you want to get audio
  // data after the hotword.
  console.log(buffer);
  console.log('hotword', index, hotword);
   
  mic.unpipe(detector);

  mic.unpipe(detectStream);
  mic.pipe(detectStream);
  // pump(
  //   mic,
  //   // Format the audio stream into the request format.
  //   through2.obj((obj, _, next) => {
  //     next(null, {inputAudio: obj});
  //   }),
  //   detectStream
  // );
});

const mic = record.start({
  threshold: 0,
  verbose: true
});

mic.pipe(detector);

