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
      password = fs.readFileSync(config.get('mongodb.password_file'), 'utf8');
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

    async function do_bad_username_login() {
        let data = await missingUsernameLoginPromise();
        expect(data.statusCode).toBe(400);
	expect(JSON.parse(data.body).message).toEqual('Login failed.');
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
        expect(data.statusCode).toBe(400);
	expect(JSON.parse(data.body).message).toEqual('Login failed.');
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
    }

    (async () => await do_login())()
  });

/*
  it('User authentication, get access and refresh tokens.', async () => {
    function doLogin() {
      return new Promise((resolve, reject) => {
        let login_message = 'Login';
        let login_data = JSON.stringify({
          username: config.get('mongodb.user'),
          password: password
        });
        options['headers'] = {
          'Content-Type': 'application/json',
          'Content-Length': login_data.length
        };
        options['method'] = 'POST';
        options['path'] = '/auth/login';
	console.log('HERE');
        let login_request = https.request(options, (response) => {
	  let login_data = [];
          response.on('data', (chunks) => {
            login_data.push(chunks);
          });
          response.on('end', () => {
            let response_body = Buffer.concat(login_data);
            resolve(response_body.toString());
          });
          response.on('error', (error) => {
            reject(error);
          });
        });
        login_request.end();
      });
    }

    async function authLoginRequest(request) {
      try {
        let http_promise = doLogin();
        let response_body = await http_promise;
        console.log(response_body);
      }
      catch(error) {
        console.log(error);
      }
    }

    authLoginRequest();

  });

  it('User authentication, get access and refresh tokens.', async () => {
    let login_message = 'Login';
    let login_data = JSON.stringify({
      username: config.get('mongodb.user'),
      password: password
    });
    options['headers'] = {
      'Content-Type': 'application/json',
      'Content-Length': login_data.length
    };
    options['method'] = 'POST';
    options['path'] = '/auth/login';
    let login_request = await https.request(options, function(result) {
      expect(result.statusCode).toBe(200);
      result.on('login_data', d => {
        process.stdout.write(d);
      });
    });
    login_request.on('error', err => {
      throw new Error(err);
    });
    login_request.write(login_data);
    login_request.end();
  });

  it('User authentication, refresh tokens.', async () => {
    let refresh_message = 'Refresh';
    options['method'] = 'POST';
    options['path'] = '/auth/refresh';
    let refresh_request = await https.request(options, (response) => { 
      expect(response.statusCode).toBe(200);
      response.on('data', (d) => {
        jsonobject = JSON.parse(d);
        expect(jsonobject['message']).toBe(refresh_message);
      });
    });
    refresh_request.end();
  });

  it('User authentication, logout.', async () => {
    let logout_message = 'Logout';
    options['method'] = 'DELETE';
    options['path'] = '/auth/logout';
    let logout_request = await https.request(options, (response) => { 
      expect(response.statusCode).toBe(200);
      response.on('data', (d) => {
        jsonobject = JSON.parse(d);
        expect(jsonobject['message']).toBe(logout_message);
      });
    });
    logout_request.end();
  });
*/

});

