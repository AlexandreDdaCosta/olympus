var bodyParser = require('body-parser');
var express = require('express');
var fs = require('fs');
var process = require('process');
var util = require('util');

var logdir = '/var/log/node/';
var access = fs.createWriteStream(logdir + 'access.log', { flags: 'a' });
var error = fs.createWriteStream(logdir + 'error.log', { flags: 'a' });
process.stdout.write = access.write.bind(access);
process.stderr.write = error.write.bind(error);
console.log = function () {
  var now = new Date();
  process.stdout.write(now.toJSON() + ' ' + util.format.apply(null, arguments) + '\n');
}
console.error = function () {
  var now = new Date();
  process.stderr.write(now.toJSON() + ' ' + util.format.apply(null, arguments) + '\n');
}

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