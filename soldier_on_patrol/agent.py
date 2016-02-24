'''An agent with Seek, Flee, Arrive, Pursuit behaviours

Created for COS30002 AI for Games by Clinton Woodward cwoodward@swin.edu.au

'''

from vector2d import Vector2D
from vector2d import Point2D
from graphics import egi, KEY
from math import sin, cos, radians
from random import random, randrange, uniform
from path import Path

class Agent(object):

    # NOTE: Class Object (not *instance*) variables!
    DECELERATION_SPEEDS = {
        'slow': 2.5
    }

    def __init__(self, world=None, pos=Vector2D(), scale=30.0, mass=1.0, mode='', color=None, speed=0.0):
        # keep a reference to the world object
        self.world = world
        self.mode = mode
        ang = random()*360
        # where am i and where am i going? random start pos
        dir = radians(random()*360)
        self.pos = pos
        self.vel = Vector2D()
        self.heading = Vector2D(sin(dir), cos(dir))
        self.side = self.heading.perp()
        self.scale = Vector2D(scale, scale)  # easy scaling of agent size
        self.force = Vector2D()  # current steering force
        self.accel = Vector2D() # current acceleration due to force
        self.mass = mass
        self.health = 100
        self.ammo = 10
        self.idx = 0

        #bullet info
        self.bullet_pos = Vector2D()
        self.step_count = 0
        self.avg = Vector2D()
        self.enemy = Vector2D()

        # data for drawing this agent
        self.color = color
        self.vehicle_shape = [
            Point2D(-1.0,  0.6),
            Point2D( 1.0,  0.0),
            Point2D(-1.0, -0.6)
        ]

        # wander details
        self.wander_target = Vector2D(1, 0)
        self.wander_dist = 1.0 * scale
        self.wander_radius = 1.0 * scale
        self.wander_jitter = 10.0 * scale
        self.bRadius = scale

        # speed
        self.max_speed = speed * scale

    def calculate(self, delta):
        # calculate the current steering force
        mode = self.mode

        #agent types
        if mode == 'soldier':
            #FSM hierarchy
            #alert state
            if self.world.hostiles:
                for enemy in self.world.hostiles:
                    #seek state
                    if self.pos.distance(enemy.pos) > 100:
                        force = self.seek(enemy.pos)
                    #attack state
                    elif self.pos.distance(enemy.pos) < 100:
                        self.enemy = enemy
                        force = self.attack_mode()
            #patrol state
            else:
                force = self.patrol_mode()
        elif mode == 'zombie':
            #FSM hierarchy
            #attack state
            if self.world.soldier:
                force = self.seek(self.world.soldier.pos)

                #bite the soldier
                if self.pos.distance(self.world.soldier.pos) < 10:
                    self.world.soldier.health -= 10
                    #soldier is killed
                    if self.world.soldier.health == 0:
                        self.world.agents.remove(self.world.soldier)
                        self.world.soldier = None
            #roam state
            else:
                force = self.wander(delta)
        else:
            force = Vector2D()

        #return a force
        self.force = force
        return force

    def update(self, delta):
        ''' update vehicle position and orientation '''
        # calculate and set self.force to be applied
        force = self.calculate(delta)
        # determin the new accelteration
        self.accel = force / self.mass  # not needed if mass = 1.0
        # new velocity
        self.vel += self.accel * delta
        # check for limits of new velocity
        self.vel.truncate(self.max_speed)
        # update position
        self.pos += self.vel * delta
        # update heading is non-zero velocity (moving)
        if self.vel.length_sq() > 0.00000001:
            self.heading = self.vel.get_normalised()
            self.side = self.heading.perp()
        # treat world as continuous space - wrap new position if needed
        self.world.wrap_around(self.pos)

    def render(self, color=None):
        ''' Draw the triangle agent with color'''
        # draw the ship
        egi.set_pen_color(name=self.color)
        pts = self.world.transform_points(self.vehicle_shape, self.pos,self.heading, self.side, self.scale)
        # draw it!
        egi.closed_shape(pts)

        #draw some patrol target
        egi.red_pen()
        for target in self.world.targets:
            egi.cross(target, 10)

        ''' Draw bullets '''
        egi.grey_pen()
        if self.mode == 'fire':
            self.shoot_enemy()

        if self.mode == 'reload':
            self.color = 'YELLOW'
            self.reload_gun()
            if self.ammo == 10:
                self.mode = 'soldier'
                self.color = 'GREEN'

    def speed(self):
        return self.vel.length()

    #--------------------------------------------------------------------------

    def seek(self, target_pos):
        ''' move towards target position '''
        desired_vel = (target_pos - self.pos).normalise() * self.max_speed
        return (desired_vel - self.vel)

    def arrive(self, target_pos, speed):
        ''' this behaviour is similar to seek() but it attempts to arrive at
            the target position with a zero velocity'''
        decel_rate = self.DECELERATION_SPEEDS[speed]
        to_target = target_pos - self.pos
        dist = to_target.length()
        if dist > 0:
            # calculate the speed required to reach the target given the
            # desired deceleration rate
            speed = dist / decel_rate
            # make sure the velocity does not exceed the max
            speed = min(speed, self.max_speed)
            # from here proceed just like Seek except we don't need to
            # normalize the to_target vector because we have already gone to the
            # trouble of calculating its length for dist.
            desired_vel = to_target * (speed / dist)
            return (desired_vel - self.vel)
        return Vector2D(0, 0)

    def wander(self, delta):
        ''' random wandering using a projected jitter circle '''
        wt = self.wander_target
        # this behaviour is dependent on the update rate, so this line must
        # be included when using time independent framerate.
        jitter_tts = self.wander_jitter * delta # this time slice

        # first, add a small random vector to the target's position
        wt += Vector2D(uniform(-1,1) * jitter_tts, uniform(-1,1) * jitter_tts)
        # re-project this new vector back on to a unit circle
        wt.normalise()
        # increase the length of the vector to the same as the radius
        # of the wander circle
        wt *= self.wander_radius
        # move the target into a position WanderDist in front of the agent
        target = wt + Vector2D(self.wander_dist, 0)
        # project the target into world space
        wld_target = self.world.transform_point(target, self.pos, self.heading, self.side)
        # and steer towards it
        return self.seek(wld_target)

    def next_target(self):
        if self.pos.distance(self.world.target) < 10 and self.world.finished == True:
            #index of current target is first index
            if self.idx == 0:
                self.world.finished = False
            else:
                self.idx -= 1
                self.world.target = self.world.targets[self.idx]

        if self.pos.distance(self.world.target) < 10 and self.world.finished == False:
            #index of current target is last index
            if self.idx == len(self.world.targets)-1:
                self.world.finished = True
            else:
                self.idx += 1
                self.world.target = self.world.targets[self.idx]

    def patrol_mode(self):
        self.next_target()
        if self.pos.distance(self.world.target) < 100:
            force = self.arrive(self.world.target, 'slow')
        elif self.pos.distance(self.world.target) > 100:
            force = self.seek(self.world.target)
        return force

    def attack_mode(self):
        self.vel = Vector2D()
        #shoot
        if self.ammo >= 1 and self.mode != 'reload':    #ammo must be 10 before reload mode is reset
            self.mode = 'fire'
        #reload
        elif self.ammo != 10:
            self.mode = 'reload'

        return Vector2D()

    def bullet_path(self, hostile):
        diff = hostile.pos - self.pos
        x_inc = diff.x / 10
        y_inc = diff.y / 10
        self.avg = Vector2D(x_inc, y_inc)

    def enemy_health(self):
        self.enemy.health -= 20
        self.ammo -= 1
        self.step_count = 0
        self.bullet_pos = Vector2D()

    def reload_gun(self):
        print('ammo:',self.ammo)
        print('+1 ammo')
        self.ammo += 1

    def shoot_enemy(self):
        self.bullet_path(self.enemy)

        #soldier fires bullet
        if self.step_count == 0:
            self.bullet_pos = self.world.soldier.pos.copy()
        #update bullet pos
        elif self.step_count > 0:
            self.bullet_pos += self.avg
        egi.circle(self.bullet_pos, 5)
        self.step_count += 1

        #reduce stats for soldier and enemy target
        if self.bullet_pos == self.enemy.pos or self.bullet_pos.distance(self.enemy.pos) < 10:
            self.enemy_health()
            print('enemy health: ', self.enemy.health)
            #check if enemy is dead
            if self.enemy.health == 0:
                self.mode = 'soldier'
                self.world.hostiles.remove(self.enemy)
                self.world.agents.remove(self.enemy)
                self.enemy = Vector2D()
                self.step_count = 0