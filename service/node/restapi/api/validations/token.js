const { check } = require("express-validator");

const equitiesValidate = [
  check("dataSource")
    .isString()
    .matches(/^[a-zA-Z0-9]{1,100}$/)
    .withMessage(
      'Parameter "dataSource" is required and must be an alphanumeric English alphabet string less than 100 characters.'
    ),
];

module.exports = { equitiesValidate };
