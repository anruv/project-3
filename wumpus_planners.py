import wumpus_environment
import wumpus_kb
import search


# -----------------------------------------------------------------------------
# Distance fn
# -----------------------------------------------------------------------------

def manhattan_distance_with_heading(current, target):
    """
    Return the Manhattan distance + any turn moves needed
        to put target ahead of current heading
    current: (x,y,h) tuple, so: [0]=x, [1]=y, [2]=h=heading)
    heading: 0:^:north 1:<:west 2:v:south 3:>:east
    """
    md = abs(current[0] - target[0]) + abs(current[1] - target[1])
    if current[2] == 0:   # heading north
        # Since the agent is facing north, "side" here means
        # whether the target is in a row above or below (or
        # the same) as the agent.
        # (Same idea is used if agent is heading south)
        side = (current[1] - target[1])
        if side > 0:
            md += 2           # target is behind: need to turns to turn around
        elif side <= 0 and current[0] != target[0]:
            md += 1           # target is ahead but not directly: just need to turn once
        # note: if target straight ahead (curr.x == tar.x), no turning required
    elif current[2] == 1:  # heading west
        # Now the agent is heading west, so "side" means
        # whether the target is in a column to the left or right
        # (or the same) as the agent.
        # (Same idea is used if agent is heading east)
        side = (current[0] - target[0])
        if side < 0:
            md += 2           # target is behind
        elif side >= 0 and current[1] != target[1]:
            md += 1           # target is ahead but not directly
    elif current[2] == 2:  # heading south
        side = (current[1] - target[1])
        if side < 0:
            md += 2           # target is behind
        elif side >= 0 and current[0] != target[0]:
            md += 1           # target is ahead but not directly
    elif current[2] == 3:  # heading east
        side = (current[0] - target[0])
        if side > 0:
            md += 2           # target is behind
        elif side <= 0 and current[1] != target[1]:
            md += 1           # target is ahead but not directly
    return md


# -----------------------------------------------------------------------------
# Plan Route
# -----------------------------------------------------------------------------

def plan_route(current, heading, goals, allowed):
    """
    Given:
       current location: tuple (x,y)
       heading: integer representing direction
       goals: list of one or more tuple goal-states
       allowed: list of locations that can be moved to
    ... return a list of actions (no time stamps!) that when executed
    will take the agent from the current location to one of (the closest)
    goal locations
    You will need to:
    (1) Construct a PlanRouteProblem that extends search.Problem
    (2) Pass the PlanRouteProblem as the argument to astar_search
        (search.astar_search(Problem)) to find the action sequence.
        Astar returns a node.  You can call node.solution() to extract
        the list of actions.
    NOTE: represent a state as a triple: (x, y, heading)
          where heading will be an integer, as follows:
          0='north', 1='west', 2='south', 3='east'
    """

    # Ensure heading is a in integer form
    if isinstance(heading, str):
        heading = wumpus_environment.Explorer.heading_str_to_num[heading]

    if goals and allowed:
        prp = PlanRouteProblem((current[0], current[1], heading), goals, allowed)
        # NOTE: PlanRouteProblem will include a method h() that computes
        #       the heuristic, so no need to provide here to astar_search()
        node = search.astar_search(prp, display=False)
        if node:
            return node.solution()
    
    # no route can be found, return empty list
    print('>>> NO ROUTE FOUND')
    return list()


# -----------------------------------------------------------------------------

class PlanRouteProblem(search.Problem):
    def __init__(self, initial, goals, allowed):
        """ Problem defining planning of route to closest goal
        Goal is generally a location (x,y) tuple, but state will be (x,y,heading) tuple
        initial = initial location, (x,y) tuple
        goals   = list of goal (x,y) tuples
        allowed = list of state (x,y) tuples that agent could move to """
        super().__init__(initial=initial)
        # self.initial = initial  # initial state
        self.goals = goals      # list of goals that can be achieved
        self.allowed = allowed  # the states we can move into

    def h(self, node):
        """
        Heuristic that will be used by search.astar_search()
        """
        ### YOUR CODE HERE ###
        return 0  # NOTE: This is wrong!

    def actions(self, state):
        """
        Return list of allowed actions that can be made in state
        """
        ### YOUR CODE HERE ###
        return []  # NOTE: This is wrong!

    def result(self, state, action):
        """
        Return the new state after applying action to state
        """
        ### YOUR CODE HERE ###
        pass

    def goal_test(self, state):
        """
        Return True if state is a goal state
        """
        ### YOUR CODE HERE ###
        pass


# -----------------------------------------------------------------------------
# Plan Shot
# -----------------------------------------------------------------------------

def plan_shot(current, heading, goals, allowed):
    """ Plan route to nearest location with heading directed toward one of the
    possible wumpus locations (in goals), then append shoot action.
    NOTE: This assumes you can shoot through walls!!  That's ok for now. """
    if goals and allowed:
        psp = PlanShotProblem((current[0], current[1], heading), goals, allowed)
        node = search.astar_search(psp)
        if node:
            plan = node.solution()
            plan.append(wumpus_kb.action_shoot_str(None))
            # HACK:
            # since the wumpus_alive axiom asserts that a wumpus is no longer alive
            # when on the previous round we perceived a scream, we
            # need to enforce waiting so that time elapses and knowledge of
            # "dead wumpus" can then be inferred...
            # Another approach: with correct successor-state-axiom for WumpusAlive,
            # if there is a scream, then if you look one state into the future you
            # can tell that the Wumpus is dead.
            plan.append(wumpus_kb.action_wait_str(None))
            return plan

    # no route can be found, return empty list
    return list()


# -----------------------------------------------------------------------------

class PlanShotProblem(search.Problem):
    def __init__(self, initial, goals, allowed):
        """ Problem defining planning to move to location to be ready to
              shoot at nearest wumpus location
        NOTE: Just like PlanRouteProblem, except goal is to plan path to
              nearest location with heading in direction of a possible
              wumpus location;
              Shoot and Wait actions is appended to this search solution
        Goal is generally a location (x,y) tuple, but state will be (x,y,heading) tuple
        initial = initial location, (x,y) tuple
        goals   = list of goal (x,y) tuples
        allowed = list of state (x,y) tuples that agent could move to """
        super().__init__(initial=initial)
        # self.initial = initial  # initial state
        self.goals = goals      # list of goals that can be achieved
        self.allowed = allowed  # the states we can move into

    def h(self, node):
        """
        Heuristic that will be used by search.astar_search()
        """
        ### YOUR CODE HERE ###
        return 0  # NOTE: This is wrong!

    def actions(self, state):
        """
        Return list of allowed actions that can be made in state
        """
        ### YOUR CODE HERE ###
        return []  # NOTE: This is wrong!

    def result(self, state, action):
        """
        Return the new state after applying action to state
        """
        ### YOUR CODE HERE ###
        pass

    def goal_test(self, state):
        """
        Return True if state is a goal state
        """
        ### YOUR CODE HERE ###
        pass


# -----------------------------------------------------------------------------
