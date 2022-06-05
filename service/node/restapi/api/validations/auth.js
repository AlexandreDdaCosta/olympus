const { body } = require("express-validator");

const loginValidate = [
  body("username")
    .exists({ checkFalsy: true })
    .withMessage('Parameter "username" is required.')
    .isString()
    .withMessage('User name should be string.'),
  body("password")
    .exists()
    .withMessage('Parameter "password" is required.')
    .isString()
    .withMessage('Password should be a string.')
    .isLength({ min: 100, max: 100 })
    .withMessage('Password should be 100 characters.'),
];

module.exports = { loginValidate };
