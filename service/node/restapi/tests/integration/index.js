var chai = require('chai');
var http = require('http');
var expect = chai.expect;

describe('API index', function() {
    it('should return a 200 response code and welcome message', function() {
        var options = {
            host: '127.0.0.1',
            port: 8889,
            path: '/api/'
        };
        http.get(options, function(res) {
            console.log("Got response: " + res.statusCode);
            res.on("data", function(chunk) {
                console.log("BODY: " + chunk);
            });
        }).on('error', function(e) {
            console.log("Got error: " + e.message);
        });
        // expect(statusCode).to.equal(200);
    });
});

