const config = require('config');
const equitiesModel = require('../../api/models/equities');

async function TDAmeritrade(dataSource) {
  if (dataSource.KeyName != 'authorization_code') {
    return dataSource;
  }
  let newTokenDocument = {
    'authorizationCode': 'foo',
    'accessCookie': null,
    'accessCookieExpiration': null,
    'refreshCookie': null,
    'refreshCookie_expiration': null,
  };
  let tokenDocument;
  tokenDocument = await equitiesModel.findEquityTokenDocument(dataSource.DataSource);
  let now = new Date();
  if (tokenDocument != null) {
    // Return a valid access token with at least five remaining minutes
    if (tokenDocument.accessCookie != null && tokenDocument.access_cookie_expiration != null) {
      console.log(now); 
    }
  }
  console.log(tokenDocument.authorizationCode);
  console.log(now);

  //newTokenDocument = {};
  await equitiesModel.addEquityTokenDocument('TDAmeritrade',newTokenDocument);
  return dataSource;
}

module.exports = { TDAmeritrade };
