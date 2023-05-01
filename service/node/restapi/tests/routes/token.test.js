// sudo su -s /bin/bash -c 'source /srv/www/node/restapi/tests/test_source.sh; cd /srv/www/node/restapi; npm test ./tests/routes/token.test.js' node

const config = require('config');
const fs = require('fs');
const https = require('https');
const os = require('os');
const redis = require('redis');

describe('Access tokens for various data providers.', () => {

  let access_token;
  let expiration;
  let options;
  let password;
  let protocol;
  let refresh_token;
  let token;
  let url;
  let verifyOptions;

  options = { 
    ca: fs.readFileSync(config.get('ssl_server.ca_file')),
    cert: fs.readFileSync(config.get('ssl_server.client_cert_file')),
    hostname: config.get('ssl_server.host'),
    key: fs.readFileSync(config.get('ssl_server.client_key_file')),
    port: config.get('ssl_server.port')
  }; 

  beforeAll(async () => {
    if (os.userInfo().username != config.get('restapi.user')) {
      throw new Error('Test must be run under run user '+config.get('restapi.user'));
      process.exit(1);
    }
    try {
      password = fs.readFileSync(config.get('restapi.password_file'), 'utf8');
    } catch (err) {
        expect(data.statusCode).toBe(200);
      throw new Error(err);
      process.exit(1);
    }
  });

  it('Login, get access and refresh tokens.', async () => {
    let loginPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let login_data = JSON.stringify({
          username: config.get('restapi.user'),
          password: password
        });
        options['headers'] = {
          'Content-Type': 'application/json',
          'Content-Length': login_data.length
        };
        options['method'] = 'POST';
        options['path'] = '/auth/login';
        const req = https.request(options, (res) => {
          let body = '';
          res.on('data', (chunk) => (body += chunk.toString()));
          res.on('error', reject);
          res.on('end', () => { resolve({ statusCode: res.statusCode, headers: res.headers, body: body }); });
        });
        req.on('error', reject);
        req.write(login_data);
        req.end();
      });
    });

    let data = await loginPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual('Login successful.');
    access_token = JSON.parse(data.body).access_token;
    refresh_token = JSON.parse(data.body).refresh_token;
  });

  it('Omit provider name.', async () => {
    let tokenPromise = ((data) => {
      return new Promise((resolve, reject) => {
        options['headers'] = {
          'Authorization': 'Bearer ' + access_token,
          'Content-Type': 'application/json'
        };
        options['method'] = 'GET';
        options['path'] = '/token/equities';
        const req = https.request(options, (res) => {
          let body = '';
          res.on('data', (chunk) => (body += chunk.toString()));
          res.on('error', reject);
          res.on('end', () => { resolve({ statusCode: res.statusCode, body: body }); });
        });
        req.on('error', reject);
        req.end();
      });
    });

    let data = await tokenPromise();
    expect(data.statusCode).toBe(404);
  });

  it('Get Alpha Vantage access key.', async () => {
    let tokenPromise = ((data) => {
      return new Promise((resolve, reject) => {
        options['headers'] = {
          'Authorization': 'Bearer ' + access_token,
          'Content-Type': 'application/json'
        };
        options['method'] = 'GET';
        options['path'] = '/token/equities/AlphaVantage';
        const req = https.request(options, (res) => {
          let body = '';
          res.on('data', (chunk) => (body += chunk.toString()));
          res.on('error', reject);
          res.on('end', () => { resolve({ statusCode: res.statusCode, body: body }); });
        });
        req.on('error', reject);
        req.end();
      });
    });

    let data = await tokenPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual('Request successful.');
    protocol = JSON.parse(data.body).protocol;
    url = JSON.parse(data.body).url;
    token = JSON.parse(data.body).token;
    expiration = JSON.parse(data.body).expiration;
  });

  it('Get TD Ameritrade access key.', async () => {
    let tokenPromise = ((data) => {
      return new Promise((resolve, reject) => {
        options['headers'] = {
          'Authorization': 'Bearer ' + access_token,
          'Content-Type': 'application/json'
        };
        options['method'] = 'GET';
        options['path'] = '/token/equities/TDAmeritrade';
        const req = https.request(options, (res) => {
          let body = '';
          res.on('data', (chunk) => (body += chunk.toString()));
          res.on('error', reject);
          res.on('end', () => { resolve({ statusCode: res.statusCode, body: body }); });
        });
        req.on('error', reject);
        req.end();
      });
    });

    let data = await tokenPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual('Request successful.');
    protocol = JSON.parse(data.body).protocol;
    url = JSON.parse(data.body).url;
    token = JSON.parse(data.body).token;
    expiration = JSON.parse(data.body).expiration;
  });

  it('Test TD Ameritrade access key with connection.', async () => {
    let dataPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let connectOptions = { 
	  headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
          },
          hostname: url, 
          method: 'GET',
          path: '/v1/marketdata/$COMPX/movers?direction=up&change=percent',
          port: 443 
        };
        const req = https.request(connectOptions, (res) => {
          let body = '';
          res.on('data', (chunk) => (body += chunk.toString()));
          res.on('error', reject);
          res.on('end', () => { resolve({ statusCode: res.statusCode, body: body }); });
        });
        req.on('error', reject);
        req.end();
      });
    });

    let data = await dataPromise();
    expect(data.statusCode).toBe(200);
  });

  it('Logout.', async () => {
    let logoutPromise = ((data) => {
      return new Promise((resolve, reject) => {
        options['headers'] = {
          'Authorization': 'Bearer ' + refresh_token,
          'Content-Type': 'application/json'
        };
        options['method'] = 'DELETE';
        options['path'] = '/auth/logout';
        const req = https.request(options, (res) => {
          let body = '';
          res.on('data', (chunk) => (body += chunk.toString()));
          res.on('error', reject);
          res.on('end', () => { resolve({ statusCode: res.statusCode, headers: res.headers, body: body }); });
        });
        req.on('error', reject);
        req.end();
      });
    });
    
    let data = await logoutPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual('Logout successful.');
  });

});

