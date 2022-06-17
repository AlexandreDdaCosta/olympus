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

const tokenValidate = [
  check("Authorization")
    .matches(/^Bearer .*$/)
    .withMessage('Authorization header is required and should be of the format "Bearer <access token>".'),
];

module.exports = { loginValidate, tokenValidate };
