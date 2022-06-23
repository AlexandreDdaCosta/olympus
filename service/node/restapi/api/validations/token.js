const { check } = require("express-validator");

const tokenValidate = [
  check("providerName")
    .isString()
    .matches(/^[a-zA-z0-9]{1,100}$/)
    .withMessage('Parameter "providerName" is required and must be an alphanumeric English alphabet string less than 100 characters.'),
];

module.exports = { tokenValidate };
