# wumpus_agent.py
# ---------------
# Licensing Information:
# Please DO NOT DISTRIBUTE OR PUBLISH solutions to this project.
# You are free to use and extend these projects for EDUCATIONAL PURPOSES ONLY.
# The Hunt The Wumpus AI project was developed at University of Arizona
# by Clay Morrison (clayton@sista.arizona.edu), spring 2013.
# This project extends the python code provided by Peter Norvig as part of
# the Artificial Intelligence: A Modern Approach (AIMA) book example code;
# see http://aima.cs.berkeley.edu/code.html
# In particular, the following files come directly from the AIMA python
# code: ['agents.py', 'logic.py', 'search.py', 'utils.py']
# ('logic.py' has been modified by Clay Morrison in locations with the
# comment 'CTM')
# The file ['minisat.py'] implements a slim system call wrapper to the minisat
# (see http://minisat.se) SAT solver, and is directly based on the satispy
# python project, see https://github.com/netom/satispy .

import logic
import agents
import wumpus_kb
import wumpus_environment
import wumpus_planners
import minisat as msat
from time import perf_counter


# -------------------------------------------------------------------------------

def minisat(clauses, query=None, variable=None, value=True, verbose=False):
    """ Interface to minisat
    <query> is simply added as to the list of <clauses>
    
    Set <variable> to a particular <value> in order to test SAT
    assuming any instance of that variable has that value.
    
    Otherwise, with defaults, will perform normal SAT on <clauses>+<query>
    """
    if verbose:
        print(f'minisat({query}):', end='')
    if not query:
        c = clauses
    else:
        c = clauses + [query]
    m = msat.Minisat()
    s = m.solve(c, variable, value)
    if verbose:
        print(s.success)
    return s


# -------------------------------------------------------------------------------

class PropKB_SAT(logic.PropKB):

    def tell(self, sentence):
        if sentence: super(PropKB_SAT, self).tell(sentence)

    def load_sentences(self, sentences):
        for sentence in sentences:
            self.tell(sentence)

    def ask(self, query):
        """ Assumes query is a single positive proposition """
        if isinstance(query, str):
            query = logic.expr(query)
        s_true = minisat(self.clauses, None, variable=query, value=True, verbose=False)
        s_false = minisat(self.clauses, None, variable=query, value=False, verbose=False)
        if s_true.success == s_false.success:
            return None
        else:
            return s_true.success


# -------------------------------------------------------------------------------

class Proposition(agents.Thing):
    """ Used for debugging, to display proposition in WumpusEnvironment """

    def __init__(self, name, value='?'):
        self.name = f'{name}={value}'

    def display(self, canvas=None, x=None, y=None, width=None, height=None):
        return self.name

    def to_string(self):
        return self.name


# -------------------------------------------------------------------------------

class HybridWumpusAgent(wumpus_environment.Explorer):
    "An agent for the wumpus world that does logical inference. [Fig. 7.19]"""
    def __init__(self, heading='east', environment=None, verbose=True, keep_axioms=True):
        self.keep_axioms = keep_axioms  # for debugging: if True, keep easier-to-read PL form

        self.plan = None
        self.unvisited = None
        self.kb = None
        self.number_of_clauses_over_epochs = None
        self.belief_loc_query_times = None

        super(HybridWumpusAgent, self).__init__(self.agent_program, heading, environment, verbose)

    def reset(self):
        super(HybridWumpusAgent, self).reset()
        self.plan = list()
        self.unvisited = [(x,y)
                          for x in range(1, self.width + 1)
                          for y in range(1, self.height + 1)]
        self.kb = self.create_wumpus_KB()
        if self.verbose:
            self.number_of_clauses_over_epochs = list()
            # current location is queried at each epoch, so collecting
            # the times allows us to see how querying gets more expensive
            # as the KB grows.
            self.belief_loc_query_times = list()

    def create_wumpus_KB(self):
        start_time = None
        if self.verbose:
            print("HWA.create_wumpus_KB(): adding initial wumpus axioms")
        axioms = wumpus_kb.initial_wumpus_axioms(self.belief_location[0], self.belief_location[1],
                                                 self.width, self.height,
                                                 self.heading_str(self.belief_heading))
        if self.verbose:
            start_time = perf_counter()  # clock()
            print(f"    total number of axioms={len(axioms)}")
        kb = PropKB_SAT()
        for sentence in axioms:
            kb.tell(sentence)
        if self.keep_axioms:
            kb.axioms = axioms
        if self.verbose:
            end_time = perf_counter()  # clock()
            print(f"    total number of clauses={len(kb.clauses)}")
            print(f"          >>> time elapsed: {end_time - start_time}")
        return kb

    def make_percept_sentence(self, raw_percepts):
        sentence = wumpus_kb.axiom_generator_percept_sentence(self.time, raw_percepts)
        if self.verbose:
            print(f"   HWA.make_percept_sentence(): {sentence}")
        return sentence

    def add_temporal_axioms(self):
        ax_so_far = None
        if self.verbose:
            print("       HWA.add_temporal_axioms()")
        axioms = wumpus_kb.generate_square_OK_axioms(self.time, 1, self.width, 1, self.height)
        if self.verbose:
            ax_so_far = len(axioms)
            print(f"           number of location_OK axioms:         {ax_so_far}")
        axioms += wumpus_kb.generate_breeze_percept_and_location_axioms(self.time, 1, self.width, 1, self.height)
        axioms += wumpus_kb.generate_stench_percept_and_location_axioms(self.time, 1, self.width, 1, self.height)
        if self.verbose:
            new_ax_so_far = len(axioms)
            perc_to_loc = new_ax_so_far - ax_so_far
            print(f"           number of percept_to_loc axioms:      {perc_to_loc}")
            ax_so_far = new_ax_so_far
        axioms += wumpus_kb.generate_at_location_ssa(self.time, self.belief_location[0],
                                                     self.belief_location[1],
                                                     1, self.width, 1, self.height,
                                                     self.heading_str(self.belief_heading))
        if self.verbose:
            new_ax_so_far = len(axioms)
            local_loc_at = new_ax_so_far - ax_so_far
            print(f"           number of at_location ssa axioms:     {local_loc_at}")
            ax_so_far = new_ax_so_far
        axioms += wumpus_kb.generate_non_location_ssa(self.time)
        if self.verbose:
            new_ax_so_far = len(axioms)
            remaining_ssa_at_time = new_ax_so_far - ax_so_far
            print(f"           number of non-location ssa axioms:    {remaining_ssa_at_time}")
            ax_so_far = new_ax_so_far
        axioms += wumpus_kb.generate_mutually_exclusive_axioms(self.time)
        if self.verbose:
            new_ax_so_far = len(axioms)
            mutually_exclusive = new_ax_so_far - ax_so_far
            print(f"           number of mutually_exclusive axioms:  {mutually_exclusive}")
        
        if self.verbose:
            print(f"       Total number of axioms being added:  {len(axioms)}")
        
        for sentence in axioms:
            self.kb.tell(sentence)
        if self.keep_axioms:
            self.kb.axioms += axioms

    def wumpus_alive_query(self):
        if self.verbose:
            print("       Ask if Wumpus is Alive:")
        query = logic.expr(wumpus_kb.state_wumpus_alive_str(self.time))
        result = self.kb.ask(query)
        if self.verbose:
            if result is None:
                print("         Is Wumpus Alive? : Unknown!   (This should be known)")
            else:
                print(f"         Is Wumpus Alive? : {result}")

    def find_OK_locations(self):
        display_env = None
        start_time = None
        if self.verbose:
            print("     HWA.find_OK_locations()")
            
            self.wumpus_alive_query()
            
            display_env = wumpus_environment.WumpusEnvironment(self.width, self.height)
            start_time = perf_counter()  # clock()
        safe_loc = []
        for x in range(1, self.width + 1):
            for y in range(1, self.height + 1):
                query = logic.expr(wumpus_kb.state_OK_str(x, y, self.time))
                result = self.kb.ask(query)
                if result:
                    safe_loc.append((x, y))
                if self.verbose:
                    if result is None:
                        display_env.add_thing(Proposition(query, '?'), (x, y))
                    else:
                        display_env.add_thing(Proposition(query, result), (x, y))
        if self.verbose:
            end_time = perf_counter()  # clock()
            print("          >>> time elapsed while making OK location queries:"
                  f" {end_time - start_time}")
            print(display_env.to_string(self.time, title="Find OK locations queries"))
        return safe_loc

    def update_unvisited_locations(self):
        """ This cheats in the sense of not being fully based on inference,
        but is far more efficient
        (1) relies on global record of unvisited states
        (2) only checks for visiting based on the current time step
            (rather than from the beginning of time)
        Could make even more efficient by making no inference at all, by
        keeping track of current belief location and just subtracting that
        from self.unvisited.  But what's the fun in that ??! """
        display_env = None
        start_time = None
        if self.verbose:
            print("     HWA.update_unvisited_locations()")
            display_env = wumpus_environment.WumpusEnvironment(self.width, self.height)
            already_visited = [(x, y)
                               for x in range(1, self.width + 1)
                               for y in range(1, self.height + 1)
                               if (x, y) not in self.unvisited]
            for x, y in already_visited:
                display_env.add_thing(Proposition(logic.expr('~Vis'), 'T'), (x, y))
            start_time = perf_counter()  # clock()
        for (x, y) in self.unvisited:
            query = logic.expr(wumpus_kb.state_loc_str(x, y, self.time))
            vis_query_result = self.kb.ask(query)
            if vis_query_result:
                self.unvisited.remove((x, y))
        if self.verbose:
            end_time = perf_counter()  # clock()
            print("          >>> time elapsed while making unvisited locations queries:"
                  + f" {end_time - start_time}")
            for vis_loc in self.unvisited:
                # TODO: x and y here are only defined by previous for loop, something's missing...
                display_env.add_thing(Proposition(logic.expr('~Vis'), 'F'), (x, y))
        return self.unvisited

    def display_locations_utility(self, locations,
                                  # default set prop = state_loc_str *function*
                                  prop=wumpus_kb.state_loc_str,
                                  title="Safe univisited locations:"):
        display_env = wumpus_environment.WumpusEnvironment(self.width, self.height)
        for x,y in locations:
            if isinstance(prop, str):
                loc_prop = prop + f'{(x, y, self.time)}'
            else:
                # assumes prop is bound to the state_loc_str *function*
                loc_prop = logic.expr(prop(x, y, self.time))
            display_env.add_thing(Proposition(loc_prop, 'T'), (x, y))
        print(display_env.to_string(self.time, title=title))

    def find_possible_wumpus_locations(self):
        display_env = None
        start_time = None
        if self.verbose:
            print("     HWA.find_possible_wumpus_locations()")
            display_env = wumpus_environment.WumpusEnvironment(self.width, self.height)
            start_time = perf_counter()  # clock()
        possible_wumpus_loc = list()
        for x in range(1, self.width + 1):
            for y in range(1, self.height + 1):
                query = logic.expr(wumpus_kb.wumpus_str(x, y))
                result = self.kb.ask(query)
                if result is not False:
                    possible_wumpus_loc.append((x, y))
                if self.verbose:
                    if result is None:
                        display_env.add_thing(Proposition(query, '?'), (x, y))
                    else:
                        display_env.add_thing(Proposition(query, result), (x, y))
        if self.verbose:
            end_time = perf_counter()  # clock()
            print("          >>> time elapsed while making possible wumpus location queries:"
                  + f" {end_time - start_time}")
            print(display_env.to_string(self.time, title="Possible Wumpus Location queries"))
            print(f"Possible locations: {possible_wumpus_loc}")
        return possible_wumpus_loc

    def find_not_unsafe_locations(self):
        display_env = None
        start_time = None
        if self.verbose:
            print("   HWA.find_not_unsafe_locations()")
            display_env = wumpus_environment.WumpusEnvironment(self.width, self.height)
            start_time = perf_counter()  # clock()
        not_unsafe = []
        for x in range(1,self.width+1):
            for y in range(1,self.height+1):
                query = logic.expr(wumpus_kb.state_OK_str(x, y, self.time))
                result = self.kb.ask(query)
                if result is not False:
                    not_unsafe.append((x, y))
                if self.verbose:
                    if result is not False:
                        if result is None:
                            display_env.add_thing(Proposition(query, '?'), (x, y))
                        else:
                            display_env.add_thing(Proposition(query, 'T'), (x, y))
        if self.verbose:
            end_time = perf_counter()  # clock()
            print("          >>> time elapsed while making not unsafe location queries:"
                  + f" {end_time - start_time}")
            print(display_env.to_string(self.time, title="Not Unsafe Location queries"))
            # print "Not Unsafe locations: {0}".format(not_unsafe)
        return not_unsafe

    def infer_and_set_belief_location(self):
        start_time = None
        if self.verbose:
            start_time = perf_counter()  # clock()
        self.belief_location = None
        for x in range(1, self.width + 1):
            for y in range(1, self.height+1):
                query = logic.expr(wumpus_kb.state_loc_str(x, y, self.time))
                result = self.kb.ask(query)
                if result:
                    self.belief_location = wumpus_kb.loc_proposition_to_tuple(f'{query}')
        if not self.belief_location:
            if self.verbose:
                print("        --> FAILED TO INFER belief location, "
                      "assuming at initial location (entrance).")
            self.belief_location = self.initial_location
        if self.verbose:
            end_time = perf_counter()  # clock()
            print(f"        Current believed location (inferred): {self.belief_location}")
            print("          >>> time elapsed while making current location queries:"
                  + f" {end_time - start_time}")
            self.belief_loc_query_times.append(end_time-start_time)

    def infer_and_set_belief_heading(self):
        start_time = None
        self.belief_heading = None
        if self.verbose: start_time = perf_counter()  # clock()
        if self.kb.ask(logic.expr(wumpus_kb.state_heading_north_str(self.time))):
            self.belief_heading = wumpus_environment.Explorer.heading_str_to_num['north']
        elif self.kb.ask(logic.expr(wumpus_kb.state_heading_west_str(self.time))):
            self.belief_heading = wumpus_environment.Explorer.heading_str_to_num['west']
        elif self.kb.ask(logic.expr(wumpus_kb.state_heading_south_str(self.time))):
            self.belief_heading = wumpus_environment.Explorer.heading_str_to_num['south']
        elif self.kb.ask(logic.expr(wumpus_kb.state_heading_east_str(self.time))):
            self.belief_heading = wumpus_environment.Explorer.heading_str_to_num['east']

        else:
            print("        --> FAILED TO INFER belief heading, assuming initial heading.")
            self.belief_heading = self.initial_heading
            
        if self.verbose:
            end_time = perf_counter()  # clock()
            print(f"        Current inferred heading: {self.heading_str(self.belief_heading)}")
            print("          >>> time elapsed while making belief heading queries:"
                  + f"{end_time - start_time}")

    def agent_program(self, percept):
        """ Implementation of Hybrid-Wumpus-Agent of [Fig. 7.20], p.270 """
        clauses_before = None
        start_time = None
        unvisited = None

        if self.verbose:
            print(f"HWA.agent_program(): at time {self.time}")

        # update belief location and heading based on current KB knowledge state
        # if self.verbose: print "     HWA.infer_and_set_belief_location()"
        # self.infer_and_set_belief_location()
        # if self.verbose: print "     HWA.infer_and_set_belief_heading()"
        # self.infer_and_set_belief_heading()

        percept_sentence = self.make_percept_sentence(percept)
        if self.verbose:
            print("     HWA.agent_program(): kb.tell(percept_sentence):")
            print(f"         {percept_sentence}")
        self.kb.tell(percept_sentence) # update the agent's KB based on percepts
        if self.keep_axioms:
            self.kb.axioms.append(percept_sentence)

        # NOTE (CTM:20170412): updating location *has* to happen *after* percepts
        # have been added to the KB.  Otherwise, after bump or scream
        # update belief location and heading based on current KB knowledge state
        if self.verbose:
            print("     HWA.infer_and_set_belief_location()")
        self.infer_and_set_belief_location()
        if self.verbose:
            print("     HWA.infer_and_set_belief_heading()")
        self.infer_and_set_belief_heading()

        if self.verbose:
            clauses_before = len(self.kb.clauses)
            print("     HWA.agent_program(): Prepare to add temporal axioms")
            print(f"         Number of clauses in KB before: {clauses_before}")
        self.add_temporal_axioms()
        if self.verbose:
            clauses_after = len(self.kb.clauses)
            print(f"         Number of clauses in KB after: {clauses_after}")
            print(f"         Total clauses added to KB: {clauses_after - clauses_before}")
            self.number_of_clauses_over_epochs.append(len(self.kb.clauses))

        safe = None

        # If Glitter, Grab gold and leave
        if self.kb.ask(wumpus_kb.percept_glitter_str(self.time)):
            if self.verbose:
                print("   HWA.agent_program(): Grab gold and leave!")
            safe = self.find_OK_locations()
            if self.verbose: start_time = perf_counter()  # clock()
            self.plan = [wumpus_kb.action_grab_str(None)] \
                        + wumpus_planners.plan_route(self.belief_location, self.belief_heading,
                                     [self.initial_location], safe) \
                        + [wumpus_kb.action_climb_str(None)]
            if self.verbose:
                end_time = perf_counter()  # clock()
                print("          >>> time elapsed while executing plan_route():"
                      + f" {end_time - start_time}")

        # Update safe locations only if we don't have a plan
        if self.plan:
            if self.verbose:
                print("   HWA.agent_program(): Already have plan"
                      + f" (with {len(self.plan)} actions left), continue executing...")
        elif safe is None:
            if self.verbose:
                print("   HWA.agent_program(): No current plan, find one...")
            safe = self.find_OK_locations()

        # Visit unvisited safe square
        if not self.plan:
            if self.verbose:
                print("   HWA.agent_program(): Plan to visit safe square...")
            unvisited = self.update_unvisited_locations()  # find_unvisited_locations()
            safe_unvisited = list(set(unvisited).intersection(set(safe)))
            if self.verbose:
                self.display_locations_utility(safe_unvisited, prop=wumpus_kb.state_loc_str,
                                               title="Safe univisited locations:")
                start_time = perf_counter()  # clock()
            self.plan = wumpus_planners.plan_route(self.belief_location, self.belief_heading, safe_unvisited, safe)
            if self.verbose:
                end_time = perf_counter()  # clock()
                print("          >>> time elapsed while executing plan_route():"
                      + f" {end_time-start_time}")
        # Shoot wumpus to try to clear path
        if not self.plan and self.kb.ask(logic.expr(wumpus_kb.state_have_arrow_str(self.time))):
            if self.verbose:
                print("   HWA.agent_program(): Plan to shoot wumpus...")
            possible_wumpus = self.find_possible_wumpus_locations()
            if self.verbose: start_time = perf_counter()  # clock()
            self.plan = wumpus_planners.plan_shot(self.belief_location, self.belief_heading, possible_wumpus, safe)
            if self.verbose:
                end_time = perf_counter()  # clock()
                print("          >>> time elapsed while executing plan_shot():"
                      + f" {end_time-start_time}")
        # No safe choice, take risk with an unknown square
        if not self.plan:
            if self.verbose:
                print("   HWA.agent_program(): No safe choice, take risk...")
            not_unsafe = self.find_not_unsafe_locations()

            # print "univisited: ", unvisited
            
            not_unsafe_unvisited = list(set(unvisited).intersection(set(not_unsafe)))

            # print "not_unsafe_unvisited", not_unsafe_unvisited
            # print "safe", safe

            safe_and_not_unsafe_unvisited = list(set(safe).union(set(not_unsafe_unvisited)))

            # print "safe_and_not_unsafe_unvisited", safe_and_not_unsafe_unvisited
            
            if self.verbose: start_time = perf_counter()  # clock()
            self.plan = wumpus_planners.plan_route(self.belief_location,
                                                   self.belief_heading,
                                                   not_unsafe_unvisited,
                                                   safe_and_not_unsafe_unvisited)
            if self.verbose:
                end_time = perf_counter()  # clock()
                print("          >>> time elapsed while executing plan_route():"
                      + f" {end_time - start_time}")
        # No choices left, leave!
        if not self.plan:
            if self.verbose:
                print("   HWA.agent_program(): No choices left, leave!...")
                start_time = perf_counter()  # clock()
            self.plan = wumpus_planners.plan_route(self.belief_location,
                                                   self.belief_heading,
                                                   self.initial_location, safe) \
                        + [wumpus_kb.action_climb_str(None)]
            if self.verbose:
                end_time = perf_counter()  # clock()
                print("          >>> time elapsed while executing plan_route():"
                      + f" {end_time - start_time}")

        if self.verbose:
            print(f"   HWA.agent_program(): Plan:\n    {self.plan}")

        action = self.plan.pop(0)  # take next action in plan

        if self.verbose:
            print(f"   HWA.agent_program(): Action: {action}")

        # update KB with selected action
        self.kb.tell(wumpus_kb.add_time_stamp(action, self.time))
        if self.keep_axioms:
            self.kb.axioms.append(wumpus_kb.add_time_stamp(action, self.time))
        
        self.time += 1  # advance the agent's time
        return action

