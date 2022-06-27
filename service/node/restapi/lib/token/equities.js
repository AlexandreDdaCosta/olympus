const config = require('config');
const equitiesModel = require('../../api/models/equities');
const https = require('https'); 

async function TDAmeritrade(dataSource) {
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

    //let code = dataSource.Token; // Already url encoded
    let code = 'do3WihBV7gCrLrSC4q27UyHK2Xg9fLOaE7Tc9rr1wBqkOt5zOpjQyKO2RiyVzmgEBdrZeo8pTDUHqyQrhsHx4o1SzzS1TQ%2BwY8BzkMJrqlZPmYT426MbY4LvBb13wL%2FX41yELkDWQkL2WbQ2VUyc%2FfQq0dCk5kahKP93wk3zVqjv1r4WkAT9xqWxdUbZqXFjeFv0vuM0yHtV1t5eMQxeY6mdGiaPdvONKzoF8rotE1htVX7zsB3BPfv%2FoceCbcTJ97NEXS8X6b4qSjPj7XhBtF27bK1K7%2FQ9CzpjS96fKKs9AB18NkAipvHjs0%2BGsrmG%2BZR0Yc6UrEbtoGRbuF1NKyVJgjqwUpgCS8NSK5VIzVD0x9Vpt27o7ckbuF70frayVrughXxzxRI5aMhB%2BdjBEdSjeS%2F%2Bzv1SGoyj3gGUOxuhjO2BAt9XkTQqzks100MQuG4LYrgoVi%2FJHHvlmSeAtulXHOAnyvZLYarIJ04XRH4MT5R2noH2%2FVm3gH2OJXfS6LXMZQDa836dfS4cN0Qb3TnfQBZUsGHeL2D8OCJkVyN82zjqGw7Y0WqRInSKF6k0iKVfL3ESvpsg%2BNIwJi8rlaV7PsvFUOZ%2F1KlFyCdBTTnA29YioVG6NO0oKyS3%2FdWPTS4uC8CEUYJsYEKiwcDOpN6IHmRq4X%2FaMpcVy2TfgkUum5Z1EmYfYv5fmfaT2GaGEnn8XP%2F3Sz0HOvoorW4PZi8%2FVT5IQ8gDjpw0AddmP5RFxy0hH%2B04ULIDMKVcVfrQuRfALiryVAmjNdE4ZQSLHrgl%2FXByuMwkFrcyVpdaMpnmfT3qWkuwFvWPjmlsfyu2v%2FfypgS9inL4SSbza01hxXPUBuBLFeu0QsinF1jxQiIvqzTS%2FWXf7rFN8m59eeIQBuSi4Rqhgbs%3D212FD3x19z9sWBHDJACbC00B75E';
    let redirectUri = encodeURIComponent(dataSource.RedirectUrl);
    //let data = '&access_type=offline&client_id=' + dataSource.ClientID + '&code=' + code + '&grant_type=authorization_code&redirect_url=' + redirectUrl;
    let data = 'grant_type=authorization_code&refresh_token=&access_type=offline&code=' + code + '&client_id=' + dataSource.ClientID + '&redirect_uri=' + redirectUri;
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
    console.log(options);
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
    //let res = await getAmeritradeToken(options, data);
    let res = {
  access_token: 'BP95E6QzFNTAwlsHB5+6jCFNu3tAyGWboC+2sPlC/bdYBBxF2Su0JL4MNy5Nc/jCYXNh1IDPk42PzRtSc+EW3cte0L1DgU6esgmcjglwPQKmNv917C1algail0yvCNvGACi5QVQwYDn4wkgykCzdghBxT+TQmoHK9daLTAhFzIYJt6xYsEt9cP3HH/EIQwbjROOFfkw7yCbaVa/Z1BciCUr8pRnhZSf0hYlpRZQc/WFbsHEtxc4kKquZHSS+0bvBzQ8ds3Ybn7Qs5BjpDVecpJMgmwN3tfr7u/O41+juGW35n85uHXFWz0iMexoJSrbIwHnFZ0fZVsubZhZC4g95GnkIVMOiA8CPnurexaSXM8Fxh9GIFPJmWJHVskEHsdzl0Pag2exyEYOYKjwjVGfVJPY33MX5kZZkNHeB2+wTXwTBrS+NPJTO2kWtTEASkZP0ZOpK5Q1URxEVA3P+zILnWEA/a8xf9s4ftV3+Ny5x9C5CdMPKUgzpwYnto2f97/WPV4tlf7O6XACIlChrhhWcCQ27ljdnOXpZYMYCUmAXs5AZvAoiTA2axqa/ZoiUq14eztiNr8jzFDd3Lfr7i8337ZWFzcvfIis2rAmAw100MQuG4LYrgoVi/JHHvlV/yVx9yqjkswm4ZAcXqdt3dUxOOPFBt38ld7xqCWhfQMhnHc3FlaTocMvN8dOgWpcTBnHvLks2SDBixXvmvcKk2LeCJHgT2zkgjbSB/Sr9Gh87m+szsWBwIN/GVF66OUB+9oZrQE2guxynNEktOdYxScnsqauSmx+hxlNosszklBD6+KIj6wCutvNF6WQew0NbNvQ0vvK+qxCFpfj8tb/525PECvGc4ZdUWm0ppz7mfpIkFFdIPkW+g2kPJTBmWqmXzLeqsZULACjXNFNCC92HYyXi/sAkwXfe38OQgHagQLo/cJ96RCCo6AbN9AjrKAy5Ly8faRIF+YUGWO+SB6oB9GRPLpNVInRkSSTazh8AAgtgULQ5SGF58+dZkoKcTR8HE0u4vd7M+bMnndtjb2btcRZ+b/u7FIEqQpBtE/htUdVGJ28Vj5H8ub0Vpnjwen+pDkXP7DsVsC9hMx2NfX+LiMd4MrL0aycdrb/d1llXAfyZstsCKrW88HKsjYm9GzPasp7YJNlq7xDoMq+eDUGBAUhpiOpoxCiJyOHXnq4UAjVW2OEkdnkh863OguupjxJ3OhogIxfrcihjfMbRHlpx/To9Vk50YYlaW0PQ212FD3x19z9sWBHDJACbC00B75E',
  refresh_token: 'ilriWmwS+eSMk7642P+t0rJ8A65LNlJX3zglOa1DebDo0TrC2yA13nY7gkUsSIs+e94pwYw63FasL2UqY4hviI6GSj3BIh8+ZEh858j1CSPxrrgks68Q11xWKBdAAEdoy6XdXcNV3wKIVYviPyvoPgJm++9UGMKCA51iWTwMQlnMyxYRU6jbxp7rTIezBjLXrTmpLmghhmp291La7CqdVPfUjcHlSUZILGq/D5ezyfR9SEU93mZnodoZK75kY1acBmvxUKbYJDJyAhLH2cStW/Zr44xNP2gje2bNNGANlssJXuV1AGfAGTz+JC7neajhpXj32GGv7Q7fH2Atg4Qp8RrEObruZxxStnxPGCiv6pcLl6x6xI5xGglmrh4sZX4xVSFxgfd2rsAgdmsEEPLYV0o84Nhm+TWxSHPtvlGA4r2B8iZOSUqozl/lnHC100MQuG4LYrgoVi/JHHvlmG+5osnjglcp7z46GeV6fuo4WMnyczAhH8sr1Qae5rck5WeNOdBRBGBOXGUlhbW4Gj/G/hiwffFQBprFEpTW//3IqUYysYiV0XXSlk+0S/RytVxlcdBqcAkKY1/fojw/1KlAqEiz2H0mhkOLzRbBvMRB3jOxrRaNyODKw4YIJPeAAtg1J9gX09/gelwl5tMoB5Hy5x64+pd0+L9LDYgKjFFzSOy7THqwJkeHEq5DeUnwKmTFuLkW5szXMUkEa6/3XTbgfyd8Q405O06EmX0MW8710pOk3xt05yLl0eo3GpUkrgmSPq9MtgARprV3eS9dKpR2COq/4gsRskht+ROPxEAoo4PXIN3HQjhpe+yuDBk5oSubCUBzX1EDQgSWohFX61Qe/3iSM0OAd4GSuh4nrp4aEk+XRlKX4IZCZ2RQtSWvG9pX4NhN+DTJpPs=212FD3x19z9sWBHDJACbC00B75E',
  scope: 'PlaceTrades AccountAccess MoveMoney',
  expires_in: 1800,
  refresh_token_expires_in: 7776000,
  token_type: 'Bearer'
};
    console.log(res);
    now = parseInt(new Date().getTime()/1000);
    console.log(now);
    if (res.error) {
      throw Error('TD Ameritrade API error for ' + options['path'] + ': ' + res.error);
    }
    console.log(res.access_token);
    console.log(res.expires_in);
    console.log(res.refresh_token);
    console.log(res.refresh_token_expires_in);
    now = parseInt(new Date().getTime()/1000);
    tokenDocument = {};
    tokenDocument.accessToken = res.access_token;
    tokenDocument.accessTokenExpiration = res.expires_in + now;
    tokenDocument.authorizationCode == dataSource.Token;
    tokenDocument.refreshToken = res.refresh_token;
    tokenDocument.refreshTokenExpiration = res.refresh_token_expires_in + now;
    dataSource.Token = tokenDocument.access_token;
    dataSource.Expiration = tokenDocument.accessTokenExpiration;
  }
  else {
    if (tokenDocument.refreshTokenExpiration > (now + 604800)) {
      // Get a new access token if valid refresh token exists and expires in more than one week.
      // Put new access token code here
    }
    else {
      // Get a new access + refresh token if a valid refresh token exists and expires in less than one week
      // Put new access/refresh token code here
    }
  }
      
/*
    // Return a valid access token with at least five remaining minutes
    if (tokenDocument.accessToken != null && tokenDocument.accessTokenExpiration != null) {
      if (now < (tokenDocument.accessTokenExpiration + 300)) {
	dataSource.Token = tokenDocument.accessToken;
	dataSource.Expiration = tokenDocument.accessTokenExpiration;
        return dataSource;
      }
*/

  console.log(tokenDocument);
  console.log(dataSource);

  await equitiesModel.updateEquityTokenDocument('TDAmeritrade',tokenDocument);
  return dataSource;
}

module.exports = { TDAmeritrade };
