const config = require('config');
const equitiesModel = require('../../api/models/equities');
const https = require('https'); 

async function TDAmeritrade(dataSource,localAccessToken) {
  let data;
  let options;
  let redirectUri = encodeURIComponent(dataSource.RedirectUri);
  let result;
  localAccessToken = true;

  if (dataSource.KeyName != 'authorization_code') {
    return dataSource;
  }
  let tokenDocument;
  tokenDocument = await equitiesModel.findEquityTokenDocument(dataSource.DataSource);
  let now = parseInt(new Date().getTime()/1000);

  if (tokenDocument == null || tokenDocument.refreshToken == null || tokenDocument.refreshTokenExpiration == null || tokenDocument.refreshTokenExpiration < now) {
    // With no valid refresh token, use authorization code to generate new tokens
    if (tokenDocument != null && tokenDocument.authorizationCode != null && tokenDocument.authorizationCode == dataSource.Token) {
      // Cannot re-use one-time tokens
      throw Error('Stale one-time authorization code for TD Ameritrade; must regenerate manually.');
    }

    let code = dataSource.Token; // Already url encoded
    data = 'grant_type=authorization_code&refresh_token=&access_type=offline&code=' + code + '&client_id=' + dataSource.ClientID + '&redirect_uri=' + redirectUri;
    options = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': data.length
      },
      hostname: dataSource.Url,
      method: 'POST',
      path: '/v1/oauth2/token',
      port: 443
    };
    function initAmeritradeTokens(options, data) {
      return new Promise((resolve, reject) => {
        const req = https.request(options, (res) => {
          res.setEncoding('utf8');
          let body = '';
          res.on('data', (chunk) => { body += chunk; });
          res.on('end', () => { resolve(JSON.parse(body)); });
        });
        req.on('error', (err) => { reject(err); });
        req.write(data)
        req.end();
      });
    };
    result = await initAmeritradeTokens(options, data);
    if (result.error) {
      throw Error('TD Ameritrade API error for ' + options['path'] + ': ' + result.error);
    }
    now = parseInt(new Date().getTime()/1000);
    tokenDocument = {};
    tokenDocument.authorizationCode = dataSource.Token;
    tokenDocument.localAccessToken = result.access_token;
    tokenDocument.localAccessTokenExpiration = result.expires_in + now;
    tokenDocument.refreshToken = result.refresh_token;
    tokenDocument.refreshTokenExpiration = result.refresh_token_expires_in + now;
  }

  if (tokenDocument.refreshTokenExpiration < (now + 604800)) {
    // Get a new access + refresh token if a valid refresh token exists and expires in less than one week
    // Put new access/refresh token code here
    let encodedToken = encodeURIComponent(tokenDocument.refreshToken);
    data = 'grant_type=refresh_token&refresh_token=' + encodedToken + '&access_type=offline&client_id=' + dataSource.ClientID + '&redirect_uri=' + redirectUri;
    options = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': data.length
      },
      hostname: dataSource.Url,
      method: 'POST',
      path: '/v1/oauth2/token',
      port: 443
    };
    function getAmeritradeTokens(options, data) {
      return new Promise((resolve, reject) => {
        const req = https.request(options, (res) => {
          res.setEncoding('utf8');
          let body = '';
          res.on('data', (chunk) => { body += chunk; });
          res.on('end', () => { resolve(JSON.parse(body)); });
        });
        req.on('error', (err) => { reject(err); });
        req.write(data)
        req.end();
      });
    };
    result = await getAmeritradeTokens(options, data);
    if (result.error) {
      throw Error('TD Ameritrade API error for ' + options['path'] + ': ' + result.error);
    }
    now = parseInt(new Date().getTime()/1000);
    tokenDocument.localAccessToken = result.access_token;
    tokenDocument.localAccessTokenExpiration = result.expires_in + now;
    tokenDocument.refreshToken = result.refresh_token;
    tokenDocument.refreshTokenExpiration = result.refresh_token_expires_in + now;
    dataSource.Token = tokenDocument.locaSccessToken;
    dataSource.Expiration = tokenDocument.localAccessTokenExpiration;
  }

  now = parseInt(new Date().getTime()/1000);
  if (localAccessToken && (now < (tokenDocument.localAccessTokenExpiration - 300))) {
    dataSource.Token = tokenDocument.localAccessToken;
    dataSource.Expiration = tokenDocument.localAccessTokenExpiration;
  }
  else {
    let encodedToken = encodeURIComponent(tokenDocument.refreshToken);
    data = 'grant_type=refresh_token&refresh_token=' + encodedToken + '&client_id=' + dataSource.ClientID + '&redirect_uri=' + redirectUri;
    options = {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': data.length
      },
      hostname: dataSource.Url,
      method: 'POST',
      path: '/v1/oauth2/token',
      port: 443
    };
    function getAmeritradeAccessToken(options, data) {
      return new Promise((resolve, reject) => {
        const req = https.request(options, (res) => {
          res.setEncoding('utf8');
          let body = '';
          res.on('data', (chunk) => { body += chunk; });
          res.on('end', () => { resolve(JSON.parse(body)); });
        });
        req.on('error', (err) => { reject(err); });
        req.write(data)
        req.end();
      });
    };
    result = await getAmeritradeAccessToken(options, data);
    if (result.error) {
      throw Error('TD Ameritrade API error for ' + options['path'] + ': ' + result.error);
    }
    now = parseInt(new Date().getTime()/1000);
    if (localAccessToken) {
      tokenDocument.localAccessToken = result.access_token;
      tokenDocument.localAccessTokenExpiration = result.expires_in + now;
    }
    dataSource.Token = result.access_token
    dataSource.Expiration = result.expires_in + now;
  }

  await equitiesModel.updateEquityTokenDocument('TDAmeritrade',tokenDocument);
  return dataSource;
}

module.exports = { TDAmeritrade };
