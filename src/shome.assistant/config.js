/**
 * Created by user on 02.10.2015.
 */
var config = {};

config.model = {
    file: "resources/models/Alexa.pmdl",
    // sensitivity: 0.448,
    sensitivity: 0.40,
    hotwords: 'Alexa'
};

config.dialogflow = {
    projectId: '***REMOVED***'
};

module.exports = config;
