const auth = require('../../lib/auth.js');
const config = require('config');
const redisConnection = require('redis_connect');
const { validationResult } = require('express-validator');

const login = async (req, res, next) => {
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
    const errors = myValidationResult(req);
    if (! errors.isEmpty()) {
      console.result(400,req.url,JSON.stringify(errors.array()));
      return res.status(400).json({ message: 'Login failed.', errors: errors.array() });
    }
  } 
  catch (err) {
    next(err);
    console.result(500,req.url,err);
    return res.status(500).json({ message: 'Internal server error.' });
  }

  try {
    if (! await auth.passwordUserMatch(req.body.username,req.body.password)) {
      console.result(401,req.url,'Bad user/password match');
      next();
      return res.status(401).json({ message: 'Access denied.' });
    }
    tokens = await auth.createTokens(req.body.username);
    let poolConnection = redisConnection.getInstance();
    let resourcePromise = poolConnection.acquire();
    resourcePromise
      .then(function(client) {
        client.hSet('user_node:auth:'+req.body.username, "date", Date.now());
        client.hSet('user_node:auth:'+req.body.username, "access_token", tokens.access_token);
        client.hSet('user_node:auth:'+req.body.username, "refresh_token", tokens.refresh_token);
        poolConnection.release(client);
        console.result(200,req.url);
        return res.status(200).json({ message: 'Login successful.', access_token: tokens.access_token, refresh_token: tokens.refresh_token });
      })
      .catch(function(err) {
	next(err);
        console.result(500,req.url,err);
        return res.status(500).json({ message: 'Internal server error.' });
      });
  }
  catch (err) {
    next(err);
    console.result(500,req.url,err);
    return res.status(500).json({ message: 'Internal server error.' });
  }
};
const logout = async (req, res, next) => {
  try {
    let poolConnection = redisConnection.getInstance();
    let resourcePromise = poolConnection.acquire();
    resourcePromise
      .then(function(client) {
        client.del('user_node:auth:'+req.user);
        poolConnection.release(client);
        console.result(200,req.url);
        return res.status(200).json({ message: 'Logout successful.' });
      })
      .catch(function(err) {
	next(err);
        console.result(500,req.url,err);
        return res.status(500).json({ message: 'Internal server error.' });
      });
  } 
  catch (err) {
    console.result(500,req.url,err);
    return res.status(500).json({ message: 'Internal server error.' });
  }
};
const ping = async (req, res, next) => {
  console.result(200,req.url);
  return res.status(200).json({ message: 'Give me a ping, Vasili. One ping only, please.' });
};
const refresh = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (! errors.isEmpty()) {
      console.result(400,req.url,JSON.stringify(errors.array()));
      return res.status(400).json({ message: 'Refresh failed.', errors: errors.array() });
    }
    if (req.body.username != req.user) {
      console.result(401,req.url,'Bad username in body');
      return res.status(401).json({ message: 'Access denied.' });
    }
    tokens = await auth.createTokens(req.body.username);
    let poolConnection = redisConnection.getInstance();
    let resourcePromise = poolConnection.acquire();
    resourcePromise
      .then(function(client) {
        client.hSet('user_node:auth:'+req.body.username, "date", Date.now());
        client.hSet('user_node:auth:'+req.body.username, "access_token", tokens.access_token);
        client.hSet('user_node:auth:'+req.body.username, "refresh_token", tokens.refresh_token);
        poolConnection.release(client);
        console.result(200,req.url);
        return res.status(200).json({ message: 'Refresh successful.', access_token: tokens.access_token, refresh_token: tokens.refresh_token });
      })
      .catch(function(err) {
	next(err);
        console.result(500,req.url,err);
        return res.status(500).json({ message: 'Internal server error.' });
      });
  } 
  catch (err) {
    console.result(500,req.url,err);
    return res.status(500).json({ message: 'Internal server error.' });
  }
};
module.exports = { login, logout, ping, refresh };
