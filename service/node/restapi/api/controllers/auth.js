const auth = require('../../lib/auth.js');
const config = require('config');
const redisConnection = require('redis_connect');
const { validationResult } = require('express-validator');

const login = async (request, result, next) => {
  let tokens;

  try {
    // Suppress sensitive login information in logs and returned messages
    const myValidationResult = validationResult.withDefaults({
      formatter: error => {
        return {
          location: error.location,
          msg: error.msg,
          param: error.param
        };
      },
    });
    const errors = myValidationResult(request);
    if (! errors.isEmpty()) {
      console.result(400,request.url,JSON.stringify(errors.array()));
      return result.status(400).json({
        message: 'Login failed.',
        errors: errors.array(),
      });
    }
  } 
  catch (err) {
    next(err);
  }

  try {
    if (! await auth.passwordUserMatch(request.body.username,request.body.password)) {
      console.result(401,request.url);
      return result.status(401).json({ message: 'Access denied.' });
    }
    tokens = await auth.createTokens(request.body.username);
    let poolConnection = redisConnection.getInstance();
    let resourcePromise = poolConnection.acquire();
    resourcePromise
      .then(function(client) {
        client.hSet('user_node:auth:'+request.body.username, "date", Date.now());
        client.hSet('user_node:auth:'+request.body.username, "access_token", tokens.access_token);
        client.hSet('user_node:auth:'+request.body.username, "refresh_token", tokens.refresh_token);
        poolConnection.release(client);
      })
      .catch(function(err) {
        next(err);
      });
  }
  catch (err) {
    console.result(500,request.url,err);
    return result.status(500).json({ message: 'Internal server error.' });
  }

  console.result(200,request.url);
  return result.status(200).json({ message: 'Login successful.', access_token: tokens.access_token, refresh_token: tokens.refresh_token });
};
const logout = async (request, result, next) => {
  console.result(200,request.url);
  return result.status(200).json({ message: 'Logout successful.' });
};
const ping = async (request, result, next) => {
  console.result(200,request.url);
  return result.status(200).json({ message: 'Give me a ping, Vasili. One ping only, please.' });
};
const refresh = async (request, result, next) => {
  try {
    const errors = validationResult(request);
    if (! errors.isEmpty()) {
      console.result(400,request.url,JSON.stringify(errors.array()));
      return result.status(400).json({
        message: 'Refresh failed.',
        errors: errors.array(),
      });
    }
    if (request.body.username != request.user) {
      console.result(401,request.url);
      return result.status(401).json({ message: 'Access denied.' });
    }
  } 
  catch (err) {
    console.result(500,request.url,err);
    return result.status(500).json({ message: 'Internal server error.' });
  }

  console.result(200,request.url);
  return result.status(200).json({ message: 'Refresh successful.' });
};
module.exports = { login, logout, ping, refresh };
