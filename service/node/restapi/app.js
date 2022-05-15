const bodyParser = require('body-parser');
const config = require('config');
const express = require('express');
const fs = require('fs');
const process = require('process');
const util = require('util');

//require("mongo_connect").initPool();

const access = fs.createWriteStream(config.get('log.access'), { flags: 'a' });
const error = fs.createWriteStream(config.get('log.error'), { flags: 'a' });
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
fs.writeFile(config.get('pidfile'), util.format('%s', process.pid), (err) => {
  if (err)
    return console.error(err);
  else
    console.log(util.format('PID written successfully [%s]', process.pid));
});

const app = express();
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

const routes = require('./api/routes');
app.use('/', routes);

app.listen(config.get('server.port'));
console.log('node.js REST API listening on port ' + config.get('server.port'));
