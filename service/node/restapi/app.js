var fs = require('fs');
var express = require('express');
var bodyParser = require('body-parser');
var process = require('process');
var util = require('util');

var logdir = '/var/log/node/';
var access = fs.createWriteStream(logdir + 'access.log', { flags: 'a' });
var error = fs.createWriteStream(logdir + 'error.log', { flags: 'a' });
process.stdout.write = access.write.bind(access);
process.stderr.write = error.write.bind(error);

fs.writeFile("/var/run/node.pid", process.pid, function(err) {
    if (err) {
        return console.error(err);
    }
}); 

var app = express();
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
var routes = require('./api/routes');
app.use('/api', routes);
var port = 8889;
app.listen(port);
console.log('node.js REST API listening on port ' + port);
