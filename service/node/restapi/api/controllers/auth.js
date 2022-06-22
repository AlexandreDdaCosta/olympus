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
      next();
      res.locals.message = 'Login failed: '+JSON.stringify(errors.array());
      return res.status(400).json({ message: 'Login failed.', errors: JSON.stringify(errors.array()) }).send();
    }
  } 
  catch (err) {
    next(err);
    return res.status(500).json({ message: 'Internal server error.' }).send();
  }

  try {
    if (! await auth.passwordUserMatch(req.body.username,req.body.password)) {
      next();
      res.locals.message = 'Bad user/password match';
      return res.status(401).json({ message: 'Access denied.' }).send();
    }
    tokens = await auth.createTokens(req.body.username);
    let poolConnection = redisConnection.getInstance();
    let resourcePromise = poolConnection.acquire();
    resourcePromise
      .then(function(client) {
        client.hSet('restapi:auth:'+req.body.username, "date", Date.now());
        client.hSet('restapi:auth:'+req.body.username, "access_token", tokens.access_token);
        client.hSet('restapi:auth:'+req.body.username, "refresh_token", tokens.refresh_token);
        poolConnection.release(client);
        next();
        return res.status(200).json({ message: 'Login successful.', access_token: tokens.access_token, refresh_token: tokens.refresh_token }).send();
      })
      .catch(function(err) {
	next(err);
        return res.status(500).json({ message: 'Internal server error.' }).send();
      });
  }
  catch (err) {
    next(err);
    return res.status(500).json({ message: 'Internal server error.' }).send();
  }
};
const logout = async (req, res, next) => {
  try {
    let poolConnection = redisConnection.getInstance();
    let resourcePromise = poolConnection.acquire();
    resourcePromise
      .then(function(client) {
        client.del('restapi:auth:'+req.user);
        poolConnection.release(client);
	next();
        return res.status(200).json({ message: 'Logout successful.' }).send();
      })
      .catch(function(err) {
	next(err);
        return res.status(500).json({ message: 'Internal server error.' }).send();
      });
  } 
  catch (err) {
    next(err);
    return res.status(500).json({ message: 'Internal server error.' }).send();
  }
};
const ping = async (req, res, next) => {
  next();
  return res.status(200).json({ message: 'Give me a ping, Vasili. One ping only, please.' }).send();
};
const refresh = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (! errors.isEmpty()) {
      next();
      res.locals.message = 'Refresh failed: '+JSON.stringify(errors.array());
      return res.status(400).json({ message: 'Refresh failed.', errors: errors.array() }).send();
    }
    if (req.body.username != req.user) {
      next();
      res.locals.message = 'Bad username in body';
      return res.status(401).json({ message: 'Access denied.' }).send();
    }
    tokens = await auth.createTokens(req.body.username);
    let poolConnection = redisConnection.getInstance();
    let resourcePromise = poolConnection.acquire();
    resourcePromise
      .then(function(client) {
        client.hSet('restapi:auth:'+req.body.username, "date", Date.now());
        client.hSet('restapi:auth:'+req.body.username, "access_token", tokens.access_token);
        client.hSet('restapi:auth:'+req.body.username, "refresh_token", tokens.refresh_token);
        poolConnection.release(client);
        next();
        return res.status(200).json({ message: 'Refresh successful.', access_token: tokens.access_token, refresh_token: tokens.refresh_token }).send();
      })
      .catch(function(err) {
	next(err);
        return res.status(500).json({ message: 'Internal server error.' }).send();
      });
  } 
  catch (err) {
    next(err);
    return res.status(500).json({ message: 'Internal server error.' }).send();
  }
};
module.exports = { login, logout, ping, refresh };
