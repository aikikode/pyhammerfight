#!/usr/bin/env python
import random
import threading
from cocos.director import director
from cocos.sprite import Sprite
import cocos
import math
import pymunk
import constants

__author__ = 'aikikode'


class Enemy(object):
    def __init__(self, space, pos):
        self.is_alive = True
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
        self.sprite = Sprite("enemy.png")
        self.body.position = self.sprite.position = pos
        self.body.apply_force(-(self.body.mass + self.aim.mass) * space.gravity)
        # Connect aim and body with a DampedSpring - this should create the effect of flying through the air to the
        # player
        self.move = pymunk.constraint.DampedSpring(self.aim, self.body, (0, 0), (0, 0), 1, 600.0, 100)
        space.add(self.body, self.shape, self.aim, self.move)

    def update(self, dt):
        if not self.is_alive:
            self.sprite.opacity *= 0.91
        self.sprite.position = self.body.position

    def move_to(self, pos):
        self.aim.position = pos


class Hammer(object):
    def __init__(self, space, pos):
        # Mouse pointer 'body'
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
        body_shape.layers = 0b001
        self.body_shape = body_shape
        # Connect aim and hammer with a DampedSpring - this should create the effect of flying through the air
        self.hammer_move = pymunk.constraint.DampedSpring(self.aim, self.body, (0, 0), (0, 0), 1, 4000.0, 1.0)
        # Hammer sprite
        self.body_sprite = cocos.sprite.Sprite('body.png')
        # sword
        mass = 15
        inertia = pymunk.moment_for_box(mass, 8, 120)
        self.sword = pymunk.Body(mass, inertia)
        self.sword.position = (pos[0], pos[1] - 60)
        self.sword.angular_velocity_limit = 2 * math.pi  # Do not allow too rapid swinging, it's not natural and also
                                                         # can 'break' physics due to objects flying through the sword
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
        # body for more natural look
        self.sword_hammer = pymunk.constraint.PivotJoint(self.body, self.sword, (pos[0], pos[1] - 1))
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


class GameLayer(cocos.layer.Layer):
    is_event_handler = True  # enable pyglet's events

    def __init__(self):
        super(GameLayer, self).__init__()
        self.space = pymunk.Space()
        self.space.gravity = (0.0, -900.0)
        self.space.damping = 0.3  # Use damping to prevent eternal hammer swinging
        self.width, self.height = director.get_window_size()
        bg = cocos.sprite.Sprite('bg.jpg')
        bg.position = (self.width / 2., self.height / 2.)
        self.add(bg, z=-1)
        self.hammer = Hammer(self.space, (self.width / 2., self.height / 2.))
        z = 0
        for sprite in self.hammer.get_sprites():
            self.add(sprite, z=z)
            z += 1
        self.target = ((self.width / 2., self.height / 2.))
        self.enemies = []
        self.schedule_interval(self.update, 1./constants.FPS)
        self.schedule_interval(self.spawn_enemy, 5)
        self.space.add_collision_handler(3, 1, begin=self.on_enemy_hits_body)
        self.space.add_collision_handler(2, 3, begin=self.on_sword_hits_enemy)

    def on_enemy_hits_body(self, space, arbiter):
        print "enemy hits body"
        enemy = filter(lambda b: b.shape == arbiter.shapes[0], self.enemies)[0]
        return enemy.is_alive

    def on_sword_hits_enemy(self, space, arbiter):
        enemy = filter(lambda b: b.shape == arbiter.shapes[1], self.enemies)[0]
        enemy.is_alive = False
        threading.Timer(0.5, self.remove_enemy, args=[enemy]).start()
        return True

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
        for enemy in self.enemies[:]:
            enemy.move_to(self.target)
            enemy.update(dt)
            if enemy.body.position[1] < 30:
                self.remove_enemy(enemy)

    def remove_enemy(self, enemy):
        try:
            self.remove(enemy.sprite)
            self.space.remove(enemy.body, enemy.shape, enemy.aim, enemy.move)
            self.enemies.remove(enemy)
        except Exception:  # in case the enemy was already removed
            pass

    def spawn_enemy(self, dt):
        enemy = Enemy(self.space, (random.randint(30, self.width - 30), self.height + 50))
        self.enemies.append(enemy)
        self.add(enemy.sprite)


if __name__ == "__main__":
    director.init(resizable=False, width=1024, height=768)
    cocos.director.director.run(cocos.scene.Scene(GameLayer()))
    director.window.set_mouse_visible(False)

