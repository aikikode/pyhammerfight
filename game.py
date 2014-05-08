#!/usr/bin/env python
import random
import threading
from cocos.director import director
from cocos.layer import Layer, ColorLayer
from cocos.scene import Scene
from cocos.sprite import Sprite
import cocos
from cocos.text import Label
import pyglet
import pymunk

import constants
from gamectrl import GameCtrl
from hud import Hud
from models import Hammer, Enemy

__author__ = 'aikikode'


class Game(Layer):
    is_event_handler = True  # enable pyglet's events

    def __init__(self):
        super(Game, self).__init__()
        self.game_ended = False
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
        self.schedule_interval(self.update, 1. / constants.FPS)
        self.schedule_interval(self.spawn_enemy, constants.DEFAULT_SPAWN_INTERVAL)
        self.space.add_collision_handler(3, 1, post_solve=self.on_enemy_hits_body)
        self.space.add_collision_handler(2, 3, post_solve=self.on_sword_hits_enemy)
        # Configure event manager to send game events to control module
        self.event_manager = pyglet.event.EventDispatcher()
        self.event_manager.register_event_type('on_enemy_kill')
        self.event_manager.register_event_type('on_enemy_hits_player')
        self.event_manager.register_event_type('on_enemy_spawn')

    def on_enemy_hits_body(self, space, arbiter):
        enemy = filter(lambda b: b.shape == arbiter.shapes[0], self.enemies)[0]
        if enemy.is_alive and self.hammer.is_alive:
            self.hammer.take_damage(arbiter.total_impulse.length)
            self.event_manager.dispatch_event('on_enemy_hits_player', self)
        return enemy.is_alive

    def on_sword_hits_enemy(self, space, arbiter):
        enemy = filter(lambda b: b.shape == arbiter.shapes[1], self.enemies)[0]
        enemy.take_damage(arbiter.total_impulse.length)
        if not enemy.is_alive:
            self.event_manager.dispatch_event('on_enemy_kill', self, enemy)
            threading.Timer(0.5, self.remove_enemy, args=[enemy]).start()
        return True

    def kill_enemy(self, enemy):
        enemy.suicide()
        threading.Timer(0.5, self.remove_enemy, args=[enemy]).start()

    ## Disable mouse clicks for now
    # def on_mouse_press(self, x, y, buttons, modifiers):
    #     posx, posy = director.get_virtual_coordinates(x, y)
    #     print posx, posy

    def on_mouse_motion(self, x, y, dx, dy):
        self.target = ((x, y))

    def update(self, dt):
        if not self.game_ended:
            dt = constants.GAME_SPEED / float(constants.FPS)
            self.space.step(dt)
            self.hammer.move_to(self.target)
            self.hammer.update(dt)
            for enemy in self.enemies[:]:
                k = 1.5
                enemy.move_to(((1 + k) * self.hammer.body.position[0] - k * enemy.body.position[0],
                               (1 + k) * self.hammer.body.position[1] - k * enemy.body.position[1]))
                if (enemy.body.position - self.hammer.body.position).length < 100:
                    enemy.body.apply_impulse(self.hammer.body.position - enemy.body.position, (0, 0))
                enemy.update(dt)

    def remove_enemy(self, enemy):
        try:
            self.remove(enemy.sprite)
            self.space.remove(enemy.body, enemy.shape, enemy.aim, enemy.move)
            self.enemies.remove(enemy)
        except Exception:  # in case the enemy was already removed
            pass

    def spawn_enemy(self, dt):
        def get_random_with_probability(prob_distr):
            assert prob_distr
            r = random.uniform(0, 1)
            s = 0
            for item in prob_distr:
                s += item[1]
                if s >= r:
                    return item[0]
        if len(self.enemies) < constants.MAX_ENEMIES and not self.game_ended:
            enemy_type = get_random_with_probability([[0, 0.9],
                                                      [constants.HEALTH_BONUS_TYPE, 0.07],
                                                      [constants.KILLALL_BONUS_TYPE, 0.03]])
            enemy = Enemy(self, (random.randint(30, self.width - 30), self.height + 50), bonus_type=enemy_type)
            self.enemies.append(enemy)
            self.add(enemy.sprite)
            self.event_manager.dispatch_event('on_enemy_spawn', self)


class EndGame(Layer):
    is_event_handler = True  # enable pyglet's events

    def __init__(self):
        super(EndGame, self).__init__()
        self.background = ColorLayer(0, 0, 0, 170)
        self.header_label = Label()
        self.label = Label()

    def reset(self):
        self.remove(self.background)
        self.remove(self.label)

    def show_game_end_screen(self, text="", position=(0, 0)):
        self.add(self.background)
        self.header_label = Label("You died!", (position[0], position[1] + 50), font_name='Edit Undo Line BRK', font_size=32, anchor_x='center')
        self.label = Label(text, position, font_name='Edit Undo Line BRK', font_size=32, anchor_x='center')
        self.add(self.header_label)
        self.add(self.label)


def get_new_game():
    scene = Scene()
    game = Game()
    hud = Hud()
    end_game = EndGame()
    game_ctrl = GameCtrl(game, hud, end_game)
    scene.add(game, z=0, name="game layer")
    scene.add(game_ctrl, z=1, name="game control layer")
    scene.add(hud, z=2, name="hud layer")
    scene.add(end_game, z=3, name="end game layer")
    return scene