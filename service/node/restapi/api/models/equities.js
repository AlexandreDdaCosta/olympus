var mongoConnection = require("mongo_connect");

async function findDatasourceByName(dataSource) {
  const connection = await mongoConnection.getInstance();
  let db = connection.db('equities');
  return await db.collection('datasources').findOne({ 'DataSource': dataSource });
}

async function findEquityTokenDocument(dataSource) {
  const connection = await mongoConnection.getInstance();
  let db = connection.db('restapi');
  let document = await db.collection('token').findOne({ 'DataSource': dataSource, 'Category': 'equities' });
  if (document == null) {
    return null;
  }
  return document['TokenDocument'];
}

async function findSymbol(symbol) {
  const connection = await mongoConnection.getInstance();
  let db = connection.db('equities');
  return await db.collection('symbols').findOne({ 'Symbol': symbol }, { projection: { _id: 0 }});
}

async function updateEquityTokenDocument(dataSource, tokenDocument) {
  const connection = await mongoConnection.getInstance();
  let db = connection.db('restapi');
  return await db.collection('token').updateOne( { DataSource: dataSource, Category: 'equities' }, { $set: { TokenDocument: tokenDocument } }, { upsert: true });
}

module.exports = { findDatasourceByName, findEquityTokenDocument, findSymbol, updateEquityTokenDocument }
