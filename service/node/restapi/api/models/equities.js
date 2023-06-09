const mongoConnection = require("../../lib/mongo_connect");

async function findDatasourceByName(dataSource) {
  const connection = await mongoConnection.getInstance();
  const db = connection.db("equities");
  return db.collection("datasources").findOne({ DataSource: dataSource });
}

async function findEquityTokenDocument(dataSource) {
  const connection = await mongoConnection.getInstance();
  const db = connection.db("restapi");
  const document = await db
    .collection("token")
    .findOne({ DataSource: dataSource, Category: "equities" });
  if (document == null) {
    return null;
  }
  return document.TokenDocument;
}

async function findSymbol(symbol) {
  const connection = await mongoConnection.getInstance();
  const db = connection.db("equities");
  return db
    .collection("symbols")
    .findOne({ Symbol: symbol }, { projection: { _id: 0 } });
}

async function findSymbols(symbolList) {
  const connection = await mongoConnection.getInstance();
  const db = connection.db("equities");
  return db
    .collection("symbols")
    .find({ Symbol: { $in: symbolList } }, { projection: { _id: 0 } })
    .toArray();
}

async function updateEquityTokenDocument(dataSource, tokenDocument) {
  const connection = await mongoConnection.getInstance();
  const db = connection.db("restapi");
  return db
    .collection("token")
    .updateOne(
      { DataSource: dataSource, Category: "equities" },
      { $set: { TokenDocument: tokenDocument } },
      { upsert: true }
    );
}

module.exports = {
  findDatasourceByName,
  findEquityTokenDocument,
  findSymbol,
  findSymbols,
  updateEquityTokenDocument,
};
