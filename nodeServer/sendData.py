from socketIO_client_nexus import SocketIO
import numpy as np
import json

listPoints = [
  (43.5497575,1.3076914,'A'),
  (43.7643653,1.0982645,'B'),
  (43.8473688,1.3619364,'C'),
  (43.7149094,1.5857085,'D'),
  (43.6044711,1.4426038,'E')]

with SocketIO('localhost',8080) as socketIO:
  socketIO.connect()
  socketIO.emit('python', json.dumps(listPoints))
  socketIO.wait(seconds=1)
