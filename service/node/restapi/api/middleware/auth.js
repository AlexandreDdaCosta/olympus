const jwt = require('jsonwebtoken');
const redisConnection = require('redis_connect');

const verifyAccessToken = (request, result, next) => {
  if (! request.headers || ! request.headers.authorization || request.headers.authorization.split(' ')[0] != 'Bearer') {
    console.result(401,request.url,'Bad authorization header for "Bearer <access token>" ['+request.headers.authorization+']');
    result.status(401).json({ message: 'Access denied.' }).send();
  }
  else {
    const token = request.headers.authorization.split(" ")[1];
    jwt.verify(token, process.env.access_token_secret, (err, user) => {
      if (err) {
        console.result(401,request.url,'Invalid access token ['+request.headers.authorization+']');
        result.status(401).json({ message: 'Access denied.' }).send();
      }
      else {
        request.user = user.username;
        next();
      }
    });
  }
};

const verifyRefreshToken = (request, result, next) => {
  if (! request.headers || ! request.headers.authorization || request.headers.authorization.split(' ')[0] != 'Bearer') {
    console.result(401,request.url,'Bad authorization header for "Bearer <refresh token>" ['+request.headers.authorization+']');
    result.status(401).json({ message: 'Access denied.' }).send();
  }
  else {
    const token = request.headers.authorization.split(" ")[1];
    jwt.verify(token, process.env.refresh_token_secret, (err, user) => {
      if (err) {
        console.result(401,request.url,'Invalid refresh token ['+token+']');
        result.status(401).json({ message: 'Access denied.' }).send();
      }
      else {
        request.user = user.username;
        let poolConnection = redisConnection.getInstance();
        let resourcePromise = poolConnection.acquire();
	let key = 'user_node:auth:' + request.user;
        let last_token;
        resourcePromise
          .then(function(client) {
            last_token = client.hGet(key,'refresh_token');
            console.log('LASTTOKEN');
            console.log(last_token);
            poolConnection.release(client);
          })
          .catch(function(err) {
            next(err);
          });
        next();
      }
    });
  }
};

module.exports = { verifyAccessToken, verifyRefreshToken };
