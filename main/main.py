# Main function of the "maquette"

# Print debug messages
debug = True
debug_sockets = False
debug_threads = False

import threading
import time
from collections import deque
import speech_recognition as sr
import pyttsx3
import json

actionQueue = deque()

# Stop semaphores
stop = dict()
for ps in ['FGFS','API','SR','node','position']:
  stop[ps] = threading.Semaphore(value=0)

from Database import Database
db_name = 'maquette.db'

from FGFS_Interface import FGFS_Interface, updateFlightParams
from API import initAPI, updateAPI
from ActionPreprocessing import ActionPreprocessing
from StateMachine import StateMachine, State

from Trajectory import computeTrajectory

from socketIO_client_nexus import SocketIO


class FGFS_Listener(threading.Thread):
  """
  FGFS interface thread
  """

  def __init__(self, _frequency = 1):
    super().__init__()
    self.frequency = _frequency # default: 1 Hz
    
    self.fgfs = FGFS_Interface()
    self.fgfs.connect("", 5555)


  def run(self):
    with Database(db_name) as db:
      while not stop['FGFS'].acquire(False):
         updateFlightParams(db, self.fgfs)
         if debug_threads: print("[THD] updateFlightParams")
         time.sleep(1/self.frequency)
    return


class API_update(threading.Thread):
  """
  Regular API update thread
  """

  def __init__(self, _frequency = 0.2):
    super().__init__()
    self.frequency = _frequency # default: 0.2 Hz


  def run(self):
    with Database(db_name) as db:
      while not stop['API'].acquire(False):
        updateAPI(db)
        if debug_threads: print("[THD] updateAPI")
        time.sleep(1/self.frequency)
    return


class SR_Listener(threading.Thread):
  """
  Speech recognition event listener
  """
  
  def __init__(self, _frequency = 5):
    super().__init__()
    self.frequency = _frequency # default: 5 Hz
    self.r = sr.Recognizer()
    self.m = sr.Microphone()
    self.stop_listening = None
  

  def run(self):
    # initial calibration
    with self.m as source:
      self.r.adjust_for_ambient_noise(source)
    self.stop_listening = self.r.listen_in_background(self.m, self.callback)
    while not stop['SR'].acquire(False):
      if debug_threads: print("[THD] Sleep in sr")
      time.sleep(1/self.frequency)
    self.stop_listening()
    return
  
  
  # callback when speech heard
  def callback(self, recognizer, audio):
    try:
      textHeard = recognizer.recognize_google(audio, language='fr-FR')
      if debug: print("[DBG] \tHeard: {}".format(textHeard))
      keyword = actionPreprocessing.understand(textHeard)
      if keyword is not None:
        actionQueue.append(keyword)
    except sr.UnknownValueError:
      if debug: print("[DBG] \tSpeech not recognized")
    except sr.RequestError as e:
      if debug: print("[DBG] \tSpeech recognition request error;{}".format(e))


class NodeListener(threading.Thread):
  """
  Node interface
  """
  
  def __init__(self, _frequency = 10):
    super().__init__()
    self.frequency = _frequency # default: 10 Hz (approx)


  def run(self):
    try:
      with SocketIO('localhost', 8080, wait_for_connection=False) as socket:
        socket.connect()
        if debug_sockets: print("[SCK] Connected to Node server on 8080")
        socket.on('action', self.callback)
        while not stop['node'].acquire(False):
          if debug_threads: print("[THD] Socket wait in node")
          socket.wait(1/self.frequency)
    except Exception:
      print("[ERR] *** NodeListener failed")
    return


  # callback when keyword received from Node server
  def callback(self, *args):
    if debug_sockets: print("[SCK] From Node: {}".format(args[0]))
    keyword = actionPreprocessing.understand(args[0])
    if keyword is not None:
      actionQueue.append(keyword)


class PositionUpdate(threading.Thread):
  """
  Regular aircraft position update for Node.js server
  """

  def __init__(self, _frequency = 0.5):
    super().__init__()
    self.frequency = _frequency # default: 0.5 Hz


  def run(self):
    with Database(db_name) as db:
      while not stop['position'].acquire(False):
        sendToNode('position', (
          db.getFlightParam("latitude_deg"),
          db.getFlightParam("longitude_deg"),
          db.getFlightParam("airspeed_kt"),
          db.getFlightParam("altitude_ft"),
          db.getFlightParam("heading_deg")))
        if debug_threads: print("[THD] positionUpdate")
        time.sleep(1/self.frequency)
    return


def dict2list(dico):
  ret = []
  for x in dico.values():
    print(x)
    ret.append(x.tolist())
  return ret


def sendToNode(channel, data):
  """
  Send string to Node.js server
  No reply expected

  WARNING: while trying to connect, the main loop is blocked
  """
  if debug_sockets: print("[SCK] To Node (on {}): {}".format(channel, data))
  with SocketIO('localhost', 8081, wait_for_connection=False) as socket:
    socket.connect()
    if debug_sockets: print("[SCK] Connected to Node server on 8081")
    if(type(data) == dict):
      socket.emit(channel, json.dumps(dict2list(data), ensure_ascii=False))
    else:
      socket.emit(channel, json.dumps(data, ensure_ascii=False))
  if debug_sockets: print("[SCK] To Node: sent")


class ThirstyTalker():
  """
  Text to speech

  WARNING: blocking call when talking
  """
  
  def __init__(self):
    self.engine = pyttsx3.init()


  def talk(self, text):
    self.engine.say(text)
    self.engine.runAndWait()


def stopThreads(*threads):
  """
  Stop all threads and exit cleanly
  """
  for s in stop.values():
    s.release()
  print("\nStopping")
  for t in threads:
    print("[THD]", t)
    t.join()
  print("Stopped\n")


### MAIN main

actionPreprocessing = ActionPreprocessing(["déroutement", "retour"])


# States and state machine
s = dict()
for kw in actionPreprocessing.keywords:
  s[kw] = State(kw)

s['retour'].addNext(s['déroutement'])
airfields = ['LFCL','LFBO','LFBR']
for airfield in airfields:
  s[airfield] = State(airfield)
  s['déroutement'].addNext(s[airfield])
  s[airfield].addNext(s['retour'])

stateMachine = StateMachine(s['retour'])


# TTS
talker = ThirstyTalker()


# Threads
fgfsListener = FGFS_Listener()
fgfsListener.start()
if debug: print("[DBG] fgfsListener started")
time.sleep(1)
with Database(db_name) as db:
  db.init()
  initAPI(db)
if debug: print("[DBG] initAPI executed")
APIupdate = API_update()
APIupdate.start()
if debug: print("[DBG] APIupdate started")
srListener = SR_Listener()
srListener.start()
if debug: print("[DBG] srListener started")
nodeListener = NodeListener()
nodeListener.start()
if debug: print("[DBG] nodeListener started")
positionUpdate = PositionUpdate()
positionUpdate.start()
if debug: print("[DBG] positionUpdate started")


# Main loop
if debug: print("[DBG] \tCurrent state: {}".format(stateMachine.getState()))
try:
  with Database(db_name) as db:
    while True:
      if debug_threads: print("[THD] main loop")
      if actionQueue:
        if stateMachine.proceed(actionQueue.popleft()):
          state = stateMachine.getState()
          if debug: print("[DBG] \tCurrent state: {}".format(state))
          if str(state) == "déroutement":
            sendToNode('action', 'déroutement')
            talker.talk("Diversion initiated")
          elif str(state) in airfields:
            points = computeTrajectory(db, str(state))
            sendToNode('points', points)
            talker.talk("Diverting to " + str(state))
          elif str(state) == "retour":
            sendToNode('action', 'retour')
            talker.talk("Resuming normal flight mode")
      time.sleep(0.1)
except KeyboardInterrupt:
  # ^C
  stopThreads(fgfsListener, APIupdate, srListener, nodeListener, positionUpdate)
