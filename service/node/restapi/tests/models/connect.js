// Excerpted from http://mongodb.github.io/node-mongodb-native/2.2/quick-start/quick-start/

var chai = require('chai');
var expect = chai.expect;

var MongoClient = require('mongodb').MongoClient;
var url = 'mongodb://127.0.0.1:27017/olympus';
var test_collection = 'test'

var findDocuments = function(db, callback) {
  var collection = db.collection(test_collection);
  collection.find({}).toArray(function(err, docs) {
    expect(err).to.equal(null);
    console.log("Found the following records");
    console.log(docs)
    callback(docs);
  });
}
var insertDocuments = function(db, callback) {
  var collection = db.collection(test_collection);
  collection.insertMany([
    {a : 1}, {a : 2}, {a : 3}
  ], function(err, result) {
    expect(err).to.equal(null);
    expect(result.result.n).to.equal(3);
    expect(result.ops.length).to.equal(3);
    console.log("Inserted three documents into test collection");
    callback(result);
  });
}

describe('MongoDB basic connection and operations', function () {
  it('Connect to olympus database, manage test document', function (done) {
    MongoClient.connect(url, function(err, db) {
      expect(err).to.equal(null);
      insertDocuments(db, function() {
        findDocuments(db, function() {
          db.close();
          done();
        });
      });
    });
  });
});

