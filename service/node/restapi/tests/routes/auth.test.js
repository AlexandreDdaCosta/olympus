// sudo su -s /bin/bash -c 'source /srv/www/node/restapi/tests/test_source.sh; cd /srv/www/node/restapi; npm test ./tests/routes/auth.test.js' node

const config = require('config');
const fs = require('fs');
const https = require('https');
const os = require('os');
const redis = require('redis');

describe('Login, refresh token, and logout from node restapi.', () => {

  let access_token;
  let old_access_token;
  let old_refresh_token;
  let options;
  let password;
  let refresh_token;

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

  it('Missing user name.', async () => {
    let loginPromise = ((data) => {
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

    let data = await loginPromise();
    expect(data.statusCode).toBe(400);
    expect(JSON.parse(data.body).message).toEqual('Login failed.');
  });

  it('Invalid user name.', async () => {
    let loginPromise = ((data) => {
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

    let data = await loginPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
  });

  it('Bad password.', async () => {
    let loginPromise = ((data) => {
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

    let data = await loginPromise();
    expect(data.statusCode).toBe(400);
    expect(JSON.parse(data.body).message).toEqual('Login failed.');
  });

  it('Invalid password.', async () => {
    let loginPromise = ((data) => {
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

    let data = await loginPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
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

  it('Access with missing authorization header.', async () => {
    let pingPromise = ((data) => {
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

    let data = await pingPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
  });

  it('Access with bad authorization header.', async () => {
    let pingPromise = ((data) => {
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

    let data = await pingPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
  });

  it('Access with invalid access token.', async () => {
    let pingPromise = ((data) => {
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

    let data = await pingPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
  });

  it('Access with valid access token.', async () => {
    let pingPromise = ((data) => {
      return new Promise((resolve, reject) => {
        options['headers'] = {
          'Authorization': 'Bearer ' + access_token,
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

  it('Access with valid refresh token.', async () => {
    let pingPromise = ((data) => {
      return new Promise((resolve, reject) => {
        options['headers'] = {
          'Authorization': 'Bearer ' + refresh_token,
          'Content-Type': 'application/json'
        };
        options['path'] = '/auth/pingr';
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

  it('Refresh tokens, missing user name.', async () => {
    let refreshPromise = ((data) => {
      return new Promise((resolve, reject) => {
        options['headers'] = {
          'Authorization': 'Bearer ' + refresh_token,
          'Content-Type': 'application/json'
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
        req.end();
      });
    });

    let data = await refreshPromise();
    expect(data.statusCode).toBe(400);
    expect(JSON.parse(data.body).message).toEqual('Refresh failed.');
  });

  it('Refresh tokens, missing token.', async () => {
    let refreshPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let refresh_data = JSON.stringify({
          username: config.get('restapi.user')
        });
        options['headers'] = {
          'Content-Type': 'application/json',
          'Content-Length': refresh_data.length
        };
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
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
  });

  it('Refresh tokens, token/username mismatch.', async () => {
    let refreshPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let refresh_data = JSON.stringify({
          username: 'foobar'
        });
        options['headers'] = {
          'Authorization': 'Bearer ' + refresh_token,
          'Content-Type': 'application/json',
          'Content-Length': refresh_data.length
        };
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
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
  });

  it('Refresh tokens, mixed up token.', async () => {
    let refreshPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let refresh_data = JSON.stringify({
          username: config.get('restapi.user')
        });
        options['headers'] = {
          'Authorization': 'Bearer ' + access_token,
          'Content-Type': 'application/json',
          'Content-Length': refresh_data.length
        };
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
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
  });

  it('Refresh tokens.', async () => {
    let refreshPromise = ((data) => {
      return new Promise((resolve, reject) => {
        let refresh_data = JSON.stringify({
          username: config.get('restapi.user')
        });
        options['headers'] = {
          'Authorization': 'Bearer ' + refresh_token,
          'Content-Type': 'application/json',
          'Content-Length': refresh_data.length
        };
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

    // Here we pause execution for a second which is the time resolution for all tokens.
    // Without a pause, the new tokens may be identical to the old ones!
    function freeze(time) {
      const stop = new Date().getTime() + time;
      while(new Date().getTime() < stop);       
    }
    freeze(1000);
    let data = await refreshPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual('Refresh successful.');
    old_access_token = access_token;
    old_refresh_token = refresh_token;
    access_token = JSON.parse(data.body).access_token;
    refresh_token = JSON.parse(data.body).refresh_token;
  });

  it('Access with old access token (after refresh).', async () => {
    let pingPromise = ((data) => {
      return new Promise((resolve, reject) => {
        options['headers'] = {
          'Authorization': 'Bearer ' + old_access_token,
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

    let data = await pingPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
  });

  it('Access with valid new access token.', async () => {
    let pingPromise = ((data) => {
      return new Promise((resolve, reject) => {
        options['headers'] = {
          'Authorization': 'Bearer ' + access_token,
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

  it('Logout with invalid token (old refresh token).', async () => {
    let logoutPromise = ((data) => {
      return new Promise((resolve, reject) => {
        options['headers'] = {
          'Authorization': 'Bearer ' + old_refresh_token,
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
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
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

  it('Access after logout with invalidated access token.', async () => {
    let pingPromise = ((data) => {
      return new Promise((resolve, reject) => {
        options['headers'] = {
          'Authorization': 'Bearer ' + access_token,
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

    let data = await pingPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
  });

  it('Logout with invalid token (refresh token).', async () => {
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
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual('Access denied.');
  });

});

