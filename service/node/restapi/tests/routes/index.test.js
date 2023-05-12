// sudo su -s /bin/bash -c 'source /srv/www/node/restapi/tests/test_source.sh; cd /srv/www/node/restapi; npm test ./tests/routes/index.test.js' node

const config = require('config');
const { request } = require('urllib');
const url = 'http://' + config.get('server.host') + ':' + config.get('server.port') + '/';
const message = 'Olympus back-end API listening for requests via express/node.js.'

/*
Test direct backend connection, bypassing nginx
Command line: curl zeus:8889
*/

describe('Connection to HTTP index page of API, node port', () => {
  test('Should return HTTP code 200 with JSON reply including a "message" key.', () => {
    request(url, { method: 'GET' }, function (err, data, response) {
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
    ca: fs.readFileSync(config.get('ssl_server.ca_file')),
    cert: fs.readFileSync(config.get('ssl_server.client_cert_file')),
    hostname: config.get('ssl_server.host'),
    key: fs.readFileSync(config.get('ssl_server.client_key_file')),
    method: 'GET',
    path: '/', 
    port: config.get('ssl_server.port')
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
