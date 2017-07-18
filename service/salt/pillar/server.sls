interface:
  services:
    - frontend

supervisor:
  services:
    - backend
    - frontend

unified:
  services:
    - backend
    - bigdata
    - frontend
