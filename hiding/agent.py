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

    def __init__(self, world=None, scale=30.0, mass=1.0, mode=None, color=None, speed=0.0):
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
        self.max_speed = speed
        self.max_force = 500.0

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

        self.neighbours = []
        self.neighbour_radius = 150

        # debug draw info?
        self.show_info = False

        # objects for hiding spots
        self.obstacles = [
            Vector2D(402,414),
            Vector2D(150,335),
            Vector2D(350,116)
        ]
        self.cur_dest = Vector2D()

    def calculate(self, delta):
        # calculate the current steering force
        mode = self.mode
        if mode == 'seek':
            for agent in self.world.agents:
                if agent.color == 'ORANGE':
                    prey = agent.pos
            force = self.seek(prey)
        elif mode == 'hiding':
            force = self.hide(self.world.hunter, self.obstacles, delta)
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

        #draw hiding spots
        egi.blue_pen()
        egi.circle(self.obstacles[0], 25)
        egi.circle(self.obstacles[1], 50)
        egi.circle(self.obstacles[2], 75)

        #draw detection box
        egi.blue_pen()
        length = 1.0 * (self.speed() / self.max_speed) * 3.0            #db length
        dbox = [
            Point2D(-1.0,  0.6),
            Point2D(length,  0.6),    #new
            Point2D(length,  0.0),    #new
            Point2D(length, -0.6),    #new
            Point2D(-1.0, -0.6)
        ]
        pts = self.world.transform_points(dbox, self.pos, self.heading, self.side, self.scale)
        egi.closed_shape(pts, False)

    def speed(self):
        return self.vel.length()

    #--------------------------------------------------------------------------

    def seek(self, target_pos):
        ''' move towards target position '''
        desired_vel = (target_pos - self.pos).normalise() * self.max_speed
        return (desired_vel - self.vel)

    def flee(self, hunter_pos):
        ''' move away from hunter position '''
        if self.pos.distance(hunter_pos) > 150:
            return Vector2D(0,0)

        flee_target = (self.pos - hunter_pos).normalise() * self.max_speed
        return (flee_target - self.vel)

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
        wt += Vector2D(uniform(-0.5,0.5) * jitter_tts, uniform(-0.5,0.5) * jitter_tts)
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

    def hide(self, hunter, objs, delta):
        temp = Vector2D()

        #assign hunter and prey
        for bot in self.world.agents:
            if bot.color == 'ORANGE':
                prey = bot
                prey.max_speed = 100.0
            elif bot.color == 'RED':
                hunter = bot
                hunter.max_speed = prey.max_speed * 0.25
                self.world.hunter = hunter

        #clear and reset existing targets and move
        if prey.pos.distance(self.cur_dest) < 10 and prey.pos.distance(hunter.pos) < 150:
            hunter.mode = 'hiding'
            self.world.targets.clear()
            self.cur_dest = Vector2D()

        #prey has found a hiding spot
        if self.cur_dest.is_zero() == False:
            hunter.mode = 'seek'
            if prey.pos.distance(hunter.pos) <= 150:
                hunter.max_speed = prey.max_speed * 0.75
                return prey.flee(hunter.pos)
            else:
                prey.max_speed = prey.max_speed * 2.0
                return prey.arrive(self.cur_dest, 'slow')
        #find a hiding spot
        elif self.cur_dest.is_zero() == True and prey.pos.distance(hunter.pos) < 150:
            prey.max_speed = prey.max_speed * 1.5

            #calculate best hiding spot (furthest from hunter)
            for spot in objs:
                if hunter.pos.distance(spot) > hunter.pos.distance(temp) or temp.is_zero() == True:
                    temp = spot
                    self.cur_dest = temp

                #build a list of targets showing valid hiding spots
                #which side of the object the target is on depends on where the hunter is relative to the object
                self.targetList(hunter, self.world.targets, 50, spot)
            return prey.seek(self.cur_dest)
        
        #eat prey if it is right ontop of the hunter
        if prey.pos.distance(hunter.pos) <= 50:
            for bot in self.world.agents:
                if bot.pos.distance(hunter.pos) <= 50:
                    self.world.agents.remove(bot)
            #self.world.agents.remove(prey)
            hunter.mode = 'wander'
            return Vector2D()

        return self.wander(delta)

    def targetList(self, hunter, targets, offset, obj):
        if hunter.pos.x > hunter.pos.y:
            if obj.x >= hunter.pos.x:
                targets.append(obj + Vector2D(offset,0))
                self.cur_dest = self.cur_dest + Vector2D(offset,0)
            else:
                targets.append(obj + Vector2D(-offset,0))
                self.cur_dest = self.cur_dest + Vector2D(-offset,0)
        else:
            if obj.y >= hunter.pos.y:
                targets.append(obj + Vector2D(0,offset))
                self.cur_dest = self.cur_dest + Vector2D(0,offset)
            else:
                targets.append(obj + Vector2D(0,-offset))
                self.cur_dest = self.cur_dest + Vector2D(0,-offset)
    
    def searchHidingSpots(self, hunter, circles):
        hunter_dest = Vector2D()

        #get closest hiding spot to hunter
        for spot in circles:
            print(hunter.pos.distance(spot))
            if hunter.pos.distance(spot) < hunter.pos.distance(hunter_dest) or hunter_dest.is_zero() == True:
                hunter_dest = spot

        #print(hunter_dest)
        return hunter_dest