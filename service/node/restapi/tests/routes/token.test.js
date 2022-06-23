// sudo su -s /bin/bash -c 'source /srv/www/node/restapi/tests/test_source.sh; cd /srv/www/node/restapi; npm test ./tests/routes/auth.test.js' node

const config = require('config');
const fs = require('fs');
const https = require('https');
const os = require('os');
const redis = require('redis');

describe('Access tokens for various data providers.', () => {

  let access_token;
  let options;
  let password;
  let refresh_token;

  options = { 
    hostname: 'zeus', 
    port: 4443, 
    key: fs.readFileSync('/etc/ssl/localcerts/client-key.pem'), 
    cert: fs.readFileSync('/etc/ssl/localcerts/client-crt.pem'), 
    ca: fs.readFileSync('/etc/ssl/certs/ca-crt-supervisor.pem.pem')
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

  afterAll(async () => {
        options['headers'] = {
          'Content-Type': 'application/json'
        };
        options['method'] = 'GET';
        options['path'] = '/auth';
        let req = https.request(options, (res) => {
          let body = '';
          res.on('data', (chunk) => (body += chunk.toString()));
          res.on('end', () => { console.log(res.statusCode); });
        });
        req.end();
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
        options['path'] = '/token';
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
        options['path'] = '/token/AlphaVantage';
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
    provider_token = JSON.parse(data.body).provider_token;
    console.log(provider_token);
    expiration_date = JSON.parse(data.body).expiration_date;
    console.log(expiration_date);
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

