var chai = require('chai');
var http = require('http');
var request = require('request');
var expect = chai.expect;

describe('Index page of API, basic functioning', function () {
  it('should return HTTP code 200 with pre-formatted JSON reply', function (done) {
    var options = {
      host: '127.0.0.1',
      port: 8889,
      path: '/api/'
    };
    http.get(options, function (response){
      response.setEncoding('utf8');
      var body = '';
      response.on('data', function (chunk) {
        console.log('DATABODY: ' + chunk);
        body += chunk;
      });
      response.on('end', function () {
        console.log('PREBODY: ' + body);
        expect(body).to.not.equal(200);
        console.log('POSTBODY: ' + body);
      });
      console.log('precode');
      console.log(response.statusCode);
      expect(response.statusCode).to.equal(200);
      expect(response.statusCode).to.not.equal(0);
      done();
    });
  });
});
