const { check } = require("express-validator");

const symbolListValidate = [
  check("symbolList")
    .isString()
    .matches(/^[A-Z\,]{1,}$/)
    .withMessage('Parameter "symbolList" is required and must be string of uppercase equity symbols separated by commas.'),
];

const symbolValidate = [
  check("symbol")
    .isString()
    .matches(/^[A-Z]{1,10}$/)
    .withMessage('Parameter "symbol" is required and must be an upper case, English alphabet string less than 10 characters.'),
];

module.exports = { symbolListValidate, symbolValidate };
