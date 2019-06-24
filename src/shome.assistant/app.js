const record = require('node-record-lpcm16');
const Detector = require('snowboy').Detector;
const Models = require('snowboy').Models;
const config = require('./config');
const dialogflow = require('dialogflow');
const pump = require('pump');
const through2 = require('through2');
const {struct} = require('pb-util');
const util = require('util');
const fs = require('fs');

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
    singleUtterance: false,
  },
};

// Create a stream for the streaming request.
const detectStream = sessionClient
  .streamingDetectIntent()
  .on('error', error => {
    console.log(error);
    record.stop();
    detectHotword();
  })
  .on('data', data => {
    if (data.recognitionResult) {
      console.log(
        `Intermediate transcript: ${data.recognitionResult.transcript}`
      );
    } else {
      console.log(`Detected intent:`);
      
      logQueryResult(sessionClient, data.queryResult);

      record.stop();
      detectHotword();
      detectDialogIntent();
    }
  });

console.log('snow');

//snowboy:

const models = new Models();

models.add({
  file: process.env.Model__File || config.model.file,
  sensitivity: process.env.Model__Sensitivity || config.model.sensitivity,
  hotwords : process.env.Model__Hotwords || config.model.hotwords
});

var detector;

//detectDialogIntent();
//detectHotword();
// (async () => {
//   try {      
//     await testTts();
//   } catch (e) {
//     console.log(e);
//       // Deal with the fact the chain failed
//   }
// })();
detectHotword();
record.stop();
detectHotword();

function detectHotword(){
  console.log("detectHotword");


  detector = new Detector({
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
  
  detector.on('error', error=> {
    console.log(error);
  });
  
  detector.on('hotword', function (index, hotword, buffer) {
    // <buffer> contains the last chunk of the audio that triggers the "hotword"
    // event. It could be written to a wav stream. You will have to use it
    // together with the <buffer> in the "sound" event if you want to get audio
    // data after the hotword.
    console.log(buffer);
    console.log('hotword', index, hotword);
    
    record.stop();
    detectDialogIntent();
  });

  var mic = record.start({
    sampleRateHertz: sampleRateHertz,
    threshold: 0, //silence threshold
    recordProgram: 'rec', // Try also "arecord" or "sox"
    silence: '1.0', //seconds of silence before ending
    verbose: true
  });//.pipe(detector);

  pump(mic, detector);
}


 function detectDialogIntent(){
   console.log("detectDialogIntent");
  var mic = record.start({
      sampleRateHertz: sampleRateHertz,
      threshold: 0.5, //silence threshold
      recordProgram: 'rec', // Try also "arecord" or "sox"
      silence: '1.0', //seconds of silence before ending
      verbose: true
    });
   // setTimeout(()=>record.stop(), 10000);
  //  .on('error', error => {console.log(error);})
  //  .pipe(through2.obj((obj, _, next) => {
  //    next(null, {inputAudio: obj});
  //  }))
  //  .pipe(detectStream);

   pump(
     mic,
     // Format the audio stream into the request format.
     through2.obj((obj, _, next) => {
       next(null, {inputAudio: obj});
     }),
     detectStream
   );


  // Write the initial stream request to config for audio input.
  detectStream.write(initialStreamRequest);
  
}

function logQueryResult(sessionClient, result) {
  // Imports the Dialogflow library
  const dialogflow = require('dialogflow');

  // Instantiates a context client
  const contextClient = new dialogflow.ContextsClient();

  console.log(`  Query: ${result.queryText}`);
  console.log(`  Response: ${result.fulfillmentText}`);
  if (result.intent) {
    console.log(`  Intent: ${result.intent.displayName}`);
  } else {
    console.log(`  No intent matched.`);
  }
  //const parameters = JSON.stringify(struct.decode(result.parameters));
  //console.log(`  Parameters: ${parameters}`);
  if (result.outputContexts && result.outputContexts.length) {
    console.log(`  Output contexts:`);
    result.outputContexts.forEach(context => {
      const contextId = contextClient.matchContextFromContextName(context.name);
      const contextParameters = JSON.stringify(
        struct.decode(context.parameters)
      );
      console.log(`    ${contextId}`);
      console.log(`      lifespan: ${context.lifespanCount}`);
      console.log(`      parameters: ${contextParameters}`);
    });
  }
}


async function testTts(){
  const request = {
    session: sessionPath,
    queryInput: {
      text: {
        text: "привет",
        languageCode: languageCode,
      },
    },
    outputAudioConfig: {
      audioEncoding: `OUTPUT_AUDIO_ENCODING_LINEAR_16`,
    },
  };

  var outputFile = "test.wav"
  const responses = await sessionClient.detectIntent(request);
  console.log('Detected intent:');
  const audioFile = responses[0].outputAudio;
  await util.promisify(fs.writeFile)(outputFile, audioFile, 'binary');
  console.log(`Audio content written to file: ${outputFile}`);

}