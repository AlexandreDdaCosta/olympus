const express = require('express');
const router = express.Router();
const authController = require('../controllers/auth');
const authDataValidate = require("../validations/auth");

router.post('/login', authDataValidate.loginValidate, authController.login);
router.delete('/logout', authController.logout);
router.get('/ping', authController.ping);
router.post('/refresh', authController.refresh);
module.exports = router; 
