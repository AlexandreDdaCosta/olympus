const login = (req, res, next) => {
  console.log('/auth/login auth.js');
  res.json({ message: 'Login' });   
};
const logout = (req, res, next) => {
  console.log('/auth/logout auth.js');
  res.json({ message: 'Logout' });   
};
const refresh = (req, res, next) => {
  console.log('/auth/refresh refresh.js');
  res.json({ message: 'Refresh' });   
};
module.exports = {login, logout, refresh};
