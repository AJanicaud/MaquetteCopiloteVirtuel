import sqlite3

class Database:
  """
  Database interface
  """
  def __init__(self, _db_path):
    self.conn = sqlite3.connect(_db_path)
    self.c = self.conn.cursor()
  

  def __enter__(self):
    """
    For use of with statement
    """
    return self


  def __exit__(self, exc_type, exc_value, traceback):
    self.conn.close()
  
  
  def init(self):
    """
    Initialize database
    """
    try:
      self.c.execute("DROP TABLE IF EXISTS flightParams;")
      self.c.execute("CREATE TABLE flightParams"+
        "(airspeed_kt REAL,"+
        "'latitude_deg' REAL,"+
        "'longitude_deg' REAL,"+
        "'altitude_ft' REAL,"+
        "'vspeed_fps' REAL,"+
        "'heading_deg' REAL)")
      self.c.execute("INSERT INTO flightParams VALUES (0,43.566713,1.473501,489,0,97)") # Mirage III A02
      self.conn.commit()
    except:
      pass

  
  def setFlightParam(self, _param, _value):
    """
    Update table flightParams (single row with all params)
    """
    self.c.execute("UPDATE flightParams SET {}=?".format(_param), (_value,))
    self.conn.commit()

  
  def getFlightParam(self, _param):
    """
    Read a value from the flightParams table
    Return None if not found
    """
    try:
      self.c.execute("SELECT {} FROM flightParams".format(_param))
      return self.c.fetchone()[0]
    except:
      return None
