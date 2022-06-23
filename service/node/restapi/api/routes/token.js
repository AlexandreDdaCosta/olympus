const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const controller = require('../controllers/token');
const dataValidate = require('../validations/token');

router.get('/', function (req, res, next) {
    res.status(404).send();
    next();
})
router.get('/:providerName', dataValidate.tokenValidate, authMiddleware.verifyAccessToken, controller.token);
router.use((req, res, next) => {
  res.on('finish', () => {
    console.result(res,req);
  });
});
module.exports = router; 
