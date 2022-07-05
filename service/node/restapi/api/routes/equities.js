const express = require('express');
const router = express.Router();
const authMiddleware = require('../middleware/auth');
const controller = require('../controllers/equities');
const dataValidate = require('../validations/equities');

router.all('/', (req, res, next) => {
  res.status(404).send();
  next();
})
router.all('/symbol', (req, res, next) => {
  res.status(404).send();
  next();
})
router.get('/symbol/:symbol', dataValidate.symbolValidate, authMiddleware.verifyAccessToken, authMiddleware.verifyEndpointPermission, controller.symbol);
router.use((req, res, next) => {
  res.on('finish', () => {
    console.result(res,req);
  });
});
module.exports = router; 
