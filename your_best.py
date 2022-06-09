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
global team_attack
team_attack = False
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
    self.startState = gameState
    self.life = 10
    self.mode = None
    global team_attack
    if not team_attack: 
        self.mode = "attack"
        team_attack = True
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
    if self.stucked(gameState):
        best = 0
        for action in actions:
            succ = gameState.generateSuccessor(self.index, action)
            tmp = self.stuckEscape(succ)
            if tmp > best:
                best = tmp
                bestAction = action
        return bestAction
    if self.mode == "attack": bestAction = self.attackAction(gameState)
    elif self.mode == "defence": bestAction = self.defenceAction(gameState)
    return bestAction
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
      print("defAction = ", bestAction)
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
      print(features)
      return features

  def getDefWeight(self):
      return {"left invaders": -100, "dist": -1, "ghost": 100}
      
  def attackAction(self, gameState):
    actions = gameState.getLegalActions(self.index)
    myPos = gameState.getAgentPosition(self.index)
    if myPos == self.startPos: self.life = self.life - 1
    ghosts = self.getGhosts(gameState)
    bestAction = actions[0]
    value = -99999
    maximum = 99999
    minimum =-99999
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
      #life
      features["life"] = self.life
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
      #eat capsule
      features["left capsule"] = len(capsules)
      #food
      foods = self.getFood(gameState).asList()
      close_food_dist = 987654321
      for food in foods:
          close_food_dist = min(close_food_dist, self.getMazeDistance(pacPos, food))
      features["food"] = close_food_dist
      #eat
      Carrying = gameState.getAgentState(self.index).numCarrying
      features["left food"] = len(foods)
      #home
      if Carrying > 0 and scaredTime == 0:
          teammate = self.index
          team = self.getTeam(gameState)
          for i in team:
              if i != self.index: teammate = i
          teamPos = gameState.getAgentPosition(teammate)
          features["home"] = -self.getMazeDistance(pacPos, teamPos)
      else: features["home"] = 0
      return features
      
  def getWeights(self, gameState):
      return {"life":0,"capsule": -2, "eat capsule": -200, "food": -1, "left food": -100, "home": 0}
  
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
      past = self.observationHistory[-3]
      pastPos = past.getAgentPosition(self.index)
      curPos = gameState.getAgentPosition(self.index)
      if pastPos == curPos: return True
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
