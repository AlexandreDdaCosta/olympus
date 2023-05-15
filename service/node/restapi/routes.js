const express = require("express");

const authRouter = require("./api/routes/auth");
const equitiesRouter = require("./api/routes/equities");
const indexRouter = require("./api/routes/index");
const tokenRouter = require("./api/routes/token");

module.exports = function appExports(app) {
  app.use(express.json());
  app.use("/", indexRouter);
  app.use("/auth", authRouter);
  app.use("/equities", equitiesRouter);
  app.use("/token", tokenRouter);
};
