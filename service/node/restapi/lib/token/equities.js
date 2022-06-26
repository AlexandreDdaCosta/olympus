const config = require('config');
const equitiesModel = require('../../api/models/equities');
const https = require('https'); 

async function TDAmeritrade(dataSource) {
  if (dataSource.KeyName != 'authorization_code') {
    return dataSource;
  }
  let tokenDocument;
  tokenDocument = await equitiesModel.findEquityTokenDocument(dataSource.DataSource);
  let now = new Date().getTime();
  if (tokenDocument != null) {
    // Return a valid access token with at least five remaining minutes
    if (tokenDocument.accessToken != null && tokenDocument.accessTokenExpiration != null) {
      if (now < (tokenDocument.accessTokenExpiration + 300)) {
	dataSource.Token = tokenDocument.accessToken;
	dataSource.Expiration = tokenDocument.accessTokenExpiration;
        return dataSource;
      }
    }
    if (tokenDocument.refreshToken != null && tokenDocument.refreshTokenExpiration != null && tokenDocument.refreshTokenExpiration > now) {
      if (tokenDocument.refreshTokenExpiration > (now + 604800)) {
        // Get a new access token if valid refresh token exists and expires in more than one week.
        // Put new access token code here
      }
      else {
        // Get a new access + refresh token if a valid refresh token exists and expires in less than one week
        // Put new access/refresh token code here
      }
    }
    else {
      // With no valid refresh token, use authorization code to generate new tokens
      if (tokenDocument.authorizationCode && tokenDocument.authorizationCode == dataSource.Token) {
        // Cannot re-use one-time tokens
	throw Error('Stale one-time authorization code for TD Ameritrade; must regenerate manually.');
      }
      //let code = 'ALEX';
      let code = dataSource.Token;
      let redirectUrl = encodeURIComponent(dataSource.RedirectUrl);
      let data = '&access_type=offline&client_id=' + dataSource.ClientID + '&code=' + code + '&grant_type=authorization_code&redirect_url=' + redirectUrl;
      console.log(data);
      let options = {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Content-Length': data.length
        },
        hostname: dataSource.Url,
        method: 'POST',
        path: '/v1/oauth2/token',
        port: 443
      };
      function getAmeritradeToken(options, data) {
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
      let res = await getAmeritradeToken(options, data);
      if (res.error) {
	throw Error('TD Ameritrade API error for ' + options['path'] + ': ' + res.error);
      }
      console.log(res);
      console.log(res.access_token);
      console.log(res.expires_in);
      console.log(res.refresh_token);
      console.log(res.refresh_token_expires_in);
      tokenDocument.authorizationCode == dataSource.Token;
      now = new Date().getTime();
      if (res.refresh_token) {
        tokenDocument.refreshToken = res.refresh_token;
        tokenDocument.refreshTokenExpiration = res.refresh_token_expires_in + now;
      }
      if (res.access_token) {
        tokenDocument.accessToken = res.access_token;
        tokenDocument.accessTokenExpiration = res.expires_in + now;
      }
      dataSource.Token = tokenDocument.access_token;
      dataSource.Expiration = tokenDocument.accessTokenExpiration;
    }
  }
  console.log(tokenDocument);
  console.log(dataSource);

  await equitiesModel.updateEquityTokenDocument('TDAmeritrade',tokenDocument);
  return dataSource;
}

module.exports = { TDAmeritrade };
