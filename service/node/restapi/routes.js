const express = require("express");

var authRouter = require("./api/routes/auth");
var equitiesRouter = require("./api/routes/equities");
var indexRouter = require("./api/routes/index");
var tokenRouter = require("./api/routes/token");

module.exports = function(app) {
  app.use(express.json());
  app.use("/", indexRouter);
  app.use("/auth", authRouter);
  app.use("/equities", equitiesRouter);
  app.use("/token", tokenRouter);
};

