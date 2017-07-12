var chai = require('chai');
var expect = chai.expect;
var request = require('request');

var url = 'https://www.laikasden.com/';

describe('Connection to interface domain', function () {
  it('should return HTTP code 200.', function (done) {
    request.get(url, function (err, response, body){
      if (err) return done(err);
      expect(response.statusCode).to.equal(200);
      done();
    });
  });
});
