const config = require("config");
const cors = require("cors");
const express = require("express");
const fs = require("fs");
const helmet = require("helmet");
const process = require("process");
const util = require("util");

const access = fs.createWriteStream(config.get("log.access"), { flags: "a" });
const error = fs.createWriteStream(config.get("log.error"), { flags: "a" });
process.stdout.write = access.write.bind(access);
process.stderr.write = error.write.bind(error);
console.result = function processResult(res, req) {
  const now = new Date();
  let message = "";
  if (res.locals.statusMessage) {
    message = res.locals.statusMessage;
  } else {
    message = res.statusMessage;
  }
  let user = "?";
  if (req.user) {
    user = req.user;
  }
  const string = `${now
    .toLocaleString(config.get("locale.language"), {
      timeZone: config.get("locale.timezone"),
    })
    .replace(/\s/g, "")} ${res.statusCode} ${user} ${
    req.originalUrl
  } ${message}\n`;
  process.stdout.write(string);
};
console.log = function accessLog(...args) {
  const now = new Date();
  const string = now
    .toLocaleString(config.get("locale.language"), {
      timeZone: config.get("locale.timezone"),
    })
    .replace(/\s/g, "");
  process.stdout.write(`${string} ${util.format.apply(null, args)}\n`);
};
console.error = function errorLog(...args) {
  const now = new Date();
  const string = now
    .toLocaleString(config.get("locale.language"), {
      timeZone: config.get("locale.timezone"),
    })
    .replace(/\s/g, "");
  process.stderr.write(`${string} ${util.format.apply(null, args)}\n`);
};

fs.writeFile(config.get("pidfile"), util.format("%s", process.pid), (err) => {
  if (err) return console.error(err);
  console.log(util.format("PID written successfully [%s]", process.pid));
  return false;
});

// eslint-disable-next-line import/no-unresolved
require("mongo_connect").initPool();
// eslint-disable-next-line import/no-unresolved
require("redis_connect").initPool();

process.env.access_token_secret = fs.readFileSync(
  config.get("restapi.access_token_secret_file"),
  "utf8"
);
process.env.refresh_token_secret = fs.readFileSync(
  config.get("restapi.refresh_token_secret_file"),
  "utf8"
);

const app = express();
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(helmet());
app.use(cors());

require("./routes")(app);

app.listen(config.get("server.port"));
console.log(`node.js REST API listening on port ${config.get("server.port")}`);
