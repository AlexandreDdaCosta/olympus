const express = require("express");

const router = express.Router();
const controller = require("../controllers/auth");
const dataValidate = require("../validations/auth");
const middleware = require("../middleware/auth");

router.post("/login", dataValidate.loginValidate, controller.login);
router.delete("/logout", middleware.verifyRefreshToken, controller.logout);
router.get("/ping", middleware.verifyAccessToken, controller.ping);
router.get("/pingr", middleware.verifyRefreshToken, controller.ping);
router.post(
  "/refresh",
  dataValidate.refreshValidate,
  middleware.verifyRefreshToken,
  controller.refresh
);
router.use((req, res) => {
  res.on("finish", () => {
    console.result(res, req);
  });
});
module.exports = router;
