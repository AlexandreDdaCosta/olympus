// sudo su -s /bin/bash -c 'source /srv/www/node/restapi/tests/test_source.sh; cd /srv/www/node/restapi; npm test ./tests/routes/auth.test.js' node

const fs = require('fs');
const os = require('os');
const https = require('https'); 

describe('Login, refresh token, and logout from node restapi.', () => {
  let message;
  let options;
  let password;

  options = { 
    hostname: 'zeus', 
    port: 4443, 
    key: fs.readFileSync('/etc/ssl/localcerts/client-key.pem'), 
    cert: fs.readFileSync('/etc/ssl/localcerts/client-crt.pem'), 
    ca: fs.readFileSync('/etc/ssl/certs/ca-crt-supervisor.pem.pem')
  }; 

  if (os.userInfo().username != config.get('mongodb.user')) {
    throw new Error('Test must be run under run user '+config.get('mongodb.user'));
    process.exit(1);
  }
  try {
    password = fs.readFileSync(config.get('mongodb.password_file'), 'utf8');
  } catch (err) {
    throw new Error(err);
    process.exit(1);
  }

  it('User authentication, get access and refresh tokens.', async () => {
    message = 'TEST MESSAGE'
    options['method'] = 'POST';
    options['path'] = '/auth';
    const https_request = https.request(options, (response) => { 
      expect(response.statusCode).toBe(200);
      response.on('data', (d) => {
        jsonobject = JSON.parse(d);
        expect(jsonobject['message']).toBe(message);
      });
    });
    https_request.end();
  });

});

