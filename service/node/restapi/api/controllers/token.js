const config = require('config');
const equitiesModel = require('../models/equities.js');
const redisConnection = require('redis_connect');
const equitiesLib = require('../../lib/token/equities.js');
const { validationResult } = require('express-validator');

const equities = async (req, res, next) => {
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
    dataSource = await equitiesModel.findDatasourceByName(req.params.dataSource);
    if (equitiesLib.hasOwnProperty(dataSource.DataSource)) {
      dataSource = await equitiesLib[dataSource.DataSource](dataSource);
    } 
  }
  catch (err) {
    next(err);
    return res.status(500).json({ message: 'Internal server error.' }).send();
  }

  next();
  let reply = { message: 'Request successful.', dataSource: dataSource.DataSource };
  for (var key in dataSource) {
    if (['_id', 'KeyName', 'IssueEpochDate', 'RedirectUri', 'DataSource'].includes(key)) {
      continue;
    }
    replyKey = key.toLowerCase();
    reply[replyKey] = dataSource[key];
  }
  res.status(200).json(reply);
};

module.exports = { equities };
