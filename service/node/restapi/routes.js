const express = require("express");

var indexRouter = require("./api/routes/index");
var authRouter = require("./api/routes/auth");

module.exports = function(app) {
  app.use(express.json());
  app.use("/", indexRouter);
  app.use("/", authRouter);
};

