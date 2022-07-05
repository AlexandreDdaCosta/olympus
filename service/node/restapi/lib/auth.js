const restapiModel = require('../api/models/restapi');
const argon2 = require('argon2');
const config = require('config');
const fs = require('fs');
const hashing_config = { parallelism: config.get('argon2.parallelism'), memoryCost: config.get('argon2.memory_cost'), timeCost: config.get('argon2.time_cost') }
const jwt = require('jsonwebtoken');

async function createTokens(username) {
  return {
    access_token_expiration: parseInt(new Date().getTime()/1000) + 900,
    access_token: jwt.sign({ username: username }, fs.readFileSync(config.get('restapi.access_token_secret_file'), 'utf8'), { expiresIn: '15m' }),
    refresh_token_expiration: parseInt(new Date().getTime()/1000) + 86400,
    refresh_token: jwt.sign({ username: username }, fs.readFileSync(config.get('restapi.refresh_token_secret_file'), 'utf8'), { expiresIn: 86400 })
  };
}

async function passwordUserMatch(username, password) {
  user = await restapiModel.findByUsername(username)
  if (! user) {
    return false;
  }
  let hashed_password = user['Password'];
  if (await argon2.verify(hashed_password, password, hashing_config)) {
    return user;
  }
  return false;
}

module.exports = { createTokens, passwordUserMatch };
