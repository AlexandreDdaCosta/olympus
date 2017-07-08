var chai = require('chai');
var expect = chai.expect;

var MongoClient = require('mongodb').MongoClient;
var url = 'mongodb://127.0.0.1:27017/olympus';

describe('Basic connection to MongoDB on localhost', function () {
  it('Connect to olympus MongoDB database on localhost', function () {
    MongoClient.connect(url, function(err, db) {
      expect(err).to.equal(null);
      db.close();
    });
  });
});
