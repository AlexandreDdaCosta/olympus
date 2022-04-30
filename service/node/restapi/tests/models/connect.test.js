// sudo su -s /bin/bash -c 'export NODE_PATH=/usr/lib/nodejs:/usr/lib/node_modules:/usr/share/javascript; cd /srv/www/node/restapi; npm test ./tests/models/connect.test.js' node

const async = require('async');
const fs = require('fs'); 
const MongoClient = require('mongodb').MongoClient;
const test_collection = 'test'
const url = 'mongodb://127.0.0.1:27017/' + test_collection;

describe('MongoDB connection', () => {
  test('Connect to test database.', () => {
    MongoClient.connect(url, (error, database) => {
      if (error) throw new Error(error);
      async.waterfall([



      ]);
      database.close();
    });
  });
});


/*

function removeCollection(db,collectionName,callback) {

  async.waterfall([

    // Get collection
    function(cb) {
      db.collection(collectionName,function(err,collection) {
        if (err) throw err;
        cb(null,collection);
      });
    },

    // Count collection current
    function(collection,cb) {
      collection.count(function(err,count) {
        console.log(
          "%s collection has %s documents",
          collectionName,
          count
        );
        cb(null,collection);
      });
    },

    // Remove collection documents
    function(collection,cb) {
      collection.remove({},function(err,removed) {
        console.log(
          "%s collection removed %s documents",
          collectionName,
          removed
        );
        cb(null,collection);
      });
    },

  ],function(err,collection) {

    collection.count(function(err,count) {
      console.log(
        "%s collection now has %s documents",
        collectionName,
        count
      );
      callback(err);
    });

  });
}

// Main flow after connection
MongoClient.connect('mongodb://localhost/test',function(err,db) {

  if (err) throw err;

  async.waterfall([

    // Set up a collection
    function(cb) {
      var collectionName = "sample";

      db.collection(collectionName,function(err,collection) {
        cb(null,collection,collectionName);
      });
    },

    // Insert some things
    function(collection,collectionName,cb) {
      async.eachSeries([1,2,3,4,5,6,7,8],function(item,complete) {
        collection.insert({ "item": item },function(err) {
          if (err) throw err;
          complete();
        });
      },function(err) {
        // When all are complete
        cb(null,collectionName);
      });
    },

    // Call your remove method
    function(collectionName,cb) {

      removeCollection(db,collectionName,function(err) {
        if (err) throw err;

        cb();
      });

    }

  ]);

});





Initialize test commands

const insertDocuments = (db, callback) => {
  var collection = db.collection(test_collection);
  collection.insertMany([
    {a : 1}, {a : 2}, {a : 3}
  ], function(err, result) {
    expect(err).toBe(null);
    expect(result.result.ok).toBe(1);
    expect(result.result.n).toBe(3);
    expect(result.insertedCount).toBe(3);
    expect(result.ops.length).toBe(3);
    expect(result.ops[0]['a']).toBe(1);
    expect(result.ops[1]['a']).toBe(2);
    expect(result.ops[2]['a']).toBe(3);
    console.log("Inserted three documents into test collection.");
  });
}

const removeCollection = (client, callback) => {
  var collection = client.collection(test_collection);
  collection.remove( function(err, result) {
    expect(err).toBe(null);
    expect(result.result.ok).toBe(1);
    console.log("Dropped the test collection.");
    callback();
  });    
}

Run test commands

describe('MongoDB basic connection and test database and collection operations', () => {
  test('Connect to test database.', () => {
    MongoClient.connect(url, (err, client) => {
      if (err) throw new Error(err);
//      removeCollection(client, function() {});
//        insertDocuments(client, function() {
      client.close();
    });
  });
});
*/

/*
ALEX

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

*/
