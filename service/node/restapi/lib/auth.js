const argon2 = require("argon2");
const config = require("config");
const fs = require("fs");

const hashingConfig = {
  parallelism: config.get("argon2.parallelism"),
  memoryCost: config.get("argon2.memory_cost"),
  timeCost: config.get("argon2.time_cost"),
};
const jwt = require("jsonwebtoken");
const restapiModel = require("../api/models/restapi");

async function createTokens(username) {
  return {
    access_token_expiration: parseInt(new Date().getTime() / 1000, 10) + 900,
    access_token: jwt.sign(
      { username },
      fs.readFileSync(config.get("restapi.access_token_secret_file"), "utf8"),
      { expiresIn: "15m" }
    ),
    refresh_token_expiration: parseInt(new Date().getTime() / 1000, 10) + 86400,
    refresh_token: jwt.sign(
      { username },
      fs.readFileSync(config.get("restapi.refresh_token_secret_file"), "utf8"),
      { expiresIn: 86400 }
    ),
  };
}

async function passwordUserMatch(username, password) {
  const user = await restapiModel.findByUsername(username);
  if (!user) {
    return false;
  }
  const hashedPassword = user.Password;
  if (await argon2.verify(hashedPassword, password, hashingConfig)) {
    return user;
  }
  return false;
}

module.exports = { createTokens, passwordUserMatch };
