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
               first = 'DummyAgent', second = 'DummyAgent'):
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

class DummyAgent(CaptureAgent):
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
    self.depthLimit = 3
    self.startPos = gameState.getAgentPosition(self.index)

  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)

    '''
    You should change this in your own agent.
    '''
    enemies = self.getOpponents(gameState)
    ghosts = []
    for ene in enemies:
        if not gameState.getAgentState(ene).isPacman:
            ghosts.append(ene)
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
    return bestAction
  
  def pacmanTurn(self, gameState, ghosts, curDepth, maximum, minimum):
      actions = gameState.getLegalActions(self.index)
      value = -99999
      tmp = value
      for action in actions:
          succ = gameState.generateSuccessor(self.index, action)
          if succ.isOver() or curDepth == self.depthLimit:
              tmp = self.evaluate(gameState)
          tmp = self.ghostTurn(succ, ghosts, curDepth + 1, maximum, minimum)
          value = max(value, tmp)
          if value > maximum: return value
          minimum = max(minimum, value)
      return value

  def ghostTurn(self, gameState, ghosts, curDepth, maximum, minimum):
      
      value = 99999
      tmp = value
      next_succ = gameState
      for ghost in ghosts:
          chaseDist = 99999
          chaseAction = None
          actions = gameState.getLegalActions(ghost)
          for action in actions:
              if action == Directions.NORT
              dist = self.getMazeDistance(ghost, self.index)
              if chaseDist > dist:
                  chaseDist = dist
                  chaseAction = action
          next_succ = next_succ.generateSuccessor(ghost, chaseAction)
      tmp = self.pacmanTurn(next_succ,ghosts,curDepth, maximum, minimum)
      value = min(value, tmp)
      if value < minimum: return value
      maximum = min(maximum, value)
      return value

  def evaluate(self, gameState):
      features = self.getFeatures(gameState)
      weights = self.getWeights(gameState)
      print("features = ", features, " total = ", features * weights)
      return features * weights
  
  def getFeatures(self, gameState):
      features = util.Counter()
      pacPos = gameState.getAgentPosition(self.index)
      #dead
      if pacPos == self.startPos:
          features["dead"] = 1
      else: features["dead"] = 0
      #close food
      foods = self.getFood(gameState).asList()
      close_food_dist = 987654321
      for food in foods:
          close_food_dist = min(close_food_dist, self.getMazeDistance(pacPos, food))
      features["close food"] = -close_food_dist
      #eat
      Carrying = gameState.getAgentState(self.index).numCarrying
      features["eat"] = Carrying
      return features
      
  def getWeights(self, gameState):
      return {"dead":-9999999, "close food": 1, "eat": 100}
      

