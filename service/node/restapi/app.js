const bodyParser = require('body-parser');
const fs = require('fs');
const process = require('process');
const util = require('util');
const express = require('express');

const logdir = '/var/log/node/';
const access = fs.createWriteStream(logdir + 'access.log', { flags: 'a' });
const error = fs.createWriteStream(logdir + 'error.log', { flags: 'a' });
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
let data = util.format('%s', process.pid);
fs.writeFile("/var/run/node.pid", util.format('%s', process.pid), (err) => {
  if (err)
    return console.error(err);
  else
    console.log(util.format('PID written successfully [%s]', process.pid));
});

const app = express();
const port = 8889;
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

const routes = require('./api/routes');
app.use('/', routes);

app.listen(port);
console.log('node.js REST API listening on port ' + port);
