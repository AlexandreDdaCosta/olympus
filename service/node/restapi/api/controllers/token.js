const config = require('config');
const equitiesModel = require('../models/equities.js');
const redisConnection = require('redis_connect');
const tokenLib = require('../../lib/token.js');
const { validationResult } = require('express-validator');

const token = async (req, res, next) => {
  let dataSource;
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

  try {
    dataSource = await equitiesModel.findDatasourceByName(req.params.providerName);
  }
  catch (err) {
    next(err);
    return res.status(500).json({ message: 'Internal server error.' }).send();
  }

  if (tokenLib.hasOwnProperty(dataSource.DataSource)) {
    dataSource = await tokenLib[dataSource.DataSource](dataSource);
    console.log(dataSource);
  } 
  next();
  res.status(200).json({ message: 'Request successful.', dataSource: dataSource.DataSource, expiration: dataSource.expiration, token: dataSource.Key, url: dataSource.Url });
};

module.exports = { token };
