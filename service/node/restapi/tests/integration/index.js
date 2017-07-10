var chai = require('chai');
var request = require('request');
var expect = chai.expect;

var url = 'http://127.0.0.1:8889/api/';
var secureurl = 'https://127.0.0.1:4443/api/';
var message = 'Olympus back-end API listening for requests via express/node.js.'

describe('Connection to HTTP index page of API', function () {
  it('should return HTTP code 200 with JSON reply including a "message" key', function (done) {
    request.get(url, function (err, response, body){
      if (err) return done(err);
      expect(response.statusCode).to.equal(200);
      jsonobject = JSON.parse(response.body);
      expect(jsonobject['message']).to.equal(message);
      done();
    });
  });
});

describe('Connection to HTTPS index page of API', function () {
  it('should return HTTP code 200 with JSON reply including a "message" key', function (done) {
    request.get(secureurl, function (err, response, body){
      if (err) return done(err);
      expect(response.statusCode).to.equal(200);
      jsonobject = JSON.parse(response.body);
      expect(jsonobject['message']).to.equal(message);
      done();
    });
  });
});
