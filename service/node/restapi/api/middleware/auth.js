const jwt = require('jsonwebtoken');

const verifyAccessToken = (request, result, next) => {
  if (! request.headers || ! request.headers.authorization || request.headers.authorization.split(' ')[0] != 'Bearer') {
    console.result(401,request.url,'Bad authorization header for "Bearer <access token>" ['+request.headers.authorization+']');
    result.status(401).json({ message: 'Access denied.' }).send();
  }
  else {
    const token = request.headers.authorization.split(" ")[1];
    jwt.verify(token, process.env.access_token_secret, (err, user) => {
      if (err) {
        console.result(401,request.url,'Invalid token ['+request.headers.authorization+']');
        result.status(401).json({ message: 'Access denied.' }).send();
      }
      else {
        request.user = user;
        console.log(user);
        next();
      }
    })
  }
};
module.exports = { verifyAccessToken };
