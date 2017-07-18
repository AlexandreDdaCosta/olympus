interface:
  services:
    - frontend

supervisor:
  services:
    - backend

unified:
  services:
    - backend
    - bigdata
    - frontend
