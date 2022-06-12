
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

targeted = [None, None, None, None]
start = []
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
    self.depthLimit = 5
    self.startState = gameState
    self.startPos = gameState.getAgentPosition(self.index)
    start.append(self.startPos)
    self.maxFood = len(self.getFood(gameState).asList()) // 10
    self.mode = "attack"
    self.lastPos = None

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
        best = -9999999
        for action in actions:
            succ = gameState.generateSuccessor(self.index, action)
            myPos = succ.getAgentPosition(self.index)
            if myPos == self.lastPos: continue
            tmp = self.stuckEscape(succ)
            if tmp > best:
                best = tmp
                bestAction = action
        return bestAction
    foods = self.getFood(gameState).asList()
    myStat = gameState.getAgentState(self.index)
    myPos = gameState.getAgentPosition(self.index)
    carrying = myStat.numCarrying
    enemies = self.getOpponents(gameState)
    ghosts = self.getGhosts(gameState)
    invaders = []
    for enemy in enemies:
        if enemy not in ghosts: invaders.append(enemy)
    ghostDist = 99999999
    for ghost in ghosts:
        ghostPos = gameState.getAgentPosition(ghost)
        ghostDist = min(ghostDist, self.getMazeDistance(ghostPos, myPos))
    #escape
    totalFoods = self.getFoodYouAreDefending(self.startState).asList()
    enemyCarry = 0
    for enemy in enemies:
        enemyState = gameState.getAgentState(enemy)
        enemyCarry = max(enemyCarry, enemyState.numCarrying)
    if (carrying > self.maxFood and ghostDist < 10) or (len(foods) <=2 and myStat.isPacman) or carrying > self.maxFood * 2 or (enemyCarry > len(totalFoods) / 2 and myStat.isPacman): self.mode = "escape"
    #defence only
    elif (len(foods) <= 2 and not myStat.isPacman) or (not myStat.isPacman and invaders and myStat.scaredTimer == 0): self.mode  = "defence"
    else: self.mode = "attack"
    #select Action
    if self.mode == "defence": bestAction = self.defenceAction(gameState)
    elif self.mode == 'escape': bestAction = self.escapeAction(gameState)
    else: bestAction = self.attackAction(gameState)
   # print("index = ", self.index, "mode = ", self.mode)
    self.lastPos = myPos

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
      pacPos = gameState.getAgentPosition(self.index)
      #dist
      features["dist"] = self.getCloseHome(gameState, self.red)
      #ghost dist
      ghosts = self.getGhosts(gameState)
      dist = 9999
      ghostName = None
      for ghost in ghosts:
          ghostPos = gameState.getAgentPosition(ghost)
          tmp = self.getMazeDistance(pacPos, ghostPos)
          if tmp < dist:
              dist = tmp
              ghostName = ghost
      if ghostName != None:closeGhostState = gameState.getAgentState(ghostName)
      if ghostName != None and closeGhostState.scaredTimer == 0 and dist < 2: features["ghost dist"] = 1
      else: features["ghost dist"] = 0
      #dead
      if pacPos == self.startPos:
          features["dead"] = 1
      else: features["dead"] = 0

      return features

  def getEscapeWeights(self):
      return {"dist": -1, "dead": -9999, "ghost dist": -100}

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
     # print("features = ", features, " total = ", features * weights)
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
      team = self.getTeammateIndex(gameState)
      targets = []
      for index in team:
          if targeted[index] != None: targets.append(targeted[index])
      dist = 999999
      MyPos = gameState.getAgentPosition(self.index)
      if invaders:
          for invader in invaders:
              invPos = gameState.getAgentPosition(invader)
              if len(invaders) > 1 and invPos in targets: continue 
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
      #sandwich
      features["sandwich"] = 0
      team = self.getTeammateIndex(gameState)
      teamGhost = [index for index in team if not gameState.getAgentState(index).isPacman]
      if teamGhost:
        teamDist = 99999
        for ghost in teamGhost:
            teamPos = gameState.getAgentPosition(ghost)
            tmp = self.getMazeDistance(MyPos, teamPos)
            if tmp < teamDist:
               teamDist = tmp
        if teamDist <= 10 and dist > 5: features["sandwich"] = 1
      #ghost
      if myState.isPacman: features["ghost"] = 0
      else: features["ghost"] = 1
      return features

  def getDefWeight(self):
      return {"left invaders": -100000, "dist": -1,"sandwich": 0, "ghost": 1000}
      
  def attackAction(self, gameState):
    actions = gameState.getLegalActions(self.index)
    myPos = gameState.getAgentPosition(self.index)
    team = self.getTeammateIndex(gameState)
    teamPos = [gameState.getAgentPosition(index) for index in team]
    bestAction = actions[0]
    value = -99999
    maximum = 99999
    minimum =-99999
    ghosts = self.getGhosts(gameState)
    farGhost = True
    #farGhost
    dist = 9999999
    for ghost in ghosts:
        ghostPos = gameState.getAgentPosition(ghost)
        dist = min(dist, self.getMazeDistance(ghostPos, myPos))
        if dist < 5: 
            farGhost = False
            break
    if farGhost or not ghosts:
      for action in actions:
        succ = gameState.generateSuccessor(self.index, action)
        if self.mode == "attack": tmp = self.evaluate(succ)
        else: tmp = self.escapeEvaluate(succ)
        if tmp > value:
          value = tmp
          bestAction = action
      return bestAction
    #closeGhost
    for action in actions:
        succ = gameState.generateSuccessor(self.index, action)
        curPos = succ.getAgentPosition(self.index)
        if curPos in teamPos: 
            continue
        ghostValue = self.ghostTurn(succ, 1, maximum, minimum)
        if ghostValue > value:
            value = ghostValue
            bestAction = action
        minimum = max(minimum, value)
    #print("best action = ", bestAction)
    
    return bestAction

  def pacmanTurn(self, gameState, curDepth, maximum, minimum):
      actions = gameState.getLegalActions(self.index)
      value = -99999
      tmp = value
      for action in actions:
          succ = gameState.generateSuccessor(self.index, action)
          if succ.isOver() or curDepth >= self.depthLimit:
              if self.mode == "attack": tmp = self.evaluate(succ)
              else: tmp = self.escapeEvaluate(succ)
              value = max(value, tmp)
              return value
          tmp = self.ghostTurn(succ, curDepth + 1, maximum, minimum)
          value = max(value, tmp)
          if value > maximum: return value
          minimum = max(minimum, value)
      
      return value

  def ghostTurn(self, gameState, curDepth, maximum, minimum):
      value = 99999
      tmp = value
      next_succ = gameState
      pacPos = gameState.getAgentPosition(self.index)
      ghosts = self.getGhosts(gameState)
      if not ghosts:
          if self.mode == "attack": return self.evaluate(gameState)
          else: return self.escapeEvaluate(succ)     
      ghostName = ghosts[0]
      dist = 999999
      for ghost in ghosts:
          ghostPos = gameState.getAgentPosition(ghost)
          tmp = self.getMazeDistance(pacPos, ghostPos)
          if tmp < dist:
              dist = tmp
              ghostName = ghost
      actions = gameState.getLegalActions(ghostName)
      ghostPos = gameState.getAgentPosition(ghost)
      for action in actions:
          succ = gameState.generateSuccessor(ghostName, action)
          ghostPos = succ.getAgentPosition(ghostName)
          futurePacPos = succ.getAgentPosition(self.index)
          if futurePacPos== self.startPos: return -99999
          if succ.isOver() or curDepth >= self.depthLimit:
               if self.mode == "attack": tmp = self.evaluate(succ)
               else: tmp = self.escapeEvaluate(succ)
               value = min(value, tmp)
               return value
          tmp = self.pacmanTurn(succ, curDepth + 1, maximum, minimum)
          value = min(value, tmp)
          if value < minimum: return value
          maximum = min(maximum, value)

      return value

  def evaluate(self, gameState):
      features = self.getFeatures(gameState)
      weights = self.getWeights(gameState)
    #  print("features = ", features, " total = ", features * weights)
      return features * weights
  
  def getFeatures(self, gameState):
      features = util.Counter()
      pacPos = gameState.getAgentPosition(self.index)
      pacState = gameState.getAgentState(self.index)
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
      #left capsule
      features["left capsule"] = len(capsules)
      #pacman
      features["pacman"] = pacState.isPacman
      #food
      closeFood = self.closeFood(gameState) # closeFood = (distance, position , left food)
      if not pacState.isPacman :
          features["food"] = self.getCloseHome(gameState, not self.red)
      else:
          features["food"] = closeFood[0]
          if closeFood[1] != None: self.debugDraw(closeFood[1],[60,94,36], True)
      #left food
      if not pacState.isPacman:
          features["food"] = self.getCloseHome(gameState, not self.red)
      features["left food"] = closeFood[2]
      #ghost dist
      dist = 9999
      ghostName = None
      for ghost in ghosts:
          ghostPos = gameState.getAgentPosition(ghost)
          tmp = self.getMazeDistance(pacPos, ghostPos)
          if tmp < dist:
              dist = tmp
              ghostName = ghost
      if ghostName != None: closeGhostState = gameState.getAgentState(ghostName)
      if ghostName != None and closeGhostState.scaredTimer == 0 and dist < 2: features["ghost dist"] = 1
      else: features["ghost dist"] = 0
      #sandwich
      features["sandwich"] = 0
      team = self.getTeammateIndex(gameState)
      teamGhost = [index for index in team if not gameState.getAgentState(index).isPacman]
      if teamGhost:
        teamDist = 99999
        for ghost in teamGhost:
            teamPos = gameState.getAgentPosition(ghost)
            tmp = self.getMazeDistance(pacPos, teamPos)
            if tmp < teamDist:
               teamDist = tmp
        
        if teamDist <= 3: features["sandwich"] = 1

      return features
      
  def getWeights(self, gameState):
      return {"dead": -99999,"capsule": -3, "left capsule": -200, "pacman": 1000, "food": -1, "left food": -100, "ghost dist": -1000, "sandwitch": -300}
  
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
      if len(self.observationHistory) < 5: return False
      past3 = self.observationHistory[-4]
      past2 = self.observationHistory[-3]
      past1 = self.observationHistory[-2]

      past2Pos = past2.getAgentPosition(self.index)
      past1Pos = past1.getAgentPosition(self.index)
      curPos = gameState.getAgentPosition(self.index)
      if past2Pos == curPos and past1Pos == curPos: return True
      return False

  def stuckEscape(self, gameState):
      myPos= gameState.getAgentPosition(self.index)
      
      return -self.getMazeDistance(myPos, self.startPos)

  def closeFood(self, gameState):
      pacPos = gameState.getAgentPosition(self.index)
      team = self.getTeammateIndex(gameState)
      targets = [targeted[index] for index in team]
      foods = self.getFood(gameState).asList()
      foodName = None
      bestDist = 99999999
      for food in foods:
          if food in targets: continue
          tmp = self.getMazeDistance(pacPos, food)
          if tmp < bestDist:
              bestDist = tmp
              foodName = food

      targeted[self.index] = foodName
      return (bestDist, foodName, len(foods))

  def getTeammateIndex(self, gameState):
      team = self.getTeam(gameState)
      team.remove(self.index)
      
      return team

  def getCloseHome(self, gameState, red):
      height = gameState.data.layout.height
      walls = gameState.getWalls()
      halfway = gameState.data.layout.width // 2
      myPos = gameState.getAgentPosition(self.index)
      bestPos = None
      if red: x = halfway - 1
      else: x = halfway
      dist = 999999
      global distanceMap
      for y in range(1, height):
          pos = (x, y)
          if not walls[x][y]:
              tmp = self.getMazeDistance(myPos, pos)
              if tmp < dist:
                dist = tmp
                bestPos = pos
      self.debugDraw(bestPos, [1,1,1], True)
      return dist


