// sudo su -s /bin/bash -c 'source /srv/www/node/restapi/tests/test_source.sh; cd /srv/www/node/restapi; npm test ./tests/routes/auth.test.js' node

const config = require('config');
const fs = require('fs');
const os = require('os');
const https = require('https'); 

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
    if (os.userInfo().username != config.get('mongodb.user')) {
      throw new Error('Test must be run under run user '+config.get('mongodb.user'));
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

    async function do_missing_username_login() {
      let data = await missingUsernameLoginPromise();
      expect(data.statusCode).toBe(400);
      expect(JSON.parse(data.body).message).toEqual('Login failed.');
    }

    (async () => await do_missing_username_login())()
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

    async function do_bad_username_login() {
      let data = await badUsernameLoginPromise();
      expect(data.statusCode).toBe(401);
      expect(JSON.parse(data.body).message).toEqual('Access denied.');
    }

    (async () => await do_bad_username_login())()
  });

  it('User authentication, bad password.', async () => {
    let badPasswordLoginPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let login_data = JSON.stringify({
          username: config.get('mongodb.user'),
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

    async function do_bad_password_login() {
      let data = await badPasswordLoginPromise();
      expect(data.statusCode).toBe(400);
      expect(JSON.parse(data.body).message).toEqual('Login failed.');
    }

    (async () => await do_bad_password_login())()
  });

  it('User authentication, invalid password.', async () => {
    let invalidPasswordLoginPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let login_data = JSON.stringify({
          username: config.get('mongodb.user'),
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

    async function do_invalid_password_login() {
      let data = await invalidPasswordLoginPromise();
      expect(data.statusCode).toBe(401);
      expect(JSON.parse(data.body).message).toEqual('Access denied.');
    }

    (async () => await do_invalid_password_login())()
  });

  it('User authentication, get access and refresh tokens.', async () => {
    let loginPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let login_data = JSON.stringify({
          username: config.get('mongodb.user'),
          password: password
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

    async function do_login() {
      let data = await loginPromise();
      expect(data.statusCode).toBe(200);
      expect(JSON.parse(data.body).message).toEqual('Login successful.');
      access_token = JSON.parse(data.body).access_token;
      refresh_token = JSON.parse(data.body).refresh_token;
      // ALEX console.log(access_token);
      // ALEX console.log(refresh_token);
    }

    (async () => await do_login())()
  });

  it('User authentication, refresh tokens.', async () => {
    let refreshPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let refresh_data = JSON.stringify({
          username: config.get('mongodb.user')
        });
        options['headers'] = {
          'Content-Type': 'application/json',
          'Content-Length': refresh_data.length
        };
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

    async function do_refresh() {
      let data = await refreshPromise();
      expect(data.statusCode).toBe(200);
      expect(JSON.parse(data.body).message).toEqual('Refresh successful.');
    }

    (async () => await do_refresh())()
  });

  it('User authentication, logout.', async () => {
    let logoutPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let logout_data = JSON.stringify({
          username: config.get('mongodb.user')
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

    async function do_logout() {
      let data = await logoutPromise();
      expect(data.statusCode).toBe(200);
      expect(JSON.parse(data.body).message).toEqual('Logout successful.');
    }

    (async () => await do_logout())()
  });

});

