const https = require("https");
const equitiesModel = require("../../api/models/equities");

async function TDAmeritrade(dataSource, localAccessToken) {
  // Define inner functions here per eslint

  function getAmeritradeAccessToken(options, data) {
    return new Promise((resolve, reject) => {
      const req = https.request(options, (res) => {
        res.setEncoding("utf8");
        let body = "";
        res.on("data", (chunk) => {
          body += chunk;
        });
        res.on("end", () => {
          resolve(JSON.parse(body));
        });
      });
      req.on("error", (err) => {
        reject(err);
      });
      req.write(data);
      req.end();
    });
  }

  function getAmeritradeTokens(options, data) {
    return new Promise((resolve, reject) => {
      const req = https.request(options, (res) => {
        res.setEncoding("utf8");
        let body = "";
        res.on("data", (chunk) => {
          body += chunk;
        });
        res.on("end", () => {
          resolve(JSON.parse(body));
        });
      });
      req.on("error", (err) => {
        reject(err);
      });
      req.write(data);
      req.end();
    });
  }

  function initAmeritradeTokens(options, data) {
    return new Promise((resolve, reject) => {
      const req = https.request(options, (res) => {
        res.setEncoding("utf8");
        let body = "";
        res.on("data", (chunk) => {
          body += chunk;
        });
        res.on("end", () => {
          resolve(JSON.parse(body));
        });
      });
      req.on("error", (err) => {
        reject(err);
      });
      req.write(data);
      req.end();
    });
  }

  let data;
  let options;
  const redirectUri = encodeURIComponent(dataSource.RedirectUri);
  let result;

  if (dataSource.KeyName !== "authorization_code") {
    return dataSource;
  }
  let tokenDocument;
  tokenDocument = await equitiesModel.findEquityTokenDocument(
    dataSource.DataSource
  );
  let now = parseInt(new Date().getTime() / 1000, 10);

  if (
    tokenDocument == null ||
    tokenDocument.refreshToken == null ||
    tokenDocument.refreshTokenExpiration == null ||
    tokenDocument.refreshTokenExpiration < now
  ) {
    // With no valid refresh token, use authorization code to generate new tokens
    if (
      tokenDocument != null &&
      tokenDocument.authorizationCode != null &&
      tokenDocument.authorizationCode === dataSource.Token
    ) {
      // Cannot re-use one-time authorization code
      throw Error(
        "Stale one-time authorization code for TD Ameritrade; must regenerate manually."
      );
    }

    const code = dataSource.Token; // Already url encoded
    data = `grant_type=authorization_code&refresh_token=&access_type=offline&code=${code}&client_id=${dataSource.ClientID}&redirect_uri=${redirectUri}`;
    options = {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": data.length,
      },
      hostname: dataSource.Url,
      method: "POST",
      path: "/v1/oauth2/token",
      port: 443,
    };
    result = await initAmeritradeTokens(options, data);
    if (result.error) {
      throw Error(
        `TD Ameritrade API error for ${options.path}: ${result.error}`
      );
    }
    now = parseInt(new Date().getTime() / 1000, 10);
    tokenDocument = {};
    tokenDocument.authorizationCode = dataSource.Token;
    tokenDocument.localAccessToken = result.access_token;
    tokenDocument.localAccessTokenExpiration = result.expires_in + now;
    tokenDocument.refreshToken = result.refresh_token;
    tokenDocument.refreshTokenExpiration =
      result.refresh_token_expires_in + now;
  }

  if (tokenDocument.refreshTokenExpiration < now + 604800) {
    // Get a new access + refresh token if a valid refresh token exists and expires in less than one week
    const encodedToken = encodeURIComponent(tokenDocument.refreshToken);
    data = `grant_type=refresh_token&refresh_token=${encodedToken}&access_type=offline&client_id=${dataSource.ClientID}&redirect_uri=${redirectUri}`;
    options = {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": data.length,
      },
      hostname: dataSource.Url,
      method: "POST",
      path: "/v1/oauth2/token",
      port: 443,
    };
    result = await getAmeritradeTokens(options, data);
    if (result.error) {
      throw Error(
        `TD Ameritrade API error for ${options.path}: ${result.error}`
      );
    }
    now = parseInt(new Date().getTime() / 1000, 10);
    tokenDocument.localAccessToken = result.access_token;
    tokenDocument.localAccessTokenExpiration = result.expires_in + now;
    tokenDocument.refreshToken = result.refresh_token;
    tokenDocument.refreshTokenExpiration =
      result.refresh_token_expires_in + now;
    dataSource.Token = tokenDocument.localAccessToken;
    dataSource.Expiration = tokenDocument.localAccessTokenExpiration;
  }

  now = parseInt(new Date().getTime() / 1000, 10);
  if (
    localAccessToken &&
    now < tokenDocument.localAccessTokenExpiration - 300
  ) {
    dataSource.Token = tokenDocument.localAccessToken;
    dataSource.Expiration = tokenDocument.localAccessTokenExpiration;
  } else {
    const encodedToken = encodeURIComponent(tokenDocument.refreshToken);
    data = `grant_type=refresh_token&refresh_token=${encodedToken}&client_id=${dataSource.ClientID}&redirect_uri=${redirectUri}`;
    options = {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": data.length,
      },
      hostname: dataSource.Url,
      method: "POST",
      path: "/v1/oauth2/token",
      port: 443,
    };
    result = await getAmeritradeAccessToken(options, data);
    if (result.error) {
      throw Error(
        `TD Ameritrade API error for ${options.path}: ${result.error}`
      );
    }
    now = parseInt(new Date().getTime() / 1000, 10);
    if (localAccessToken) {
      tokenDocument.localAccessToken = result.access_token;
      tokenDocument.localAccessTokenExpiration = result.expires_in + now;
    }
    dataSource.Token = result.access_token;
    dataSource.Expiration = result.expires_in + now;
  }

  await equitiesModel.updateEquityTokenDocument("TDAmeritrade", tokenDocument);
  return dataSource;
}

module.exports = { TDAmeritrade };
