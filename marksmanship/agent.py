'''An agent with Seek, Flee, Arrive, Pursuit behaviours

Created for COS30002 AI for Games by Clinton Woodward cwoodward@swin.edu.au

'''

from vector2d import Vector2D
from vector2d import Point2D
from graphics import egi, KEY
from math import sin, cos, tan, radians, sqrt, degrees
from random import random, randrange, uniform, randint
from path import Path

AGENT_MODES = {
    KEY._1: 'rifle',
    KEY._2: 'rocket',
    KEY._3: 'handgun',
    KEY._4: 'grenade'
}

class Agent(object):

    # NOTE: Class Object (not *instance*) variables!
    DECELERATION_SPEEDS = {
        'slow': 2.0,
        'normal': 1.0,
        'fast': 0.01
    }

    def __init__(self, world=None, scale=30.0, mass=1.0, mode=None, color=None, speed=0.0):
        # keep a reference to the world object
        self.world = world
        self.mode = mode
        # where am i and where am i going
        self.angle = 0
        dir = radians(self.angle)
        self.pos = Vector2D(250,250)
        self.vel = Vector2D()
        self.heading = Vector2D(sin(dir), cos(dir))
        self.side = self.heading.perp()
        self.scale = Vector2D(scale, scale)  # easy scaling of agent size
        self.force = Vector2D()  # current steering force
        self.accel = Vector2D() # current acceleration due to force
        self.mass = mass

        # Force and speed limiting code
        self.max_speed = speed
        self.max_force = 500.0

        # data for drawing this agent
        self.color = color
        self.vehicle_shape = [
            Point2D(-1.0,  0.6),
            Point2D( 1.0,  0.0),
            Point2D(-1.0, -0.6)
        ]

        self.margin = Vector2D(self.world.cx - 10, self.world.cy - 10)

        # data for drawing target
        self.x0 = 10    #x left pt
        self.x1 = 120   #x right pt
        self.y0 = 490   #y top pt
        self.y1 = 450   #y bottom pt
        self.target_dir = 'right'
        self.target_mid = Vector2D((self.x1-self.x0) / 2, (self.y0-self.y1) / 2)
        self.target_pos = None      #provided at each new render

        # data for drawing bullet
        self.steps = None       #frequency of shots hitting target
        self.step_count = 0
        self.bullet_pos = Vector2D(250,250)
        self.avg = Vector2D()
        self.size = None

    def calculate(self, delta):
        # calculate the current steering force
        mode = self.mode
        if mode == 'aim':
            force = self.aim()
        elif mode == 'rifle':
            force = self.rifle()
        elif mode == 'rocket':
            force = self.rocket()
        elif mode == 'handgun':
            force = self.handgun()
        elif mode == 'grenade':
            force = self.grenade()
        else:
            force = Vector2D()
        self.force = force
        return force

    def update(self, delta):
        ''' update vehicle position and orientation '''
        # calculate and set self.force to be applied
        ## force = self.calculate()
        force = self.calculate(delta)   #delta needed for wander
        # limit force for wander
        force.truncate(self.max_force)
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
        ''' Draw moving target '''
        #calculate target points
        self.movingTarget()
        #draw target using those points
        egi.blue_pen()
        dbox = [
            Point2D(self.x0, self.y0),
            Point2D(self.x1, self.y0),
            Point2D(self.x1, self.y1),
            Point2D(self.x0, self.y1)
        ]
        egi.closed_shape(dbox, False)
        #pos of target
        self.target_pos = Vector2D(self.x0 + self.target_mid.x, self.y1 + self.target_mid.y)

        ''' Draw the triangle agent with color'''
        # draw the ship
        egi.set_pen_color(name=self.color)
        pts = self.world.transform_points(self.vehicle_shape, self.pos,
                                          self.heading, self.side, self.scale)
        # draw it!
        egi.closed_shape(pts)

        #draw bullets being fired
        egi.green_pen()
        if self.mode == 'rifle' or self.mode == 'rocket' or self.mode == 'handgun' or self.mode == 'grenade':
            if self.step_count == 0:
                egi.circle(self.bullet_pos, self.size)
                self.step_count += 1
            elif self.bullet_pos.y > self.target_pos.y:
                self.step_count = 0
                self.bullet_pos = Vector2D(250,250)
                self.mode = 'aim'
            else:
                self.bullet_pos += self.avg
                egi.circle(self.bullet_pos, self.size)
                self.step_count += 1

    def speed(self):
        return self.vel.length()

    #--------------------------------------------------------------------------

    def aim(self):
        return self.vel

    def movingTarget(self):
        #calculate where target is
        #move right to 490 then switch left
        if self.x1 < 490 and self.target_dir == 'right':
            self.x1 += 2
            self.x0 += 2
        elif self.x1 == 490 and self.target_dir == 'right':
            self.target_dir = 'left'
        #move left to 10 then switch right
        elif self.x0 != 10 and self.target_dir == 'left':
            self.x1 -= 2
            self.x0 -= 2
        elif self.x0 == 10:
            self.target_dir = 'right'
 
    #more steps means slower bullets
    #fast accurate
    def rifle(self):
        self.steps = 20
        self.size = 5
        self.bulletTrajectory(Vector2D(20,0))
        return Vector2D()
    #slow accurate
    def rocket(self):
        self.steps = 80
        self.size = 20
        self.bulletTrajectory(Vector2D(90,0))
        return Vector2D()
    #fast inaccurate
    def handgun(self):
        self.steps = 20
        self.size = 5
        self.bulletTrajectory(Vector2D(-50,0))
        return Vector2D()
    #slow inaccurate
    def grenade(self):
        self.steps = 120
        self.size = 20
        self.bulletTrajectory(Vector2D(0,0))
        return Vector2D()

    def bulletTrajectory(self, offset):
        #diff = self.target_pos - self.pos
        if self.target_dir == 'right':
            diff = (self.target_pos - self.pos) + offset
        elif self.target_dir == 'left':
            diff = (self.target_pos - self.pos) - offset

        x_inc = diff.x / self.steps
        y_inc = diff.y / self.steps
        self.avg = Vector2D(x_inc, y_inc)