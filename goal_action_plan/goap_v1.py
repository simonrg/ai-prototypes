from math import pow
from operator import itemgetter

class Gob():
    
    def __init__(self):
        self.running = ''
        self.enemy_health = 20
        self.plan_discontent = {}
        self.actions_discontent = {}
        self.best_action = None
        self.current_state = None
        self.discontentment = 0
        self.goals = {
                'Attack': 4,
                'Heal':   2,
                'Reload': 6,
                'Energy': 1
            }

        self.actions = {
                'Take Cover': {
                        'Attack using Pistol':  {'Attack': -2, 'Reload': +1},
                        'Use First Aid':        {'Heal': -5,   'Attack': +5},
                        'Reload Pistol':        {'Reload': -4, 'Attack': +4, 'Heal': +1}
                    },
                'Leave Cover': {
                    'Attack using Knife':   {'Attack': -4, 'Energy': +3, 'Heal': +1},
                    'Use Pills':            {'Heal': -2,   'Energy': -2, 'Attack': +1},
                    'Evade Enemy':          {'Energy': -3, 'Reload': +3}
                }
            }


    def filter_actions(self):
        #plan with the smallest discontentment
        new_state = min(self.plan_discontent, key=self.plan_discontent.get)
        
        #when a state (e.g. Take Cover/Leave Cover) changes or before a state has been chosen
        if self.current_state == None or new_state != self.current_state:
            self.current_state = new_state

            #best action and output
            self.best_action = min(self.plan_discontent.items(), key=itemgetter(1))
            self.print_both_states()
        else:
            #remove higher discontentment plan
            larger = max(self.plan_discontent, key=self.plan_discontent.get)
            self.plan_discontent.pop(larger)

            #merge selected plan and its actions
            for action in self.actions_discontent:
                if action in self.actions[new_state]:
                    self.plan_discontent[action] = self.actions_discontent[action]

            #best action and output
            self.best_action = min(self.plan_discontent.items(), key=itemgetter(1))
            self.print_one_state()


    def print_both_states(self):
        #organise plans with their sub-actions
        for k,v in self.plan_discontent.items():
            if k == self.current_state:
                active = { k: v }
            else:
                inactive = { k: v }
        
        for action in self.actions_discontent.items():
            if action[0] in self.actions[self.current_state]:
                active[action[0]] = action[1]
            else:
                inactive[action[0]] = action[1]
        
        #order the dictionary values for output
        active = sorted(active.items(), key=lambda t:t[1])
        inactive = sorted(inactive.items(), key=lambda t:t[1])

        print('+->', inactive[-1])
        for action in inactive[:-1]:
            print(' +->', action)

        print('+->', active[-1])
        for action in active[:-1]:
            print(' +->', action)

        #print best action
        print('BEST ACTION')
        print(self.best_action)
        print('\n ---')


    def print_one_state(self):
        output = sorted(self.plan_discontent.items(), key=lambda t:t[1])

        #print actions
        print('+->', output[-1])
        for action in output[:-1]:
            print(' +->', action)
            
        #print best action
        print('BEST ACTION')
        print(self.best_action)
        print('\n ---')


    def update_goals(self):
        #update the discontentment value
        self.discontentment = self.best_action[1]

        if self.best_action[0] == self.current_state:
            return

        #apply best actions affects to respective goals
        action = self.actions[self.current_state][self.best_action[0]]
        for goal in action:
            self.goals[goal] += action[goal]
            #zero is lowest insistence level of any goal
            if self.goals[goal] < 0:
                self.goals[goal] = 0

        #reduce enemy health if attacked -- damage is only negative numbers, reduce 'Attack' insistence
        if 'Attack' in action and action['Attack'] < 0:
            damage = action['Attack']
            self.enemy_health += damage


    def calc_discontent(self, goal, action):
        #calculate discontentment
        goal_value = self.goals[goal]
        goal_change = action
        newValue = goal_value + goal_change

        return pow(newValue, 2)


    def choose_action_goap(self):
        discontent = 0
        total_discontent = 0

        #calculate total discontentment of each plan
        for plan in self.actions:
            for action in self.actions[plan]:

                #calculate the discontentment of each action
                for goal in self.actions[plan][action]:
                    affect = self.actions[plan][action].get(goal)
                    discontent += self.calc_discontent(goal, affect)
                    #store action discontentment
                    self.actions_discontent[action] = int(discontent)

                total_discontent += discontent
                discontent = 0

            #plan discontentment -- discontentment of every action
            self.plan_discontent[plan] = int(total_discontent)
            total_discontent = 0


if __name__ == '__main__':
    gob = Gob()
    gob.running = True
    #initalise discontentment
    for goal in gob.goals:
        power = pow(gob.goals[goal], 2)
        gob.discontentment += power

    while gob.running:
        #stats
        print('\nENEMY HEALTH:', gob.enemy_health)
        print('GOALS:', gob.goals, '(DISCONTENTMENT=%i)' % int(gob.discontentment))

        #main sequence
        gob.choose_action_goap()
        gob.filter_actions()
        gob.update_goals()

        #clean variables
        gob.plan_discontent = {}
        gob.actions_discontent = {}

        #check if the simulation should end
        if gob.enemy_health <= 0:
            gob.running = False

    print('\n---------------------------')
    print('ENEMY HEALTH: 0')
    print('DISCONTENTMENT:', gob.discontentment)
    print('Final results:', gob.goals)
    print('---------------------------')