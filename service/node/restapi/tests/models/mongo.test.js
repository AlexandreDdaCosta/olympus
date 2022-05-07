// sudo su -s /bin/bash -c 'export NODE_PATH=/usr/lib/nodejs:/usr/lib/node_modules:/usr/share/javascript; cd /srv/www/node/restapi; npm test ./tests/models/mongo.test.js' node

const {MongoClient} = require('mongodb');

let test_collection = 'test.mongo'
let test_database = 'user_node'
let url = 'mongodb://127.0.0.1:27017/';

describe('insert', () => {
  let connection;
  let db;

  beforeAll(async () => {
    connection = await MongoClient.connect(url, {});
    db = await connection.db(test_database);
    var collection = db.collection(test_collection);
    await collection.remove();
  });

  afterAll(async () => {
    var collection = db.collection(test_collection);
    await collection.remove();
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
