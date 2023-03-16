import wumpus_planners


# -----------------------------------------------------------------------------
# Layout display helper
# -----------------------------------------------------------------------------

LAYOUT = """
                  west
         (0,0),(0,1),(0,2),(0,3),
 south   (1,0),(1,1),(1,2),(1,3),   north
         (2,0),            (2,3),
         (3,0),(3,1),(3,2),(3,3)]
                  east
    Facing directions: 0='north', 1='west', 2='south', 3='east'
    initial: (<x-loc>, <y-loc>, facing)
"""


# -----------------------------------------------------------------------------
# Plan Route Tests
# -----------------------------------------------------------------------------

def test_prp(initial):
    """
    The 'expected initial states and solution pairs' below are provided
    as a sanity check, showing what the PlanRouteProblem soluton is
    expected to produce.  Provide the 'initial state' tuple as the
    argument to test_PRP, and the associate solution list of actions is
    expected as the result.
    The test assumes the goals are [(2,3),(3,2)], that the heuristic fn
    defined in PlanRouteProblem uses the manhattan_distance_with_heading()
    fn above, and the allowed locations are:
        [(0,0),(0,1),(0,2),(0,3),
        (1,0),(1,1),(1,2),(1,3),
        (2,0),            (2,3),
        (3,0),(3,1),(3,2),(3,3)]

    Expected intial state and solution pairs:
    (0,0,0) : ['Forward', 'Forward', 'Forward', 'TurnRight', 'Forward', 'Forward']
    (0,0,1) : ['TurnRight', 'Forward', 'Forward', 'Forward', 'TurnRight', 'Forward', 'Forward']
    (0,0,2) : ['TurnLeft', 'Forward', 'Forward', 'Forward', 'TurnLeft', 'Forward', 'Forward']
    (0,0,3) : ['Forward', 'Forward', 'Forward', 'TurnLeft', 'Forward', 'Forward']
    """
    return wumpus_planners.plan_route((initial[0], initial[1]), initial[2],
                                      # Goals:
                                      ((2, 3), (3, 2)),
                                      # Allowed locations:
                                      ((0, 0), (0, 1), (0, 2), (0, 3),
                                       (1, 0), (1, 1), (1, 2), (1, 3),
                                       (2, 0),                 (2, 3),
                                       (3, 0), (3, 1), (3, 2), (3, 3)))


PRP_TEST_SET = (((0, 0, 0), ['Forward', 'Forward', 'Forward', 'TurnRight', 'Forward', 'Forward']),
                ((0, 0, 1), ['TurnRight', 'Forward', 'Forward', 'Forward', 'TurnRight', 'Forward', 'Forward']),
                ((0, 0, 2), ['TurnLeft', 'Forward', 'Forward', 'Forward', 'TurnLeft', 'Forward', 'Forward']),
                ((0, 0, 3), ['Forward', 'Forward', 'Forward', 'TurnLeft', 'Forward', 'Forward']))


def run_prp_tests():
    print('\n--------------------------\nRunning Plan Route Problem Tests:')
    print(LAYOUT)
    for initial, expected in PRP_TEST_SET:
        print(f'initial:  {initial}')
        print(f'expected: {expected}')
        print(f'plan:     {test_prp(initial)}')


# -----------------------------------------------------------------------------
# Plan Shot Tests
# -----------------------------------------------------------------------------


def test_psp(initial, goals):
    """
    The 'expected initial states and solution pairs' below are provided
    as a sanity check, showing what the PlanShotProblem solution is
    expected to produce.  Provide the 'initial state' tuple as the
    argument to test_PRP, and the associated solution list of actions is
    expected as the result.
    The test assumes the goals are [(2,3),(3,2)], that the heuristic fn
    defined in PlanShotProblem uses the manhattan_distance_with_heading()
    fn above, and the allowed locations are:
        [(0,0),(0,1),(0,2),(0,3),
        (1,0),(1,1),(1,2),(1,3),
        (2,0),            (2,3),
        (3,0),(3,1),(3,2),(3,3)]

    Expected intial state and solution pairs:
    (0,0,0) : ['Forward', 'Forward', 'TurnRight', 'Shoot', 'Wait']
    (0,0,1) : ['TurnRight', 'Forward', 'Forward', 'TurnRight', 'Shoot', 'Wait']
    (0,0,2) : ['TurnLeft', 'Forward', 'Forward', 'Forward', 'TurnLeft', 'Shoot', 'Wait']
    (0,0,3) : ['Forward', 'Forward', 'Forward', 'TurnLeft', 'Shoot', 'Wait']
    """
    return wumpus_planners.plan_shot((initial[0], initial[1]), initial[2],
                                     # Goals:
                                     goals,
                                     # Allowed locations:
                                     [(0, 0), (0, 1), (0, 2), (0, 3),
                                      (1, 0), (1, 1), (1, 2), (1, 3),
                                      (2, 0),                 (2, 3),
                                      (3, 0), (3, 1), (3, 2), (3, 3)])


GOALS = ((2, 3), (3, 2))

PSP_TEST_SET = (((0, 0, 0), ['Forward', 'Forward', 'TurnRight', 'Shoot', 'Wait']),
                ((0, 0, 1), ['TurnRight', 'Forward', 'Forward', 'TurnRight', 'Shoot', 'Wait']),
                ((0, 0, 2), ['TurnLeft', 'Forward', 'Forward', 'TurnLeft', 'Shoot', 'Wait']),
                ((0, 0, 3), ['Forward', 'Forward', 'TurnLeft', 'Shoot', 'Wait']))


def run_psp_tests():
    print('\n--------------------------\nRunning Plan Shot Problem Tests:')
    print(LAYOUT)
    print(f'    GOALS: {GOALS}\n')
    for initial, expected in PSP_TEST_SET:
        print(f'initial:  {initial}')
        print(f'expected: {expected}')
        print(f'plan:     {test_psp(initial, GOALS)}')


if __name__ == '__main__':
    run_prp_tests()
    run_psp_tests()
