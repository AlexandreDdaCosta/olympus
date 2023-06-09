const { validationResult } = require("express-validator");
const auth = require("../../lib/auth");
const redisConnection = require("../../lib/redis_connect");

const login = async (req, res, next) => {
  let tokens;

  try {
    // Suppress sensitive login information in logs and returned messages
    const myValidationResult = validationResult.withDefaults({
      formatter: (error) => {
        return {
          location: error.location,
          msg: error.msg,
          param: error.param,
        };
      },
    });
    const errors = myValidationResult(req);
    if (!errors.isEmpty()) {
      next();
      res.locals.statusMessage = `Login failed: ${JSON.stringify(
        errors.array()
      )}`;
      return res
        .status(400)
        .json({
          message: "Login failed.",
          errors: JSON.stringify(errors.array()),
        })
        .send();
    }
  } catch (err) {
    next(err);
    return res.status(500).json({ message: "Internal server error." }).send();
  }

  try {
    const userRecord = await auth.passwordUserMatch(
      req.body.username,
      req.body.password
    );
    if (!userRecord) {
      next();
      res.locals.statusMessage = "Bad user/password match";
      return res.status(401).json({ message: "Access denied." }).send();
    }
    req.user = req.body.username;
    tokens = await auth.createTokens(req.body.username);
    const poolConnection = redisConnection.getInstance();
    const resourcePromise = poolConnection.acquire();
    resourcePromise
      .then(function setRedisToken(client) {
        client.hSet(
          `restapi:auth:${req.body.username}:${req.headers.host}`,
          "access_token",
          tokens.access_token
        );
        client.hSet(
          `restapi:auth:${req.body.username}:${req.headers.host}`,
          "access_token_expiration",
          tokens.access_token_expiration
        );
        client.hSet(
          `restapi:auth:${req.body.username}:${req.headers.host}`,
          "refresh_token",
          tokens.refresh_token
        );
        client.hSet(
          `restapi:auth:${req.body.username}:${req.headers.host}`,
          "refresh_token_expiration",
          tokens.refresh_token_expiration
        );
        if (Object.keys(userRecord).includes("DefinedRoutes")) {
          if (!userRecord.DefinedRoutes) {
            client.hSet(
              `restapi:endpoints:${req.body.username}:${req.headers.host}`,
              "/",
              "ALL"
            );
          } else {
            const routes = Object.keys(userRecord.DefinedRoutes);
            for (let index = 0, l = routes.length; index < l; index += 1) {
              const route = routes[index];
              for (
                let userIndex = 0, m = userRecord.DefinedRoutes[route].length;
                userIndex < m;
                userIndex += 1
              ) {
                const method = userRecord.DefinedRoutes[route][userIndex];
                client.hSet(
                  `restapi:endpoints:${req.body.username}:${req.headers.host}`,
                  route,
                  method
                );
              }
            }
          }
        }
        poolConnection.release(client);
        next();
        return res
          .status(200)
          .json({
            message: "Login successful.",
            access_token: tokens.access_token,
            access_token_expiration: tokens.access_token_expiration,
            refresh_token: tokens.refresh_token,
            refresh_token_expiration: tokens.refresh_token_expiration,
          })
          .send();
      })
      .catch(function loginInternalError(err) {
        next(err);
        return res
          .status(500)
          .json({ message: "Internal server error." })
          .send();
      });
  } catch (err) {
    next(err);
    return res.status(500).json({ message: "Internal server error." }).send();
  }
  return false;
};
const logout = async (req, res, next) => {
  try {
    const poolConnection = redisConnection.getInstance();
    const resourcePromise = poolConnection.acquire();
    resourcePromise
      .then(function clientLogout(client) {
        client.del(`restapi:auth:${req.user}:${req.headers.host}`);
        client.del(`restapi:endpoints:${req.user}:${req.headers.host}`);
        poolConnection.release(client);
        next();
        return res.status(200).json({ message: "Logout successful." }).send();
      })
      .catch(function logoutInternalError(err) {
        next(err);
        return res
          .status(500)
          .json({ message: "Internal server error." })
          .send();
      });
  } catch (err) {
    next(err);
    return res.status(500).json({ message: "Internal server error." }).send();
  }
  return false;
};
const ping = async (_req, res, next) => {
  next();
  return res
    .status(200)
    .json({ message: "Give me a ping, Vasili. One ping only, please." })
    .send();
};
const refresh = async (req, res, next) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      next();
      res.locals.statusMessage = `Refresh failed: ${JSON.stringify(
        errors.array()
      )}`;
      return res
        .status(400)
        .json({ message: "Refresh failed.", errors: errors.array() })
        .send();
    }
    if (req.body.username !== req.user) {
      next();
      res.locals.statusMessage = "Bad username in body";
      return res.status(401).json({ message: "Access denied." }).send();
    }
    const tokens = await auth.createTokens(req.body.username);
    const poolConnection = redisConnection.getInstance();
    const resourcePromise = poolConnection.acquire();
    resourcePromise
      .then(function clientLoginRefresh(client) {
        client.hSet(
          `restapi:auth:${req.body.username}:${req.headers.host}`,
          "access_token",
          tokens.access_token
        );
        client.hSet(
          `restapi:auth:${req.body.username}:${req.headers.host}`,
          "access_token_expiration",
          tokens.access_token_expiration
        );
        client.hSet(
          `restapi:auth:${req.body.username}:${req.headers.host}`,
          "refresh_token",
          tokens.refresh_token
        );
        client.hSet(
          `restapi:auth:${req.body.username}:${req.headers.host}`,
          "refresh_token_expiration",
          tokens.refresh_token_expiration
        );
        poolConnection.release(client);
        next();
        return res
          .status(200)
          .json({
            message: "Refresh successful.",
            access_token: tokens.access_token,
            access_token_expiration: tokens.access_token_expiration,
            refresh_token: tokens.refresh_token,
            refresh_token_expiration: tokens.refresh_token_expiration,
          })
          .send();
      })
      .catch(function loginRefreshInternalError(err) {
        next(err);
        return res
          .status(500)
          .json({ message: "Internal server error." })
          .send();
      });
  } catch (err) {
    next(err);
    return res.status(500).json({ message: "Internal server error." }).send();
  }
  return false;
};
module.exports = { login, logout, ping, refresh };
