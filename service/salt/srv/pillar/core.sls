core-user: salt
core-email: alex_investor@yahoo.com

core-packages:
  - vim-enhanced

core-states:
  - users
  - repository
      
core-users:
  salt:
    fullname: salt configuration management
    home: /home/salt
