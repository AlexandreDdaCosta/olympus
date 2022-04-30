// sudo su -s /bin/bash -c 'export NODE_PATH=/usr/lib/nodejs:/usr/lib/node_modules:/usr/share/javascript; cd /srv/www/node/restapi; npm test ./tests/routes/index.test.js' node

const request = require('request');
const url = 'http://zeus:8889/';
const message = 'Olympus back-end API listening for requests via express/node.js.'

/*
Test direct backend connection, bypassing nginx
Command line: curl zeus:8889
*/

describe('Connection to HTTP index page of API, node port', () => {
  test('Should return HTTP code 200 with JSON reply including a "message" key.', () => {
    request.get(url, (error, response) => {
      expect(response.statusCode).toBe(200);
      jsonobject = JSON.parse(response.body);
      expect(jsonobject['message']).toBe(message);
    });
  });
});

/*
Test nginx proxy connection (https)
Command line: openssl s_client -connect zeus:4443 -cert /etc/ssl/localcerts/client-crt.pem -key /etc/ssl/localcerts/client-key.pem ... GET /
*/

const fs = require('fs'); 
const https = require('https'); 
const options = { 
    hostname: 'zeus', 
    port: 4443, 
    path: '/', 
    method: 'GET',
    key: fs.readFileSync('/etc/ssl/localcerts/client-key.pem'), 
    cert: fs.readFileSync('/etc/ssl/localcerts/client-crt.pem'), 
    ca: fs.readFileSync('/etc/ssl/certs/ca-crt-supervisor.pem.pem')
}; 
describe('Connection to HTTPS index page of API', () => {
  test('Should return HTTP code 200 with JSON reply including a "message" key.', () => {
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
