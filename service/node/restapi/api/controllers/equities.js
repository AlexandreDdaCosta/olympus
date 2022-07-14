const config = require('config');
const equitiesModel = require('../models/equities.js');
const { validationResult } = require('express-validator');

const symbol = async (req, res, next) => {
  let symbol;
  let symbolData;

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
    res.status(200).json({ message: 'Request successful.', symbol: symbolData });
  }
};

const symbols = async (req, res, next) => {

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
    stringAsList = req.params.symbolList.split(',');
    symbolData = await equitiesModel.findSymbols(stringAsList);
  }
  catch (err) {
    next(err);
    return res.status(500).json({ message: 'Internal server error.' }).send();
  }

  next();
  let unknownSymbols = [];
  let symbols = {};
  if (! symbolData) {
    res.status(200).json({ message: 'Request successful.', symbols: [], unknownSymbols: stringAsList });
  }
  else {
    for (index in stringAsList) {
      let recognizedSymbol = false;
      for (entry in symbolData) {
        if (symbolData[entry]['Symbol'] == stringAsList[index]) {
          symbols[stringAsList[index]] = symbolData[entry];
          recognizedSymbol = true;
	  break;
	}
      }
      if (! recognizedSymbol) {
        unknownSymbols.push(stringAsList[index]);
      }
    }
    res.status(200).json({ message: 'Request successful.', symbols: symbols, unknownSymbols: unknownSymbols });
  }
};

module.exports = { symbol, symbols };
