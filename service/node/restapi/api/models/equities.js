var mongoConnection = require("mongo_connect");

async function findDatasourceByName(datasource) {
  const connection = await mongoConnection.getInstance();
  let db = connection.db('equities');
  return await db.collection('datasources').findOne({ 'DataSource': datasource });
}

module.exports = { findDatasourceByName }
