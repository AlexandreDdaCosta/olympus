const config = require('config');
const redisConnection = require('redis_connect');
const { validationResult } = require('express-validator');

const token = async (req, res, next) => {
  let providerToken;

  try {
    const errors = validationResult(req);
    if (! errors.isEmpty()) {
      next();
      res.locals.statusMessage = 'Request failed: '+JSON.stringify(errors.array());
      return res.status(400).json({ message: 'Request failed.', errors: JSON.stringify(errors.array()) }).send();
    }
  } 
  catch (err) {
    next(err);
    return res.status(500).json({ message: 'Internal server error.' }).send();
  }

  next('route');
  now = new Date();
  return res.status(200).json({ message: 'Request successful.', provider_token: providerToken, expiration_date: now }).send();
};

module.exports = { token };
