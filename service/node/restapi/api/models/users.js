var mongoConnection = require("mongo_connect");

exports.findByUsername = (username) => {
  mongoConnection.getInstance(function (connection) {
    var db = connection.db('user_node');
    return db.collection('auth_users').findOne({ 'Username':username }, function(err, result) {
      if (err) throw err;
      delete result._id;
      return result;
    });
  });
};
