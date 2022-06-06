var mongoConnection = require("mongo_connect");

function findByUsername(username) {
  return new Promise( (resolve, reject) => {
    mongoConnection.getInstance( (connection) => {
      let db = connection.db('user_node');
      db.collection('auth_users').findOne({ 'Username': username }).then( (entry) => {
        resolve(entry);
      });
    });
  });
};

module.exports = { findByUsername }
