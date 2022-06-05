const newIndex = (req, res, next) => {
  console.log('/ index.js');
  res.json({ message: 'Olympus back-end API listening for requests via express/node.js.' });   
};
module.exports = { newIndex };
