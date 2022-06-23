const express = require("express");

var authRouter = require("./api/routes/auth");
var indexRouter = require("./api/routes/index");
var tokenRouter = require("./api/routes/token");

module.exports = function(app) {
  app.use(express.json());
  app.use("/", indexRouter);
  app.use("/auth", authRouter);
  app.use("/token", tokenRouter);
};

