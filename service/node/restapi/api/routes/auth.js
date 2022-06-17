const express = require('express');
const router = express.Router();
const authController = require('../controllers/auth');
const authDataValidate = require("../validations/auth");
const authMiddleware = require("../middleware/auth");

const path = '/auth';

router.post(path+'/login', authDataValidate.loginValidate, authController.login);
router.delete(path+'/logout', authController.logout);
router.get(path+'/ping', authDataValidate.tokenValidate, authMiddleware.verifyAccessToken, authController.ping);
router.post(path+'/refresh', authController.refresh);
module.exports = router; 
