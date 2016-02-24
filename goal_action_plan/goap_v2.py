from math import pow
from operator import itemgetter

class Gob():
    
    def __init__(self):
        self.running = ''
        self.action_plan = {}
        self.actions_discontent = {}
        self.goals_copy = {}
        self.goals = {
                'Attack': 4,
                'Health': 2,
                'Ammo': 3
            }

        self.actions = {
                'Shoot':    {'Attack': -2, 'Ammo': +3},
                'Heal':     {'Health': -5, 'Attack': +3},
                'Reload':   {'Ammo': -2, 'Health': +5}
            }


    def calc_discontent(self, goal, action, goalset):
        #calculate discontentment
        goal_value = goalset[goal]
        goal_change = action
        newValue = goal_value + goal_change

        return pow(newValue, 2)


    def set_action_discontentment(self, goalset, action_discontent):
        discontent = 0

        #discontentment of each action
        for action in self.actions:
            #each goal affected
            for goal in self.actions[action]:
                affect = self.actions[action].get(goal)
                discontent += self.calc_discontent(goal, affect, goalset)
            #set discontentment
            action_discontent[action] = int(discontent)
            discontent = 0


    def create_goap(self):
        stack = []
        planned_discontent = {}

        #iterate through each plan (e.g. starting with shoot, reload or heal)
        for head in self.actions_discontent.items():            
            print('Calculate path starting from', head)

            #initialise a dummy to store predicted discontentment for each path
            self.set_action_discontentment(self.goals, planned_discontent)
            stack.append(head)

            #calculate discontentment of subsequent action
            #action hierarchy levels deep
            next_action = head
            while len(stack) < 5:
                #update goals with current affects to calculate new discontentment
                #print('LEVEL:', len(stack))
                #print('-> prev goals:', self.goals_copy)
                for action in self.actions.items():
                    if next_action[0] == action[0]:
                        self.update_goals(action[1])
                #print('-> new goals:', self.goals_copy)

                #new lowest discontentment action with updated goals
                self.set_action_discontentment(self.goals_copy, planned_discontent)
                next_action = min(planned_discontent.items(), key=itemgetter(1))
                #print('-> new discontentment:', planned_discontent)
                #print('-> next action:', next_action)

                #next action is lowest discontentment (next level)
                stack.append(next_action)

            #calculate path total value and output result
            path_cost = 0
            for action in stack:
                print(action)
                path_cost += action[1]
            print('TOTAL COST:', path_cost)
            print('------------------')

            #save the path and its total cost
            self.action_plan[stack[0]] = path_cost

            #clear stack for next hierarchy
            #reset predicted goals for next hierarchy
            stack = []
            planned_discontent = {}
            self.goals_copy = self.goals.copy()


    def update_goals(self, affects):
        for goal in self.goals_copy:
            if goal in affects:
                self.goals_copy[goal] += affects[goal]

                if self.goals_copy[goal] < 0:
                    self.goals_copy[goal] = 0


if __name__ == '__main__':
    gob = Gob()
    gob.running = True
    gob.goals_copy = gob.goals.copy()

    while gob.running:
        #stats
        print('GOALS:', gob.goals)
        gob.set_action_discontentment(gob.goals, gob.actions_discontent)
        print('ACTION DISCONTENTMENT FOR CURRENT GOALS:', gob.actions_discontent)

        #main sequence
        gob.create_goap()
        
        #quit
        gob.running = False

    #summarise results
    print('\n---------------------------')
    print('Best path start pos:', min(gob.action_plan, key=gob.action_plan.get))
    print('Total path cost:', min(gob.action_plan.values()))
    print('---------------------------')