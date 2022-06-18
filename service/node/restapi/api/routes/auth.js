const path = '/auth';

const express = require('express');
const router = express.Router();
const controller = require('../controllers'+path);
const dataValidate = require('../validations'+path);
const middleware = require("../middleware"+path);

router.post(path+'/login', dataValidate.loginValidate, controller.login);
router.delete(path+'/logout', middleware.verifyAccessToken, controller.logout);
router.get(path+'/ping', middleware.verifyAccessToken, controller.ping);
router.post(path+'/refresh', dataValidate.refreshValidate, middleware.verifyRefreshToken, controller.refresh);
module.exports = router; 
