const express = require('express');
const router = express.Router();
const authController = require('../controllers/auth');
router.post('/login', authController.login);
router.delete('/logout', authController.logout);
router.post('/refresh', authController.refresh);
module.exports = router; 
