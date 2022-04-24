const chai = require('chai');
const expect = chai.expect;
const fs = require('fs'); 
const https = require('https'); 
const request = require('request');

const url = 'http://zeus:8889/api/';
const message = 'Olympus back-end API listening for requests via express/node.js.'

describe('Connection to HTTP index page of API, node port', () => {
  test('Should return HTTP code 200 with JSON reply including a "message" key.', () => {
    request.get(url, function (err, response, body){
      if (err) return (err);
      expect(response.statusCode).to.equal(200);
      jsonobject = JSON.parse(response.body);
      expect(jsonobject['message']).toBe(message);
    });
  });
});

/*
var options = { 
    hostname: 'zeus', 
    port: 4443, 
    path: '/api', 
    method: 'get',
    key: fs.readFileSync('/etc/ssl/localcerts/client-key.pem'), 
    cert: fs.readFileSync('/etc/ssl/localcerts/client-crt.pem'), 
    ca: fs.readFileSync('/etc/ssl/certs/ca-crt-supervisor.pem.pem')
}; 
describe('Connection to HTTPS index page of API', function () {
  it('Should return HTTP code 200 with JSON reply including a "message" key.', function (done) {
    var request = https.request(options, function(response) { 
      expect(response.statusCode).to.equal(200);
      response.on('data', function(data) { 
        jsonobject = JSON.parse(data);
        expect(jsonobject['message']).to.equal(message);
      }); 
      done();
    });
    request.end();
  }); 
}); 
*/
