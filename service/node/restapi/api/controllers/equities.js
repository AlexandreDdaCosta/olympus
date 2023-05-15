const { validationResult } = require("express-validator");
const equitiesModel = require("../models/equities");

const symbol = async (req, res, next) => {
  let symbolData;

  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      next();
      res.locals.statusMessage = `Request failed: ${JSON.stringify(
        errors.array()
      )}`;
      return res
        .status(400)
        .json({
          message: "Request failed.",
          errors: JSON.stringify(errors.array()),
        })
        .send();
    }
  } catch (err) {
    next(err);
    return res.status(500).json({ message: "Internal server error." }).send();
  }

  try {
    symbolData = await equitiesModel.findSymbol(req.params.symbol);
  } catch (err) {
    next(err);
    return res.status(500).json({ message: "Internal server error." }).send();
  }

  next();
  if (!symbolData) {
    res.status(404).json({ message: "Symbol not found." });
  } else {
    res
      .status(200)
      .json({ message: "Request successful.", symbol: symbolData });
  }
  return false;
};

const symbols = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      next();
      res.locals.statusMessage = `Request failed: ${JSON.stringify(
        errors.array()
      )}`;
      return res
        .status(400)
        .json({
          message: "Request failed.",
          errors: JSON.stringify(errors.array()),
        })
        .send();
    }
  } catch (err) {
    next(err);
    return res.status(500).json({ message: "Internal server error." }).send();
  }

  let stringAsList = [];
  let symbolData = {};
  try {
    stringAsList = req.params.symbolList.split(",");
    symbolData = await equitiesModel.findSymbols(stringAsList);
  } catch (err) {
    next(err);
    return res.status(500).json({ message: "Internal server error." }).send();
  }

  next();
  const unknownSymbols = [];
  const symbols = {};
  if (!symbolData) {
    res.status(200).json({
      message: "Request successful.",
      symbols: [],
      unknownSymbols: stringAsList,
    });
  } else {
    for (let i = 0; i < stringAsList.length; i += 1) {
      let recognizedSymbol = false;
      const symbolDataKeys = Object.keys(symbolData);
      for (let j = 0; j < symbolDataKeys.length; j += 1) {
        const entry = symbolDataKeys[j];
        if (symbolData[entry].Symbol === stringAsList[i]) {
          symbols[stringAsList[i]] = symbolData[entry];
          recognizedSymbol = true;
          break;
        }
      }
      if (!recognizedSymbol) {
        unknownSymbols.push(stringAsList[i]);
      }
    }
    res.status(200).json({
      message: "Request successful.",
      symbols,
      unknownSymbols,
    });
  }
  return false;
};

module.exports = { symbol, symbols };
