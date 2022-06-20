const bodyParser = require('body-parser');
const config = require('config');
const cors = require('cors');
const express = require('express');
const fs = require('fs');
const helmet = require('helmet');
const process = require('process');
const util = require('util');

const access = fs.createWriteStream(config.get('log.access'), { flags: 'a' });
const error = fs.createWriteStream(config.get('log.error'), { flags: 'a' });
process.stdout.write = access.write.bind(access);
process.stderr.write = error.write.bind(error);
console.result = function (code, url, message) {
  var now = new Date();
  let string = now.toLocaleString(config.get('locale.language'), { timeZone: config.get('locale.timezone') }).replace(/\s/g,'') + ' ' + code.toString() + ' ' + url;
  if (! message || message.length == 0) {
    string = string + '\n';
  }
  else {
    string = string + ' ' + message +'\n';
  }
  process.stdout.write(string);
}
console.log = function () {
  var now = new Date();
  let string = now.toLocaleString(config.get('locale.language'), { timeZone: config.get('locale.timezone') }).replace(/\s/g,'');
  process.stdout.write(string + ' ' + util.format.apply(null, arguments) + '\n');
}
console.error = function () {
  var now = new Date();
  let string = now.toLocaleString(config.get('locale.language'), { timeZone: config.get('locale.timezone') }).replace(/\s/g,'');
  process.stderr.write(string + ' ' + util.format.apply(null, arguments) + '\n');
}

let data = util.format('%s', process.pid);
fs.writeFile(config.get('pidfile'), util.format('%s', process.pid), (err) => {
  if (err)
    return console.error(err);
  else
    console.log(util.format('PID written successfully [%s]', process.pid));
});

require('mongo_connect').initPool();
require('redis_connect').initPool();

process.env.access_token_secret = fs.readFileSync(config.get('restapi.access_token_secret_file'), 'utf8');
process.env.refresh_token_secret = fs.readFileSync(config.get('restapi.refresh_token_secret_file'), 'utf8');

const app = express();
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(helmet());
app.use(cors());

require("./routes")(app);
app.listen(config.get('server.port'));
console.log('node.js REST API listening on port ' + config.get('server.port'));
