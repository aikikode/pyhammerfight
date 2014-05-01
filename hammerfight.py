#!/usr/bin/env python
import random
from cocos.director import director
from cocos.draw import Line
import cocos
import math
import pyglet
import pymunk
import constants

__author__ = 'aikikode'


class Ball(object):
    def __init__(self, space, pos):
        mass = 3
        radius = 30
        inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
        self.body = pymunk.Body(mass, inertia)
        body_shape = pymunk.Circle(self.body, radius, (0, 0))
        body_shape.elasticity = 0.9
        body_shape.friction = 0.8
        body_shape.collision_type = 2
        self.body_shape = body_shape
        self.sprite = cocos.sprite.Sprite("ball.png")
        self.body.position = self.sprite.position = pos
        space.add(self.body, self.body_shape)

    def update(self, dt):
        self.sprite.position = self.body.position


class Hammer(object):
    def __init__(self, space, pos):
        # Mouse pointer 'body'
        self.aim = pymunk.Body(1, 1)
        self.aim_shape = pymunk.Circle(self.aim, 1, (0, 0))
        self.aim_shape.layers = 0b000  # The 'aim' should not collide with any objects
        self.aim.position = pos
        # Hammer body
        mass = 6
        inertia = pymunk.moment_for_box(mass, 100, 100)
        self.body = pymunk.Body(mass, inertia)
        self.body.position = pos
        self.body.angular_velocity_limit = math.pi / 4
        self.body_angle_limit = math.pi / 4.  # Not to allow upside down flying and also for more natural look and feel
        body_shape = pymunk.Poly(self.body, [
            (-50, -50),
            (-50, 50),
            (50, 50),
            (50, -50)])
        body_shape.elasticity = 0.9
        body_shape.friction = 0.8
        body_shape.collision_type = 1
        body_shape.layers = 0b001
        self.body_shape = body_shape
        # Connect aim and hammer with a DampedSpring - this should create the effect of flying through the air
        self.hammer_move = pymunk.constraint.DampedSpring(self.aim, self.body, (0, 0), (0, 0), 1, 4000.0, 1.0)
        # Hammer sprite
        self.body_sprite = cocos.sprite.Sprite('body.png')
        # sword
        mass = 15
        inertia = pymunk.moment_for_box(mass, 30, 250)
        self.sword = pymunk.Body(mass, inertia)
        self.sword.position = (pos[0], pos[1] - 120)
        self.sword.angular_velocity_limit = 2 * math.pi  # Do not allow too rapid swinging, it's not natural and also
                                                         # can 'break' physics due to objects flying through the sword
        sword_shape = pymunk.Poly(self.sword, [
            (-15, -135),
            (-15, 115),
            (15, 115),
            (15, -135)])
        sword_shape.elasticity = 0.9
        sword_shape.friction = 0.8
        sword_shape.layers = 0b010
        sword_shape.collision_type = 1
        self.sword_shape = sword_shape
        # Connect hammer and sword with a joint - place the joint a little below the center of the mass of the main
        # body for more natural look
        self.sword_hammer = pymunk.constraint.PivotJoint(self.body, self.sword, (pos[0], pos[1] - 10))
        # Sword sprite
        self.sword_sprite = cocos.sprite.Sprite('sword.png')
        # Make the hammer 'fly' by applying the force opposite to the gravity
        self.body.apply_force(-(1 + self.body.mass + self.sword.mass) * space.gravity)
        space.add(self.body, self.body_shape, self.aim, self.aim_shape, self.hammer_move, self.sword, self.sword_shape,
                  self.sword_hammer)
        self.space = space

    def get_sprites(self):
        return self.body_sprite, self.sword_sprite

    def update(self, dt):
        self.body_sprite.position = self.body.position
        if self.body.angle > self.body_angle_limit:
            self.body.angle = self.body_angle_limit
        elif self.body.angle < -self.body_angle_limit:
            self.body.angle = -self.body_angle_limit
        self.body_sprite.rotation = -self.body.angle * 180. / math.pi
        self.sword_sprite.position = self.sword.position
        self.sword_sprite.rotation = -self.sword.angle * 180. / math.pi

    def move_to(self, pos):
        # Place the aim body to the mouse pointer position - the hammer will follow it due to the joint
        self.aim.position = pos


class TestJoints(cocos.layer.Layer):
    is_event_handler = True  # enable pyglet's events

    def __init__(self):
        super(TestJoints, self).__init__()
        self.space = pymunk.Space()
        self.space.gravity = (0.0, -900.0)
        self.space.damping = 0.3  # Use damping to prevent eternal hammer swinging
        self.width, self.height = director.get_window_size()
        self.hammer = Hammer(self.space, (self.width / 2., self.height / 2.))
        for sprite in self.hammer.get_sprites():
            self.add(sprite)
        self.target = ((self.width / 2., self.height / 2.))
        self.balls = []
        self.schedule_interval(self.update, 1./constants.FPS)
        self.schedule_interval(self.spawn_ball, 5)
        self.line = Line(self.hammer.aim.position, self.hammer.body.position, (255, 255, 255, 255))
        self.add(self.line)

    ## Disable mouse press for now
    # def on_mouse_press(self, x, y, buttons, modifiers):
    #     posx, posy = director.get_virtual_coordinates(x, y)
    #     print posx, posy

    def on_mouse_motion(self, x, y, dx, dy):
        self.target = ((x, y))

    def update(self, dt):
        dt = constants.GAME_SPEED / float(constants.FPS)
        self.space.step(dt)
        self.hammer.move_to(self.target)
        self.hammer.update(dt)
        for ball in self.balls[:]:
            ball.update(dt)
            if ball.body.position[1] < 0:
                self.remove(ball.sprite)
                self.space.remove(ball.body, ball.body_shape)
                self.balls.remove(ball)
        self.remove(self.line)
        self.line = Line(self.hammer.aim.position, self.hammer.body.position, (255, 255, 255, 255))
        self.add(self.line)

    def spawn_ball(self, dt):
        # ball = Ball(self.space, (random.randint(100, self.width - 100), self.height - 50))
        ball = Ball(self.space, (self.width / 2., self.height - 50))
        self.balls.append(ball)
        self.add(ball.sprite)


if __name__ == "__main__":
    director.init(resizable=False, width=1024, height=768)
    cocos.director.director.run(cocos.scene.Scene(TestJoints()))
    director.window.set_mouse_visible(False)

