import re

class ActionPreprocessing:
  """
  Class for pre-processing action inputs
  """
  def __init__(self, _keywords):
    self.keywords = _keywords


  def getAirfield(self, text):
    """
    Returns the airfield ICAO code, or None
    """
    m = re.match(r"LF[A-Z]{2}", text.upper())
    if m is not None:
      return m.group(0)
    else:
      return None


  def getKeyword(self, text):
    """
    Returns one of the possible keywords, or None
    """
    t = text.lower()
    for word in self.keywords:
      if word in text:
        return word
    return None


  def understand(self, text):
    """
    Returns airfield or keyword accordingly, or None
    """
    icao = self.getAirfield(text)
    if icao is not None:
      return icao
    else:
      return self.getKeyword(text)
