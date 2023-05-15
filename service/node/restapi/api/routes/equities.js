const express = require("express");

const router = express.Router();
const authMiddleware = require("../middleware/auth");
const controller = require("../controllers/equities");
const dataValidate = require("../validations/equities");

router.all("/", (_req, res, next) => {
  res.status(404).send();
  next();
});
router.all("/symbol", (_req, res, next) => {
  res.status(404).send();
  next();
});
router.all("/symbols", (_req, res, next) => {
  res.status(404).send();
  next();
});
router.get(
  "/symbol/:symbol",
  dataValidate.symbolValidate,
  authMiddleware.verifyAccessToken,
  authMiddleware.verifyEndpointPermission,
  controller.symbol
);
router.get(
  "/symbols/:symbolList",
  dataValidate.symbolListValidate,
  authMiddleware.verifyAccessToken,
  authMiddleware.verifyEndpointPermission,
  controller.symbols
);
router.use((req, res) => {
  res.on("finish", () => {
    console.result(res, req);
  });
});
module.exports = router;
