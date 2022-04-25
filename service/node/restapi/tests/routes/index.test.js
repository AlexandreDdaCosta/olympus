const request = require('request');

const url = 'http://zeus:8889/';
const message = 'Olympus back-end API listening for requests via express/node.js.'

/*
Test direct backend connection, bypassing nginx
Command line: curl localhost:8889
*/

describe('Connection to HTTP index page of API, node port', () => {
  test('Should return HTTP code 200 with JSON reply including a "message" key.', () => {
    request.get(url, function (err, response){
      if (err) return (err);
      expect(response.statusCode).toBe(200);
      jsonobject = JSON.parse(response.body);
      expect(jsonobject['message']).toBe(message);
    });
  });
});

/*
Test nginx proxy connection
Command line: curl https://zeus:4443 ????? ALEX
curl -k https://zeus:4443 -v -key /etc/ssl/localcerts/client-key.pem -cacert /etc/ssl/certs/ca-crt-supervisor.pem.pem -cert /etc/ssl/localcerts/client-crt.pem
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
    const req = https.request(options, function (err, resp) { 
      if (err) return (err);
      expect(resp.statusCode).toBe(200);
      jsonobject = JSON.parse(resp.body);
      expect(jsonobject['message']).toBe(message);
    });
    req.end();
  }); 
});
