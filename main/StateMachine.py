class StateMachine():
  """
  State machine for the Python part of the "maquette"
  An action from state A to state B is B
  """
  
  def __init__(self, _initialState):
    self.state = _initialState


  def proceed(self, _next):
    """
    Returns True if next state is valid, False otherwise
    and updates the current state
    """
    nextState = self.state.isReachable(_next)
    if nextState is not None:
      self.state = nextState
      return True
    else:
      return False
  

  def getState(self):
    return self.state


class State():
  """
  State class, with next achievable state associated with an "action"
  """
  
  def __init__(self, _name):
    self.name = _name
    self.nextStates = []


  def addNext(self, _nextState):
    self.nextStates.append(_nextState)
  
  
  def isReachable(self, _next):
    """
    Returns next state if reachable, None otherwise
    """
    for s in self.nextStates:
      if s.name == _next:
        return s
    return None
  
  def __str__(self):
    return self.name
