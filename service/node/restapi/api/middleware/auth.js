const jwt = require('jsonwebtoken');
const redisConnection = require('redis_connect');

const verifyAccessToken = (req, res, next) => {
  if (! req.headers || ! req.headers.authorization || req.headers.authorization.split(' ')[0] != 'Bearer') {
    next('route');
    res.locals.statusMessage = 'Bad authorization header for "Bearer <access token>" ('+req.headers.authorization+')';
    res.status(401).json({ message: 'Access denied.' }).send();
  }
  else {
    const token = req.headers.authorization.split(" ")[1];
    jwt.verify(token, process.env.access_token_secret, (err, user) => {
      if (err) {
        next('route');
        res.locals.statusMessage = 'Invalid access token ('+req.headers.authorization+')';
        res.status(401).json({ message: 'Access denied.' }).send();
      }
      else {
        req.user = user.username;
        let poolConnection = redisConnection.getInstance();
        let resourcePromise = poolConnection.acquire();
	let key = 'restapi:auth:' + req.user + ':' + req.headers.host;
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
                  res.locals.statusMessage = 'Submitted access token for ' + req.user + ' does not match token list.';
                  res.status(401).json({ message: 'Access denied.' }).send();
		}
	      })
              .catch(function(err) {
                next('route');
                res.locals.statusMessage = err;
                res.status(500).json({ message: 'Internal server error.' }).send();
	      });
          })
          .catch(function(err) {
            next('route');
            res.locals.statusMessage = err;
            res.status(500).json({ message: 'Internal server error.' }).send();
          });
      }
    });
  }
};

const verifyEndpointPermission = (req, res, next) => {
  let poolConnection = redisConnection.getInstance();
  let resourcePromise = poolConnection.acquire();
  let key = 'restapi:endpoints:' + req.user + ':' + req.headers.host;
  resourcePromise
    .then(function(client) {
      let endpoints = client.hGetAll(key);
      endpoints
        .then(function(paths) {
          for (var startPath in paths) {
	    cutLength = startPath.length
	    testPath = req.originalUrl.substr(0,cutLength);
	    if ( (testPath == startPath) && (req.method = paths[startPath] || paths[startPath] == 'ALL') ) {
	      console.log('User ' + req.user + ' permitted for ' + req.originalUrl + ' ' + req.method);
              poolConnection.release(client);
              next();
	      return;
	    }
          }
          next('route');
          res.locals.statusMessage = 'User ' + req.user + ' denied access to requested endpoint ' + req.path + ', method ' + req.methodi + '.';
          res.status(401).json({ message: 'Access denied.' }).send();
        })
        .catch(function(err) {
           next('route');
           res.locals.statusMessage = err;
           res.status(500).json({ message: 'Internal server error.' }).send();
        });
    })
    .catch(function(err) {
      next('route');
      res.locals.statusMessage = err;
      res.status(500).json({ message: 'Internal server error.' }).send();
    });
};

const verifyRefreshToken = (req, res, next) => {
  if (! req.headers || ! req.headers.authorization || req.headers.authorization.split(' ')[0] != 'Bearer') {
    next('route');
    res.locals.statusMessage = 'Bad authorization header for "Bearer <refresh token>" ('+req.headers.authorization+')';
    res.status(401).json({ message: 'Access denied.' }).send();
  }
  else {
    const token = req.headers.authorization.split(" ")[1];
    jwt.verify(token, process.env.refresh_token_secret, (err, user) => {
      if (err) {
        next('route');
        res.locals.statusMessage = 'Invalid refresh token ('+token+')';
        res.status(401).json({ message: 'Access denied.' }).send();
      }
      else {
        req.user = user.username;
        let poolConnection = redisConnection.getInstance();
        let resourcePromise = poolConnection.acquire();
	let key = 'restapi:auth:' + req.user + ':' + req.headers.host;
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
                  res.locals.statusMessage = 'Submitted refresh token for ' + req.user + ' does not match token list.';
                  res.status(401).json({ message: 'Access denied.' }).send();
		}
	      })
              .catch(function(err) {
                next('route');
                res.locals.statusMessage = err;
                res.status(500).json({ message: 'Internal server error.' }).send();
	      });
          })
          .catch(function(err) {
            next('route');
            res.locals.statusMessage = err;
            res.status(500).json({ message: 'Internal server error.' }).send();
          });
      }
    });
  }
};

module.exports = { verifyAccessToken, verifyEndpointPermission, verifyRefreshToken };
