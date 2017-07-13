var chai = require('chai');
var expect = chai.expect;
var fs = require('fs'); 
var https = require('https'); 
var request = require('request');

var url = 'http://zeus:8889/api/';
var message = 'Olympus back-end API listening for requests via express/node.js.'

describe('Connection to HTTP index page of API', function () {
  it('Should return HTTP code 200 with JSON reply including a "message" key.', function (done) {
    request.get(url, function (err, response, body){
      if (err) return done(err);
      expect(response.statusCode).to.equal(200);
      jsonobject = JSON.parse(response.body);
      expect(jsonobject['message']).to.equal(message);
      done();
    });
  });
});

var options = { 
    hostname: 'zeus', 
    port: 4443, 
    path: '/api', 
    method: 'get',
    ca: fs.readFileSync('/etc/ssl/certs/ca-crt.pem.pem')
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
