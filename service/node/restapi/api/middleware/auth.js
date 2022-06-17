const { check, validationResult } = require('express-validator');
const jwt = require('jsonwebtoken');

const verifyAccessToken = (request, result, next) => {
  const errors = validationResult(request);
  if (! errors.isEmpty()) {
    console.log('401 '+request.url+' '+JSON.stringify(errors.array()));
    result.status(401).json({ message: 'Access denied.' }).send();
  }
  else {
    next();
  }
};
module.exports = { verifyAccessToken };
