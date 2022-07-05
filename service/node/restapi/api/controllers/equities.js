const config = require('config');
const equitiesModel = require('../models/equities.js');
const { validationResult } = require('express-validator');

const symbol = async (req, res, next) => {
  let symbol;

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
    symbolData = await equitiesModel.findSymbol(req.params.symbol);
  }
  catch (err) {
    next(err);
    return res.status(500).json({ message: 'Internal server error.' }).send();
  }

  next();
  if (! symbolData) {
    res.status(404).json({ message: 'Symbol not found.' });
  }
  else {
    res.status(200).json({ message: 'Request successful.', data: symbolData });
  }
};

module.exports = { symbol };
