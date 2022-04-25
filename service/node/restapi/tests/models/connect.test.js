// Excerpted from http://mongodb.github.io/node-mongodb-native/2.2/quick-start/quick-start/

var chai = require('chai');
var expect = chai.expect;
var fs = require('fs');

var ca_cert = fs.readFileSync('/usr/local/share/ca-certificates/ca-crt-supervisor.pem.crt');
var ssl_cert = fs.readFileSync('/etc/ssl/localcerts/client-crt.pem');
var ssl_key = fs.readFileSync('/etc/ssl/localcerts/client-key.pem');
var MongoClient = require('mongodb').MongoClient;
var options =  {
  server: {
    sslCA: ca_cert,
    sslCert: ssl_cert,
    sslKey: ssl_key
  }
};
var url = 'mongodb://127.0.0.1:27017/olympus?tls=true';
var test_collection = 'test'

var findDocuments = function(db, callback) {
  var collection = db.collection(test_collection);
  collection.find({}).toArray(function(err, docs) {
    expect(err).to.equal(null);
    expect(docs.length).to.equal(3);
    expect(docs[0]['a']).to.equal(1);
    expect(docs[1]['a']).to.equal(2);
    expect(docs[1]['b']).to.equal(undefined);
    expect(docs[2]['a']).to.equal(3);
    console.log("Found the following records:");
    callback();
  });
}
var filterDocuments = function(db, callback) {
  var collection = db.collection(test_collection);
  collection.find({'a': 1}).toArray(function(err, docs) {
    expect(err).to.equal(null);
    expect(docs.length).to.equal(1);
    expect(docs[0]['a']).to.equal(1);
    console.log("Found one record.");
    callback();
  });      
}
var filterRemovedDocument = function(db, callback) {
  var collection = db.collection(test_collection);
  collection.find({'b': 1}).toArray(function(err, docs) {
    expect(err).to.equal(null);
    expect(docs.length).to.equal(0);
    console.log("Found no records.");
    callback();
  });      
}
var filterUpdatedDocument = function(db, callback) {
  var collection = db.collection(test_collection);
  collection.find({'b': 1}).toArray(function(err, docs) {
    expect(err).to.equal(null);
    expect(docs.length).to.equal(1);
    expect(docs[0]['a']).to.equal(2);
    expect(docs[0]['b']).to.equal(1);
    console.log("Found one record.");
    callback();
  });      
}
var indexCollection = function(db, callback) {
  db.collection(test_collection).createIndex(
    { "a": 1 },
      null,
      function(err, results) {
        expect(err).to.equal(null);
        console.log("Indexed test collection on 'a'.");
        callback();
    }
  );
};
var insertDocuments = function(db, callback) {
  var collection = db.collection(test_collection);
  collection.insertMany([
    {a : 1}, {a : 2}, {a : 3}
  ], function(err, result) {
    expect(err).to.equal(null);
    expect(result.result.ok).to.equal(1);
    expect(result.result.n).to.equal(3);
    expect(result.insertedCount).to.equal(3);
    expect(result.ops.length).to.equal(3);
    expect(result.ops[0]['a']).to.equal(1);
    expect(result.ops[1]['a']).to.equal(2);
    expect(result.ops[2]['a']).to.equal(3);
    console.log("Inserted three documents into test collection.");
    callback();
  });
}
var removeCollection = function(db, callback) {
  var collection = db.collection(test_collection);
  collection.remove(function(err, result) {
    expect(err).to.equal(null);
    expect(result.result.ok).to.equal(1);
    console.log("Dropped the test collection.");
    callback();
  });    
}
var removeDocument = function(db, callback) {
  var collection = db.collection(test_collection);
  collection.deleteOne({ a : 2 }, function(err, result) {
    expect(err).to.equal(null);
    expect(result.result.ok).to.equal(1);
    console.log("Removed the document with the field a equal to 2.");
    callback();
  });    
}
var updateDocument = function(db, callback) {
  var collection = db.collection(test_collection);
  collection.updateOne({ a : 2 }
    , { $set: { b : 1 } }, function(err, result) {
    expect(err).to.equal(null);
    expect(result.result.n).to.equal(1);
    console.log("Updated the document with the field a equal to 2.");
    callback();
  });  
}

describe('MongoDB basic connection and operations', function () {
  it('Connect to olympus database, manage test document', function (done) {
    MongoClient.connect(url, options, function(err, db) {
      expect(err).to.equal(null);
      removeCollection(db, function() {
        insertDocuments(db, function() {
          findDocuments(db, function() {
            filterDocuments(db, function() {
              updateDocument(db, function() {
                filterUpdatedDocument(db, function() {
                  indexCollection(db, function() {
                    removeDocument(db, function() {
                      filterRemovedDocument(db, function() {
                        removeCollection(db, function() {
                          db.close();
                          done();
                        });
                      });
                    });
                  });
                });
              });
            });
          });
        });
      });
    });
  });
});

