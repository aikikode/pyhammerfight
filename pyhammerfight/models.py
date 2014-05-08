#!/usr/bin/env python
import math

import cocos
from cocos.actions import Repeat, RotateBy, ScaleBy, Reverse
from cocos.sprite import Sprite
import pyglet
import pymunk

import constants


__author__ = 'aikikode'


class Enemy(object):
    def __init__(self, game, pos, bonus_type=0):
        self._game = game
        self.is_alive = True
        self._life = constants.ENEMY_ARMOR
        self.bonus_type = bonus_type
        # Mouse pointer 'body'
        self.aim = pymunk.Body(1, 1)
        self.aim_shape = pymunk.Circle(self.aim, 1, (0, 0))
        self.aim_shape.layers = 0b000  # The 'aim' should not collide with any objects
        self.aim.position = pos
        # Enemy body
        mass = 3
        radius = 15
        inertia = pymunk.moment_for_circle(mass, 0, radius, (0, 0))
        self.body = pymunk.Body(mass, inertia)
        shape = pymunk.Circle(self.body, radius, (0, 0))
        shape.elasticity = 0.9
        shape.friction = 0.8
        shape.collision_type = 3
        self.shape = shape
        if not bonus_type:
            self.sprite = Sprite("enemy.png")
        elif bonus_type == constants.HEALTH_BONUS_TYPE:
            animation = pyglet.resource.animation("bonus_enemy_green.gif")
            self.sprite = Sprite(animation)
        elif bonus_type == constants.KILLALL_BONUS_TYPE:
            animation = pyglet.resource.animation("bonus_enemy_yellow.gif")
            self.sprite = Sprite(animation)
        self.sprite.do(Repeat(RotateBy(360, 2)))
        self.body.position = self.sprite.position = pos
        self.body.apply_force(-(self.body.mass + self.aim.mass) * game.space.gravity)
        # Connect aim and body with a DampedSpring - this should create the effect of flying through the air to the
        # player
        self.move = pymunk.constraint.DampedSpring(self.aim, self.body, (0, 0), (0, 0), 1, 600.0, 100)
        game.space.add(self.body, self.shape, self.aim, self.move)

    def update(self, dt):
        if not self.is_alive:
            self.sprite.opacity *= 0.91
        self.sprite.position = self.body.position

    def move_to(self, pos):
        self.aim.position = pos

    def take_damage(self, damage):
        self._life -= damage
        if self._life <= 0:
            self._life = 0
            self.is_alive = False
        elif self._life < 1500 and not self.bonus_type:
            self._game.remove(self.sprite)
            self.sprite = Sprite("enemy_damaged.png")
            self.sprite.do(Repeat(RotateBy(360, 1)))
            self._game.add(self.sprite)

    def suicide(self):
        self._life = 0
        self.is_alive = False


class Hammer(object):
    def __init__(self, space, pos):
        self.is_alive = True
        self.life = constants.PLAYER_ARMOR
        # Mouse pointer 'body'
        # We need to make the hammer follow the cursor, but with some delay to create the effect of flying through the
        # air. We achieve this by adding an invisible damped string between the mouse pointer and the hammer. For this
        # we need to create a 'body' for mouse pointer to connect a damped string to.
        self.aim = pymunk.Body(1, 1)
        self.aim_shape = pymunk.Circle(self.aim, 1, (0, 0))
        self.aim_shape.layers = 0b000  # The 'aim' should not collide with any objects
        self.aim.position = pos
        # Hammer body
        mass = 6
        inertia = pymunk.moment_for_box(mass, 34, 45)
        self.body = pymunk.Body(mass, inertia)
        self.body.position = pos
        self.body.angular_velocity_limit = math.pi / 4
        self.body_angle_limit = math.pi / 4.  # Not to allow upside down flying and also for more natural look and feel
        body_shape = pymunk.Poly(self.body, [
            (-17, -22.5),
            (-17, 22.5),
            (17, 22.5),
            (17, -22.5)])
        body_shape.elasticity = 0.9
        body_shape.friction = 0.8
        body_shape.collision_type = 1
        body_shape.layers = 0b001  # set layers for body and sword (below) to forbid their collision
        self.body_shape = body_shape
        # Connect aim and hammer with a DampedSpring - this should create the effect of flying through the air
        self.hammer_move = pymunk.constraint.DampedSpring(self.aim, self.body, (0, 0), (0, 0), 1, 4000.0, 1.0)
        # Hammer sprite
        self.body_sprite = Sprite('body.png')
        self.propeller_sprite = Sprite('propeller.png')
        # Scaling the propeller back and forth will create the effect of its movement
        action = ScaleBy(0.2, 0.1)
        self.propeller_sprite.do(Repeat(action + Reverse(action)))
        # Sword
        mass = 15
        inertia = pymunk.moment_for_box(mass, 8, 120)
        self.sword = pymunk.Body(mass, inertia)
        self.sword.position = (pos[0], pos[1] - 60)
        self.sword.angular_velocity_limit = 1.8 * math.pi  # Do not allow too rapid swinging, it's not natural and also
        # can 'break' physics due to enemies flying through the sword
        sword_shape = pymunk.Poly(self.sword, [
            (-4, -60),
            (-4, 60),
            (4, 60),
            (4, -60)])
        sword_shape.elasticity = 0.9
        sword_shape.friction = 0.8
        sword_shape.layers = 0b010
        sword_shape.collision_type = 2
        self.sword_shape = sword_shape
        # Connect hammer and sword with a joint - place the joint a little below the center of the mass of the main
        # body to make the body return to vertical state
        self.sword_hammer = pymunk.constraint.PivotJoint(self.body, self.sword, (pos[0], pos[1] - 1))
        # Sword sprite
        self.sword_sprite = cocos.sprite.Sprite('sword.png')
        # Make the hammer 'fly' by applying the force opposite to the gravity
        self.body.apply_force(-(self.aim.mass + self.body.mass + self.sword.mass) * space.gravity)
        space.add(self.body, self.body_shape, self.aim, self.aim_shape, self.hammer_move, self.sword, self.sword_shape,
                  self.sword_hammer)
        self.space = space

    def get_sprites(self):
        return self.body_sprite, self.propeller_sprite, self.sword_sprite

    def update(self, dt):
        self.body_sprite.position = self.body.position
        if self.body.angle > self.body_angle_limit:
            self.body.angle = self.body_angle_limit
        elif self.body.angle < -self.body_angle_limit:
            self.body.angle = -self.body_angle_limit
        self.propeller_sprite.rotation = self.body_sprite.rotation = -self.body.angle * 180. / math.pi
        # Place propeller
        delta = 21  # the height of propeller location from player's center of the mass
        self.propeller_sprite.position = (self.body_sprite.position[0] - delta * math.sin(self.body.angle),
                                          self.body_sprite.position[1] + delta * math.cos(self.body.angle))
        self.sword_sprite.position = self.sword.position
        self.sword_sprite.rotation = -self.sword.angle * 180. / math.pi

    def move_to(self, pos):
        # Place the aim body to the mouse pointer position - the hammer will follow it due to the joint
        self.aim.position = pos

    def take_damage(self, damage):
        self.life -= damage
        if self.life <= 0:
            self.life = 0
            self.is_alive = False

    def repair(self):
        self.life = constants.PLAYER_ARMOR
