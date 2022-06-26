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
      console.log('PREPROMISE');
      let AmeritradePromise = ((data) => {
        return new Promise((resolve, reject) => {
          let request_data = JSON.stringify({
	    access_type: 'offline',
	    code: 'foo',
	    client_id: 'ZW44GWR4U1YPJXZBIN49TXRVPCUSMAMS',
	    grant_type: 'authorization_code',
	    redirect_url: 'https://127.0.0.1'
          });
          let options = {};
          options['headers'] = {
            'Content-Length': request_data.length,
            'Content-Type': 'application/json'
          };
          options['hostname'] = 'https://api.tdameritrade.com'
          //options['hostname'] = dataSource.Url,
          options['method'] = 'POST';
	  options['path'] = '/vi/oauth2/token';
          const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => (body += chunk.toString()));
            res.on('error', reject);
            res.on('end', () => { resolve({ body: body }); });
          });
          req.on('error', reject);
          req.end();
        });
      });
      let data = await AmeritradePromise();
      console.log(data);
    }
  }
  console.log(tokenDocument.authorizationCode);
  console.log(dataSource.Token);
  console.log(now);

  await equitiesModel.updateEquityTokenDocument('TDAmeritrade',tokenDocument);
  return dataSource;
}

module.exports = { TDAmeritrade };
