'''An agent with Seek, Flee, Arrive, Pursuit behaviours

Created for COS30002 AI for Games by Clinton Woodward cwoodward@swin.edu.au

'''

from vector2d import Vector2D
from vector2d import Point2D
from graphics import egi, KEY
from math import sin, cos, radians, sqrt
from random import random, randrange, uniform
from path import Path

AGENT_MODES = {
}

class Agent(object):

    # NOTE: Class Object (not *instance*) variables!
    DECELERATION_SPEEDS = {
        'slow': 2.0,
        'normal': 1.0,
        'fast': 0.01
    }

    def __init__(self, world=None, scale=30.0, mass=1.0, mode=None, color=None):
        # keep a reference to the world object
        self.world = world
        self.mode = mode
        # where am i and where am i going? random start pos
        dir = radians(random()*360)
        self.pos = Vector2D(randrange(world.cx), randrange(world.cy))
        self.vel = Vector2D()
        self.heading = Vector2D(sin(dir), cos(dir))
        self.side = self.heading.perp()
        self.scale = Vector2D(scale, scale)  # easy scaling of agent size
        self.force = Vector2D()  # current steering force
        self.accel = Vector2D() # current acceleration due to force
        self.mass = mass

        # Force and speed limiting code
        self.max_speed = 2.0 * scale
        self.max_force = 5.0 * scale

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

        # group based weight values
        self.wander_wt = 1.0
        self.align_wt = 1.0
        self.cohesion_wt = 1.0
        self.separate_wt = 1.0

        self.neighbours = []
        self.neighbour_radius = 150

        # debug draw info?
        self.show_info = False

        # data for drawing walls
        self.walls = [
            Vector2D(10.0,490.0), 
            Vector2D(490.0,490.0), 
            Vector2D(490.0,10.0), 
            Vector2D(10.0,10.0)
        ]

    def calculate(self, delta):
        # calculate the current steering force
        mode = self.mode
        if mode == 'flocking':
            force = self.wander_wt * self.wander(delta)
            self.find_neighbours()
            force += self.align_wt * self.align(self.neighbours)
            force += self.separate_wt * self.separate(self.neighbours)
            force += self.cohesion_wt * self.cohesion(self.neighbours)
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
        ''' Draw the triangle agent with color'''
        # draw the ship
        egi.set_pen_color(name=self.color)
        pts = self.world.transform_points(self.vehicle_shape, self.pos,
                                          self.heading, self.side, self.scale)
        # draw it!
        egi.closed_shape(pts)

        # draw the border
        egi.blue_pen()
        egi.closed_shape(self.walls, False)
        egi.red_pen()
        egi.line_with_arrow(self.pos, self.pos + self.vel * 0.5, 5)    #feeler1

        # add some handy debug drawing info lines - force and velocity
        if self.show_info:
            s = 0.5 # <-- scaling factor
            # force
            egi.red_pen()
            egi.line_with_arrow(self.pos, self.pos + self.force * s, 5)
            # velocity
            egi.grey_pen()
            egi.line_with_arrow(self.pos, self.pos + self.vel * s, 5)
            # net (desired) change
            egi.white_pen()
            egi.line_with_arrow(self.pos+self.vel * s, self.pos+ (self.force+self.vel) * s, 5)
            egi.line_with_arrow(self.pos, self.pos+ (self.force+self.vel) * s, 5)

    def speed(self):
        return self.vel.length()

    #--------------------------------------------------------------------------

    def seek(self, target_pos):
        ''' move towards target position '''
        desired_vel = (target_pos - self.pos).normalise() * self.max_speed
        return (desired_vel - self.vel)

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

    def align(self, group):
        sum_heading = Vector2D()
        avg = Vector2D()
        count = 0

        for agent in group:
            if agent.pos != self.pos:
                sum_heading += agent.heading
                count += 1

        if count > 0:
            avg = sum_heading/float(count)
            avg -= self.heading

        return avg

    def cohesion(self, group):
        center_of_mass = Vector2D()
        count = 0

        for agent in group:
            if agent.pos != self.pos:
                center_of_mass += agent.pos
                count += 1

        if count > 0:
            center_of_mass /= float(count)
            
        return center_of_mass

    def separate(self, group):
        min = 80.0
        steerForce = Vector2D()

        for agent in group:
            if agent.pos != self.pos and agent.pos.distance(self.pos) < min:
                #distance self to closest neighbour
                diff = self.pos - agent.pos

                if diff.x >= 0 or diff.y >= 0:
                    diff = Vector2D(sqrt(min)-diff.x, sqrt(min)-diff.y)
                elif diff.x < 0 or diff.y < 0:
                    diff = Vector2D(-sqrt(min)-diff.x, sqrt(min)-diff.y)

                #difference force
                steerForce += diff.normalise() / diff.length()
                self.vel -= steerForce 

        return self.vel

    def find_neighbours(self):
        self.neighbours[:] = [n for n in self.world.agents if self.pos.distance(n.pos) < self.neighbour_radius]

    def avoid_walls(self):
        feeler1 = self.pos + self.vel * 0.5
        intersectPt = Vector2D()
        pt1 = Vector2D()
        pt2 = Vector2D()
        pt_distances = []
        #self.feelers = feeler1

        #identify if any feelers go outside border
        #iterate to find points forming the wall
        if feeler1.x <= 10.0 or feeler1.x >= 490.0:     #x borders
            #intersectPt = feeler1
            for w in self.walls:
                if w.x >= 490:                          #east wall
                    print(w)
                elif w.x <= 10.0:                       #west wall
                    print(w)

        if feeler1.y <= 10.0 or feeler1.y >= 490.0:     #y borders
            #intersectPt = feeler1
            for w in self.walls:
                if feeler1.y > w.y:                     #north
                    print(self.walls[0])
                    print()      
                elif feeler1.y < w.y:                   #south
                    print(self.walls[3])
                    print()