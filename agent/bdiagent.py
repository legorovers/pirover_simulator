import time
from inspect import signature


class Agent:
    def __init__(self):
        self.beliefbase = {}
        self.rules = {}
        self.num_rules = 0
        self.running = 0
        # list of goal names
        self.goalbase = []
        # dictionary linking goal names to functions that determine if they are satisfied
        self.goal_functions = {}
        self.pending_goals = {}

    # REASONING CYCLE
    def run_agent(self):
        # From original pi2go implementation - potentiall need to account for intitialisation functions.
        # robohat.init()
        self.running = 1
        # dummy_rule is a catch all if no other rule applies
        self.add_rule(self.dummy_rule)
        while self.running:
            self.reason("no platform", "no rule info")

    def reason(self, platform, rule_info):
        # Note this was originally part of the agent but we now anticipate different applications will
        # want to use different belief update functions.  Need to find an elegant way to integrate this.
        self.getpercepts(self.beliefbase)
        self.manage_goals(self.beliefbase, self.goalbase)
        selected_rule = self.selectRule(self.beliefbase, self.goalbase)
        self.execute(selected_rule, platform, rule_info)

    def getpercepts(self, beliefbase):
        time.sleep(0.1)
        return

    def manage_goals(self, beliefbase, goalbase):
        for goal in self.goalbase:
            if self.is_achieved(goal):
                print(goal, " Goal Achieved!")
                self.achieved_goal(goal, goalbase)
        return

    # A goal is achieved if either it shares a name with a belief and the belief is true or its associated function returns true
    def is_achieved(self, goal):
        if goal in self.beliefbase.keys():
            if self.beliefbase[goal] == 1:
                return 1
            return 0
        else:
            goalfunc = self.goal_functions[goal]
            if goalfunc():
                return 1
            return 0

    # When a goal is achieved it is removed from the goalbase, if it is a subgoal of some other goal then the next subgoal should now be attempted
    def achieved_goal(self, goal, goalbase):
        goalbase.remove(goal)
        if goal in self.pending_goals.keys():
            next_goallist = self.pending_goals[goal]
            next_goal = next_goallist.pop(0)
            self.add_goal(next_goal)
            self.pending_goals.pop(goal, None)
            if len(next_goallist) > 0:
                self.pending_goals[next_goal] = next_goallist
        return

    def selectRule(self, beliefbase, goalbase):
        for key in self.rules.keys():
            tuple = self.rules[key]
            guard = tuple[0]
            evaluated_guard = guard()
            if evaluated_guard == 1:
                selected_rule = tuple[1]
                return selected_rule
            elif type(evaluated_guard) == list:
                rule = tuple[1]
                if len(evaluated_guard) > 0:
                    selected_rule = lambda: rule(evaluated_guard[0])
                    return selected_rule

    def execute(self, rule, robot, rule_info):
        sig = signature(rule)
        params = sig.parameters
        if len(params) == 0:
            rule()
        else:
            rule(robot, rule_info)

    # REASONING ABOUT BELIEFS
    # believe and B are the same.
    def believe(self, key):
        return lambda: self.believe_support(key, self.beliefbase)

    def B(self, key):
        return lambda: self.believe_support(key, self.beliefbase)

    def believe_support(self, key, beliefbase):
        print("checking "), key
        if key in beliefbase:
            return beliefbase[key]
        return 0

    def belief_value(self, belief):
        return belief()

    def AND(self, belief1, belief2):
        return lambda: self.and_support(belief1, belief2)

    def and_support(self, belief1, belief2):
        b1 = belief1()
        if b1 == 1:
            return belief2()
        elif type(b1) == list:
            b2 = belief2()
            if b2 == 1:
                return b1
            elif b2 == 0:
                return 0
            else:
                return self.intersect(b1, b2)
        else:
            return 0

    def NOT(self, belief):
        return lambda: self.not_support(belief)

    def not_support(self, belief):
        if belief() == 0:
            return 1
        else:
            return 0

    def OR(self, belief1, belief2):
        return lambda: self.or_support(belief1, belief2)

    def or_support(self, belief1, belief2):
        if belief1() == 1:
            return 1
        elif belief1() == 0:
            return belief2()
        else:
            if belief2() == 1:
                return belief1()
            elif belief2() == 0:
                return belief1()
            else:
                return belief1().extend(belief2())

    # SET MANIPULATION FUNCTIONS for belielfs

    def intersect(self, s1, s2):
        out = []
        i = 0
        for m1 in s1:
            if m1 in s2:
                out[i] = m1
                i = i + 1
        return out

    # REASONING ABOUT GOALS - NB Think AND, OR, NOT etc will also work for goals but haven't checked this.
    # has_goal and G are the same
    def has_goal(self, key):
        return lambda: self.goal_support(key, self.goalbase)

    def G(self, key):
        return lambda: self.goal_support(key, self.goalbase)

    def goal_support(self, key, goalbase):
        if key in goalbase:
            return 1
        return 0

    # RULES
    def add_rule(self, rule):
        self.rules[self.num_rules] = (self.alwaystrue, rule)
        self.num_rules = self.num_rules + 1

    def add_condition_rule(self, condition, rule):
        self.rules[self.num_rules] = (condition, rule)
        self.num_rules = self.num_rules + 1

    def add_pick_best_rule(self, set, cmp_function, rule):
        bestof = lambda: self.best_of(set, cmp_function)
        self.rules[self.num_rules] = (bestof, rule)
        self.num_rules = self.num_rules + 1

    def best_of(self, listb, comp_function):
        best = listb()[0]
        for x in listb():
            if comp_function(x, best):
                best = x
        return [best]

    # Functions for inclusion in rules
    def sensor_value(self, key):
        if key in self.beliefbase:
            return self.beliefbase[key]
        else:
            print("ERROR: No value from sensors for ", key)
            return 0

    def done(self):
        self.running = 0

    #  BELIEF MANAGEMENT
    def add_belief(self, key):
        self.beliefbase[key] = 1

    def drop_belief(self, key):
        self.beliefbase[key] = 0

    def change_belief(self, key, value):
        self.beliefbase[key] = value

    #  GOAL MANAGEMENT
    def add_goal(self, key):
        self.goalbase.append(key)

    def add_subgoals(self, goal, goallist):
        first_goal = goallist.pop(0)
        self.add_goal(first_goal)
        self.pending_goals[first_goal] = goallist

    def drop_goal(self, key):
        self.goalbase.remove(key)

    def goal_is_achieved_when(self, key, function):
        self.goal_functions[key] = function

    # Default Rule
    def alwaystrue(self):
        return 1

    def dummy_rule(self, plan, robot):
        time.sleep(0.5)
        return
