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
      let redirectUrl = encodeURIComponent('https://127.0.0.1');
      let data = '&access_type=offline&client_id=ZW44GWR4U1YPJXZBIN49TXRVPCUSMAMS&code=foo&grant_type=authorization_code&redirect_url=' + redirectUrl;
      let options = {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Content-Length': data.length
        },
        hostname: 'api.tdameritrade.com',
        method: 'POST',
        path: '/v1/oauth2/token',
        port: 443
      };
      //options['hostname'] = dataSource.Url;
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
      console.log(data);
      let res = await getAmeritradeToken(options, data);
      console.log(res);
    }
  }
  console.log(tokenDocument.authorizationCode);
  console.log(dataSource.Token);
  console.log(now);

  await equitiesModel.updateEquityTokenDocument('TDAmeritrade',tokenDocument);
  return dataSource;
}

module.exports = { TDAmeritrade };
