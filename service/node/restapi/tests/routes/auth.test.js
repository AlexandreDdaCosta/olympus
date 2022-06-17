// sudo su -s /bin/bash -c 'source /srv/www/node/restapi/tests/test_source.sh; cd /srv/www/node/restapi; npm test ./tests/routes/auth.test.js' node

const config = require('config');
const fs = require('fs');
const https = require('https');
const os = require('os');

describe('Login, refresh token, and logout from node restapi.', () => {

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

  it('User authentication, missing user name.', async () => {
    let missingUsernameLoginPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let login_data = JSON.stringify({
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

    let data = await missingUsernameLoginPromise();
    expect(data.statusCode).toBe(400);
    expect(JSON.parse(data.body).message).toEqual('Login failed.');
  });

  it('User authentication, invalid user name.', async () => {
    let badUsernameLoginPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let login_data = JSON.stringify({
          username: 'foobar',
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

    let data = await badUsernameLoginPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
  });

  it('User authentication, bad password.', async () => {
    let badPasswordLoginPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let login_data = JSON.stringify({
          username: config.get('restapi.user'),
          password: 'foobar'
        });
        options['headers'] = {
          'Content-Type': 'application/json',
          'Content-Length': login_data.length
        };
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

    let data = await badPasswordLoginPromise();
    expect(data.statusCode).toBe(400);
    expect(JSON.parse(data.body).message).toEqual('Login failed.');
  });

  it('User authentication, invalid password.', async () => {
    let invalidPasswordLoginPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let login_data = JSON.stringify({
          username: config.get('restapi.user'),
          password: '1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890'
        });
        options['headers'] = {
          'Content-Type': 'application/json',
          'Content-Length': login_data.length
        };
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

    let data = await invalidPasswordLoginPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
  });

  it('User authentication, get access and refresh tokens.', async () => {
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

  it('User authentication, access test with missing authorization header.', async () => {
    let missingPingPromise = ((data) => {
      return new Promise((resolve, reject) => {
        options['headers'] = {
          'Content-Type': 'application/json'
        };
        options['method'] = 'GET';
        options['path'] = '/auth/ping';
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

    let data = await missingPingPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
  });

  it('User authentication, access test with bad authorization header.', async () => {
    let incompletePingPromise = ((data) => {
      return new Promise((resolve, reject) => {
        options['headers'] = {
          'Authorization': 'Bearing gifts',
          'Content-Type': 'application/json'
        };
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

    let data = await incompletePingPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
  });

  it('User authentication, access test with invalid access token.', async () => {
    let badPingPromise = ((data) => {
      return new Promise((resolve, reject) => {
        options['headers'] = {
          'Authorization': 'Bearer 1234567890',
          'Content-Type': 'application/json'
        };
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

    let data = await badPingPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
  });

  it('User authentication, access test with valid access token.', async () => {
    let pingPromise = ((data) => {
      return new Promise((resolve, reject) => {
        options['headers'] = {
          'Authorization': 'Bearer '+access_token,
          'Content-Type': 'application/json'
        };
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

    let data = await pingPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual('Give me a ping, Vasili. One ping only, please.');
  });

  it('User authentication, refresh tokens.', async () => {
    let refreshPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let refresh_data = JSON.stringify({
          refresh_token: refresh_token,
          username: config.get('restapi.user')
        });
        options['headers'] = {
          'Content-Type': 'application/json',
          'Content-Length': refresh_data.length
        };
        options['method'] = 'POST';
        options['path'] = '/auth/refresh';
        const req = https.request(options, (res) => {
          let body = '';
          res.on('data', (chunk) => (body += chunk.toString()));
          res.on('error', reject);
          res.on('end', () => { resolve({ statusCode: res.statusCode, headers: res.headers, body: body }); });
        });
        req.on('error', reject);
        req.write(refresh_data);
        req.end();
      });
    });

    let data = await refreshPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual('Refresh successful.');
  });

  it('User authentication, logout.', async () => {
    let logoutPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let logout_data = JSON.stringify({
          username: config.get('restapi.user')
        });
        options['headers'] = {
          'Content-Type': 'application/json',
          'Content-Length': logout_data.length
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
        req.write(logout_data);
        req.end();
      });
    });

    let data = await logoutPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual('Logout successful.');
  });

});

