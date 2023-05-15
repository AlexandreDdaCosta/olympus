const express = require("express");

const router = express.Router();
const authMiddleware = require("../middleware/auth");
const controller = require("../controllers/token");
const dataValidate = require("../validations/token");

router.all("/", (_req, res, next) => {
  res.status(404).send();
  next();
});
router.all("/equities", (_req, res, next) => {
  res.status(404).send();
  next();
});
router.get(
  "/equities/:dataSource",
  dataValidate.equitiesValidate,
  authMiddleware.verifyAccessToken,
  authMiddleware.verifyEndpointPermission,
  controller.equities
);
router.use((req, res) => {
  res.on("finish", () => {
    console.result(res, req);
  });
});
module.exports = router;
