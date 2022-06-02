//ALEX
exports.login = (req, res, next) => {
  console.log('/auth/login auth.js');
  res.json({ message: 'Login.' });   
};
exports.logout = (req, res, next) => {
  console.log('/auth/logout auth.js');
  res.json({ message: 'Logout.' });   
};
exports.refresh = (req, res, next) => {
  console.log('/auth/refresh refresh.js');
  res.json({ message: 'Refresh.' });   
};
