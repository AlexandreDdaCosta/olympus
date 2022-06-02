// sudo su -s /bin/bash -c 'source /srv/www/node/restapi/tests/test_source.sh; cd /srv/www/node/restapi; npm test ./tests/models/mongo.test.js' node

const {MongoClient} = require('mongodb');
const config = require('config');
const fs = require('fs');
const os = require('os');

const test_collection = 'test.models.mongo';

describe('Connect to mongo database and execute a variety of document operations.', () => {
  let connection;
  let db;
  let password;

  if (os.userInfo().username != config.get('mongodb.user')) {
    throw new Error('Test must be run under run user '+config.get('mongodb.user'));
    process.exit(1);
  }
  try {
    password = fs.readFileSync(config.get('mongodb.password_file'), 'utf8');
  } catch (err) {
    throw new Error(err);
    process.exit(1);
  }

  beforeAll(async () => {
    const uri = 'mongodb://'+config.get('mongodb.user')+':'+password+'@'+config.get('mongodb.host')+':'+config.get('mongodb.port')+'/'+config.get('mongodb.database_auth');
    connection = await MongoClient.connect(uri, {});
    db = await connection.db(config.get('mongodb.database_default'));
    var collection = db.collection(test_collection);
    await collection.drop(function (err, result) { if (err); });
  });

  afterAll(async () => {
    var collection = db.collection(test_collection);
    await collection.drop();
    await connection.close();
  });

  it('Insert/delete/update a single document into/from collection', async () => {
    var collection = db.collection(test_collection);
    var mockItem = {a : 1};
    await collection.insertOne(mockItem);
    var insertedItem = await collection.findOne({a : 1});
    expect(insertedItem).toEqual(mockItem);
    await collection.updateOne({a : 1}, {$set: {a : 2}});
    searchedItem = await collection.findOne({a : 2});
    expect(searchedItem['a']).toEqual(2);
    await collection.deleteOne({a : 2});
    var deletedItem = await collection.findOne({a : 2});
    expect(deletedItem).toEqual(null);
  });

  it('Insert/delete/update(one) multiple documents into/from collection', async () => {
    var collection = db.collection(test_collection);
    var mockItems = [{a : 1}, {b : 2}, {c : 3}];
    await collection.insertMany(mockItems);
    var searchedItem = await collection.findOne({a : 1});
    expect(searchedItem['a']).toEqual(1);
    searchedItem = await collection.findOne({b : 1});
    expect(searchedItem).toEqual(null);
    var searchedItems = await collection.find({b : 2}).toArray();
    expect(searchedItems.length).toEqual(1);
    searchedItems = await collection.find({b : 1}).toArray();
    expect(searchedItems.length).toEqual(0);
    searchedItems = await collection.find({}).toArray();
    expect(searchedItems.length).toEqual(3);
    expect(searchedItems[0]['a']).toEqual(1);
    expect(searchedItems[1]['b']).toEqual(2);
    await collection.deleteOne({b : 2});
    searchedItem = await collection.findOne({b : 2});
    expect(searchedItem).toEqual(null);
    searchedItems = await collection.find({}).toArray();
    expect(searchedItems.length).toEqual(2);
    await collection.updateOne({c : 3}, {$set: {b : 2}});
    searchedItem = await collection.findOne({b : 2});
    expect(searchedItem['b']).toEqual(2);
    searchedItems = await collection.find({}).toArray();
    expect(searchedItems.length).toEqual(2);
    expect(searchedItems[0]['a']).toEqual(1);
    expect(searchedItems[1]['b']).toEqual(2);
    await collection.deleteMany({});
    searchedItems = await collection.find({}).toArray();
    expect(searchedItems).toEqual([]);
    expect(searchedItems.length).toEqual(0);
  });

  it('Insert/index/select(some fields)/sort for multiple documents into/from collection', async () => {
    var collection = db.collection(test_collection);
    var mockItems = [{name : 'foo', surname : 'barf'}, {name : 'pooh', surname : 'bar'}, { name : 'chew', surname : 'bar'}];
    await collection.insertMany(mockItems);
    await collection.createIndex({name : 1, surname: 1});
    var searchedItems = await collection.find({}).toArray();
    expect(searchedItems.length).toEqual(3);
    expect(searchedItems[0]['name']).toEqual('foo');
    expect(searchedItems[0]['surname']).toEqual('barf');
    expect(searchedItems[1]['name']).toEqual('pooh');
    expect(searchedItems[1]['surname']).toEqual('bar');
    var searchedItem = await collection.findOne({name : 'pooh'});
    expect(searchedItem['surname']).toEqual('bar');
    searchedItems = await collection.find({name : 'foo'}, { projection: { surname: 1 } }).toArray();
    expect(searchedItems.length).toEqual(1);
    expect(searchedItems[0]['surname']).toEqual('barf');
    expect(searchedItems[0]['name']).toEqual(undefined);
    searchedItems = await collection.find({name : 'foo'}, { projection: { surname: 0 } }).toArray();
    expect(searchedItems.length).toEqual(1);
    expect(searchedItems[0]['name']).toEqual('foo');
    expect(searchedItems[0]['surname']).toEqual(undefined);
    searchedItems = await collection.find({name : 'foobarf'}).toArray();
    expect(searchedItems).toEqual([]);
    expect(searchedItems.length).toEqual(0);
    searchedItems = await collection.find({}).sort({ surname : 1, name : 1 }).toArray();
    expect(searchedItems.length).toEqual(3);
    expect(searchedItems[0]['name']).toEqual('chew');
    expect(searchedItems[1]['name']).toEqual('pooh');
  });

});
