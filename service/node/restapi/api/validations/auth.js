const { check } = require("express-validator");

const loginValidate = [
  check("username")
    .isString()
    .withMessage('Parameter "username" is required and must be a string.'),
  check("password")
    .isString()
    .withMessage('Parameter "password" is required and must be a string.')
    .isLength({ min: 100, max: 100 })
    .withMessage('Password should be 100 characters.'),
];

module.exports = { loginValidate };
