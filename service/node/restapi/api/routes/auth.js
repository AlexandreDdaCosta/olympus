const express = require('express');
const router = express.Router();
//const authController = require('../controllers/auth');
router.post('/auth/login', authController.login);
//router.delete('/auth/logout', authController.logout);
//router.post('/auth/refresh', authController.refresh);
module.exports = router; 
