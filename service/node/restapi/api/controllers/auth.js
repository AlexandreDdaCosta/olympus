const UserModel = require("../models/users");
const argon2 = require('argon2');
const config = require('config');
const hashing_config = { parallelism: config.get('argon2.parallelism'), memoryCost: config.get('argon2.memory_cost'), timeCost: config.get('argon2.time_cost') }
const { validationResult } = require("express-validator");

const login = (req, res, next) => {
  let path = ' /auth/login auth.js ';
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
      console.log('400'+path+JSON.stringify(errors.array()));
      return res.status(400).json({
        message: 'Login failed.',
        errors: errors.array(),
      });
    }
  } 
  catch (err) {
    next(err);
  }
  UserModel.findByUsername(req.body.username).then( (user) => {
    console.log(user);
    if (! user) {
      console.log('404'+path);
      return res.status(404).json({ message: 'Access denied.' });
    }
    var hashed_password = user['Password'];
    console.log(hashed_password);
    //var password_verification = argon2.verify(hashed_password, restapi_password, hashing_config);
    //console.log(password_verification);
  });
  console.log('200'+path);
  return res.status(200).json({ message: 'Login successful.' });
};
const logout = (req, res, next) => {
  let path = ' /auth/logout auth.js ';
  console.log('200'+path);
  return res.status(200).json({ message: 'Logout successful.' });
};
const refresh = (req, res, next) => {
  let path = ' /auth/refresh auth.js ';
  console.log('200'+path);
  return res.status(200).json({ message: 'Refresh successful.' });
};
module.exports = { login, logout, refresh };
