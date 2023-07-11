Client-Server application with Qt. 
- Client:
  sends presence-message.
  If it is ok, client sends message to other client.
  
- Server:
  checks a client whether it is registered or not.
  If the client is registered the server sends confirmation.
  receives messages from clients and resend them to addressees

Stack:
Python3, SQlAlchemy, Qt5
