const { validationResult } = require("express-validator");
const equitiesModel = require("../models/equities");
const equitiesLib = require("../../lib/token/equities");

const equities = async (req, res, next) => {
  let dataSource;

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
    dataSource = await equitiesModel.findDatasourceByName(
      req.params.dataSource
    );
    if (
      Object.prototype.hasOwnProperty.call(equitiesLib, dataSource.DataSource)
    ) {
      dataSource = await equitiesLib[dataSource.DataSource](dataSource);
    }
  } catch (err) {
    next(err);
    return res.status(500).json({ message: "Internal server error." }).send();
  }

  next();
  const reply = {
    message: "Request successful.",
    dataSource: dataSource.DataSource,
  };
  const dataSourceKeys = Object.keys(dataSource);
  for (let i = 0; i < dataSourceKeys.length; i += 1) {
    const key = dataSourceKeys[i];
    if (
      ![
        "_id",
        "KeyName",
        "IssueEpochDate",
        "RedirectUri",
        "DataSource",
      ].includes(key)
    ) {
      const replyKey = key.toLowerCase();
      reply[replyKey] = dataSource[key];
    }
  }
  res.status(200).json(reply);
  return false;
};

module.exports = { equities };
