const { check } = require("express-validator");

const symbolValidate = [
  check("symbol")
    .isString()
    .matches(/^[A-Z0-9]{1,10}$/)
    .withMessage('Parameter "symbol" is required and must be an upper case, alphanumeric English alphabet string less than 10 characters.'),
];

module.exports = { symbolValidate };
