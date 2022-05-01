// sudo su -s /bin/bash -c 'export NODE_PATH=/usr/lib/nodejs:/usr/lib/node_modules:/usr/share/javascript; cd /srv/www/node/restapi; npm test ./tests/models/connect.test.js' node

const {MongoClient} = require('mongodb');

let test_collection = 'connect.test'
let test_database = 'test_node'
let url = 'mongodb://127.0.0.1:27017/';

describe('insert', () => {
  let connection;
  let db;

  beforeAll(async () => {
    connection = await MongoClient.connect(url, {});
    db = await connection.db(test_database);
    await db.dropDatabase();
  });

  afterAll(async () => {
    await db.dropDatabase();
    await connection.close();
  });

  it('Dopey test', async () => {
    expect('1').toEqual('1');
  });
  
  it('Insert/delete a single document into/from collection', async () => {
    var collection = db.collection(test_collection);
    var mockItem = {a : 1};
    await collection.insertOne(mockItem);
    var insertedItem = await collection.findOne({a : 1});
    expect(insertedItem).toEqual(mockItem);
    await collection.deleteOne(mockItem);
    var deletedItem = await collection.findOne({a : 1});
    expect(deletedItem).toEqual(null);
  });

  it('Insert/delete multiple documents into/from collection', async () => {
    var collection = db.collection(test_collection);
    var mockItems = [{a : 1}, {b : 2}];
    await collection.insertMany(mockItems);
    var item = {a : 1};
    var searchedItem = await collection.findOne({a : 1});
    expect(searchedItem['a']).toEqual(1);
    searchedItem = await collection.findOne({b : 1});
    expect(searchedItem).toEqual(null);
    var searchedItems = await collection.find({b : 2}).toArray();
    expect(searchedItems.length).toEqual(1);
    searchedItems = await collection.find({b : 1}).toArray();
    expect(searchedItems.length).toEqual(0);
    var searchedItems = await collection.find({}).toArray();
    expect(searchedItems.length).toEqual(2);
    expect(searchedItems[0]['a']).toEqual(1);
    expect(searchedItems[1]['b']).toEqual(2);
  });

});

/*


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

*/
