import socket

class FGFS_Interface:
  """
  Interface with FlightGear

  Connects to FGFS socket, and can read properties.

  To launch FGFS: --telnet=socket,out,60,localhost,5555,udp
  """

  def __init__(self):
    self.fgfs_sock = None
    self.fgfs_file = None


  def connect(self, host, port):
    if host == "":
      host = socket.gethostname()

    self.fgfs_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.fgfs_sock.connect((host, port))
    self.fgfs_file = self.fgfs_sock.makefile()
    self.fgfs_sock.sendall(b"data\r\n")


  #def setprop(self, prop, value):
  #  self.fgfs_sock.sendall(bytes("get {0}\r\n".format(prop),"utf8"))


  def getprop(self, prop):
    self.fgfs_sock.sendall(bytes("get {0}\r\n".format(prop),"utf8"))
    return self.fgfs_file.readline().strip()


def updateFlightParams(db, fgfs):
  """
  Function that updates the flight parameters from FGFS in the database
  """
  p = dict() # parameters
  p["airspeed_kt"] = "/velocities/airspeed-kt"
  p["latitude_deg"] = "/position/latitude-deg"
  p["longitude_deg"] = "/position/longitude-deg"
  p["altitude_ft"] = "/position/altitude-ft"
  p["vspeed_fps"] = "/velocities/vertical-speed-fps"
  p["heading_deg"] = "/orientation/heading-deg"
  
  for param,path in p.items():
    db.setFlightParam(param, fgfs.getprop(path))
