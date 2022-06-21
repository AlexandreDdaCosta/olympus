const jwt = require('jsonwebtoken');
const redisConnection = require('redis_connect');

const verifyAccessToken = (req, res, next) => {
  if (! req.headers || ! req.headers.authorization || req.headers.authorization.split(' ')[0] != 'Bearer') {
    next('route');
    res.locals.message = 'Bad authorization header for "Bearer <access token>" ('+req.headers.authorization+')';
    res.status(401).json({ message: 'Access denied.' }).send();
  }
  else {
    const token = req.headers.authorization.split(" ")[1];
    jwt.verify(token, process.env.access_token_secret, (err, user) => {
      if (err) {
        next('route');
        res.locals.message = 'Invalid access token ('+req.headers.authorization+')';
        res.status(401).json({ message: 'Access denied.' }).send();
      }
      else {
        req.user = user.username;
        let poolConnection = redisConnection.getInstance();
        let resourcePromise = poolConnection.acquire();
	let key = 'user_node:auth:' + req.user;
        resourcePromise
          .then(function(client) {
            let lastToken = client.hGet(key,'access_token');
            lastToken
              .then(function(accessToken) {
                poolConnection.release(client);
		if (accessToken == token) {
                  next();
		}
		else {
                  next('route');
                  res.locals.message = 'Submitted access token for ' + req.user + ' does not match token list.';
                  res.status(401).json({ message: 'Access denied.' }).send();
		}
	      })
              .catch(function(err) {
                next('route');
                res.locals.message = err;
                res.status(500).json({ message: 'Internal server error.' }).send();
	      });
          })
          .catch(function(err) {
            next('route');
            res.locals.message = err;
            res.status(500).json({ message: 'Internal server error.' }).send();
          });
      }
    });
  }
};

const verifyRefreshToken = (req, res, next) => {
  if (! req.headers || ! req.headers.authorization || req.headers.authorization.split(' ')[0] != 'Bearer') {
    next('route');
    res.locals.message = 'Bad authorization header for "Bearer <refresh token>" ('+req.headers.authorization+')';
    res.status(401).json({ message: 'Access denied.' }).send();
  }
  else {
    const token = req.headers.authorization.split(" ")[1];
    jwt.verify(token, process.env.refresh_token_secret, (err, user) => {
      if (err) {
        next('route');
        res.locals.message = 'Invalid refresh token ('+token+')';
        res.status(401).json({ message: 'Access denied.' }).send();
      }
      else {
        req.user = user.username;
        let poolConnection = redisConnection.getInstance();
        let resourcePromise = poolConnection.acquire();
	let key = 'user_node:auth:' + req.user;
        resourcePromise
          .then(function(client) {
            let lastToken = client.hGet(key,'refresh_token');
            lastToken
              .then(function(refreshToken) {
                poolConnection.release(client);
		if (refreshToken == token) {
                  next();
		}
		else {
                  next('route');
                  res.locals.message = 'Submitted refresh token for ' + req.user + ' does not match token list.';
                  res.status(401).json({ message: 'Access denied.' }).send();
		}
	      })
              .catch(function(err) {
                next('route');
                res.locals.message = err;
                res.status(500).json({ message: 'Internal server error.' }).send();
	      });
          })
          .catch(function(err) {
            next('route');
            res.locals.message = err;
            res.status(500).json({ message: 'Internal server error.' }).send();
          });
      }
    });
  }
};

module.exports = { verifyAccessToken, verifyRefreshToken };
