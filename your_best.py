# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from pyexpat import version_info
from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'MyAgent', second = 'MyAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########
global attacker
attacker = None
class MyAgent(CaptureAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """
  
  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)

    '''
    Your initialization code goes here, if you need any.
    '''
    self.depthLimit = 4
    self.startPos = gameState.getAgentPosition(self.index)
    self.maxFood = len(self.getFood(gameState).asList()) / 4
    self.life = 10
    self.mode = None
    global attacker
    if attacker == None: 
        self.mode = "attack"
        attacker = self.index
    else: self.mode = "defence"
  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)
    '''
    You should change this in your own agent.
    '''

    bestAction = actions[0]
    #stuced
    if self.stucked(gameState):
        best = 0
        for action in actions:
            succ = gameState.generateSuccessor(self.index, action)
            tmp = self.stuckEscape(succ)
            if tmp > best:
                best = tmp
                bestAction = action
        return bestAction
    foods = self.getFood(gameState).asList()
    myStat = gameState.getAgentState(self.index)
    carrying = myStat.numCarrying
    #escape
    if (myStat.isPacman and len(foods) <= 2) or carrying > self.maxFood: self.mode = "escape"
    else:
        global attacker
        if self.index == attacker: self.mode = "attack"
        else: "defence"
    if self.mode == "attack": bestAction = self.attackAction(gameState)
    elif self.mode == "defence": bestAction = self.defenceAction(gameState)
    elif self.mode == "escape": bestAction = self.escapeAction(gameState)
    return bestAction

  def escapeAction(self, gameState):
      actions = gameState.getLegalActions(self.index)
      bestAction = actions[0]
      bestScore = -9999999
      for action in actions:
          succ = gameState.generateSuccessor(self.index, action)
          score = self.escapeEvaluate(succ)
          if score > bestScore:
              bestScore = score
              bestAction = action
      return bestAction

  def escapeEvaluate(self, gameState):
      features = self.getEscapeFeatures(gameState)
      weights = self.getEscapeWeights()
      
      return features * weights
   
  def getEscapeFeatures(self, gameState):
      features = util.Counter()
      #dist
      myPos = gameState.getAgentPosition(self.index)
      features["dist"] = self.getMazeDistance(myPos, self.startPos)
      #life
      features["life"] = self.life
      
      return features

  def getEscapeWeights(self):
      return {"dist": -1, "life": 100}

  def defenceAction(self, gameState):
      actions = gameState.getLegalActions(self.index)
      bestAction = actions[0]
      bestScore = -99999999
      for action in actions:
          succ = gameState.generateSuccessor(self.index, action)
          score = self.defEvaluate(succ)
          if score > bestScore:
              bestScore = score
              bestAction = action
      return bestAction
   
  def defEvaluate(self, gameState):
      features = self.getDefFeatures(gameState)
      weights = self.getDefWeight()
      return features * weights

  def getDefFeatures(self, gameState):
      features = util.Counter()
      myState = gameState.getAgentState(self.index)
      enemies = self.getOpponents(gameState)
      invaders = []
      for enemy in enemies:
          eneState = gameState.getAgentState(enemy)
          if eneState.isPacman: invaders.append(enemy)
      #left invaders
      features["left invaders"] = len(invaders)
      #dist
      dist = 999999
      MyPos = gameState.getAgentPosition(self.index)
      if invaders:
          for invader in invaders:
              invPos = gameState.getAgentPosition(invader)
              tmp = self.getMazeDistance(MyPos, invPos)
              if tmp < dist:
                  dist = tmp
      else:
          for enemy in enemies:
              invPos = gameState.getAgentPosition(enemy)
              tmp = self.getMazeDistance(MyPos, invPos)
              if tmp < dist:
                  dist = tmp
      features["dist"] = dist
      #ghost
      if myState.isPacman: features["ghost"] = 0
      else: features["ghost"] = 1
      return features

  def getDefWeight(self):
      return {"left invaders": -100, "dist": -1, "ghost": 1000}
      
  def attackAction(self, gameState):
    actions = gameState.getLegalActions(self.index)
    myPos = gameState.getAgentPosition(self.index)
    bestAction = actions[0]
    value = -99999
    maximum = 99999
    minimum =-99999
    if myPos == self.startPos: self.life = self.life - 1
    ghosts = self.getGhosts(gameState)
    farGhost = True
    #farGhost
    for ghost in ghosts:
        ghostPos = gameState.getAgentPosition(ghost)
        dist = self.getMazeDistance(ghostPos, myPos)
        if dist < 5: 
            farGhost = False
            break
    if farGhost:
      for action in actions:
        tmp = self.evaluate(gameState)
        if tmp > value:
          value = tmp
          bestAction = action
      print("far action = ", bestAction)
      return bestAction
    #closeGhost
    for action in actions:
        succ = gameState.generateSuccessor(self.index, action)
        ghostValue = self.ghostTurn(succ, ghosts, 1, maximum, minimum)
        if ghostValue > value:
            value = ghostValue
            bestAction = action
        minimum = max(minimum, value)
    #print("best action = ", bestAction)

    return bestAction

  def pacmanTurn(self, gameState, ghosts, curDepth, maximum, minimum):
      actions = gameState.getLegalActions(self.index)
      value = -99999
      tmp = value
      for action in actions:
          succ = gameState.generateSuccessor(self.index, action)
          if succ.isOver() or curDepth == self.depthLimit:
              tmp = self.evaluate(gameState)
              value = max(value, tmp)
              return value
          tmp = self.ghostTurn(succ, ghosts, curDepth + 1, maximum, minimum)
          value = max(value, tmp)
          if value > maximum: return value
          minimum = max(minimum, value)
      return value

  def ghostTurn(self, gameState, ghosts, curDepth, maximum, minimum):
      value = 99999
      tmp = value
      next_succ = gameState
      pacPos = gameState.getAgentPosition(self.index)
      for ghost in ghosts:
          chaseDist = 99999
          chaseAction = None
          actions = gameState.getLegalActions(ghost)
          ghostPos = gameState.getAgentPosition(ghost)
          for action in actions:
              Pos = self.getPos(ghostPos, action)
              dist = self.getMazeDistance(Pos, pacPos)
              if chaseDist > dist:
                  chaseDist = dist
                  chaseAction = action
          next_succ = next_succ.generateSuccessor(ghost, chaseAction)
      tmp = self.pacmanTurn(next_succ, ghosts, curDepth, maximum, minimum)
      value = min(value, tmp)
      if value < minimum: return value
      maximum = min(maximum, value)
      return value

  def evaluate(self, gameState):
      features = self.getFeatures(gameState)
      weights = self.getWeights(gameState)
      #print("features = ", features, " total = ", features * weights)
      return features * weights
  
  def getFeatures(self, gameState):
      features = util.Counter()
      pacPos = gameState.getAgentPosition(self.index)
      #dead
      if pacPos == self.startPos:
          features["dead"] = 1
      else: features["dead"] = 0
      #capsule
      ghosts = self.getGhosts(gameState)
      scaredTime = 100
      capsules = self.getCapsules(gameState)
      close_cap_dist = 987654321
      if ghosts:
          scaredTime = gameState.getAgentState(ghosts[0]).scaredTimer
      if scaredTime == 0 and capsules:
          for cap in capsules:
              close_cap_dist = min(close_cap_dist, self.getMazeDistance(pacPos, cap))
      else: close_cap_dist = 0
      features["capsule"] = close_cap_dist
      #eat ghost
      features["eat ghost"] = len(ghosts)
      #eat capsule
      features["left capsule"] = len(capsules)
      #food
      foods = self.getFood(gameState).asList()
      foodName = None
      bestDist = 99999999
      for food in foods:
          tmp = self.getMazeDistance(pacPos, food)
          if tmp < bestDist:
              bestDist = tmp
              foodName = food
      features["food"] = bestDist
      self.debugDraw(pacPos,[0,1,0], True)
      self.debugDraw(foodName,[1,0,0])
      #left food
      features["left food"] = len(foods)

      return features
      
  def getWeights(self, gameState):
      return {"dead":0,"capsule": 0, "eat capsule": 0, "food": -1, "left food": -100, "eat ghost":0}
  
  def getPos(self, Pos, action):
      x, y = Pos
      if action == Directions.NORTH: y = y + 1
      elif action == Directions.EAST: x = x + 1
      elif action == Directions.SOUTH: y = y - 1
      elif action == Directions.WEST: x = x - 1
      return (x, y)
  
  def getGhosts(self, gameState):
      enemies = self.getOpponents(gameState)
      ghosts = []
      for ene in enemies:
        if not gameState.getAgentState(ene).isPacman:
            ghosts.append(ene)
      return ghosts

  def stucked(self, gameState):
      if len(self.observationHistory) < 3: return False
      past2 = self.observationHistory[-3]
      past1 = self.observationHistory[-2]
      past2Pos = past2.getAgentPosition(self.index)
      past1Pos = past1.getAgentPosition(self.index)
      curPos = gameState.getAgentPosition(self.index)
      if past2Pos == curPos and past1Pos == curPos: return True
      return False

  def stuckEscape(self, gameState):
      myPos= gameState.getAgentPosition(self.index)
      enemies = self.getOpponents(gameState)
      dist = 99999
      for enemy in enemies:
          enePos = gameState.getAgentPosition(enemy)
          tmp = self.getMazeDistance(myPos, enePos)
          if tmp < dist:
              dist = tmp
      return dist

  def generateSuccessor(self, gameState, action):
      succ = gameState.generateSuccessor(self.index, action)
      pos = succ.getAgentState(self.index).getPosition()
      if pos != util.nearestPoint(pos):
          print("half")
          return succ.generateSuccessor(self.index, action)

