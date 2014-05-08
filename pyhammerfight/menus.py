#!/usr/bin/env python
from cocos.director import director
from cocos.layer import Layer, MultiplexLayer
from cocos.menu import MenuItem, Menu, CENTER, shake, shake_back
from cocos.scene import Scene
from cocos.sprite import Sprite
import cocos
import pyglet

import constants
import game

__author__ = 'aikikode'


class BackgroundLayer(Layer):
    def __init__(self):
        super(BackgroundLayer, self).__init__()
        self.width, self.height = director.get_window_size()
        # Background image
        bg = cocos.sprite.Sprite('bg.jpg')
        bg.position = (self.width / 2., self.height / 2.)
        self.add(bg, z=0)


class MainMenu(Menu):
    def __init__(self):
        super(MainMenu, self).__init__('PyHammerfight')
        self.menu_anchor_x = CENTER
        self.menu_anchor_y = CENTER

        self.font_title['font_name'] = 'Edit Undo Line BRK'
        self.font_title['font_size'] = 72
        self.font_title['color'] = (255, 255, 255, 255)
        self.font_item['font_name'] = 'Edit Undo Line BRK',
        self.font_item['font_size'] = 46
        self.font_item['color'] = (255, 255, 255, 200)
        self.font_item_selected['font_name'] = 'Edit Undo Line BRK'
        self.font_item_selected['font_size'] = 56
        self.font_item_selected['color'] = (255, 255, 255, 255)

        items = [MenuItem('Start', self.on_start_game),
                 # MenuItem('Options', self.on_options),
                 # MenuItem('Scores', self.on_scores),
                 MenuItem('Quit', self.on_quit)]
        self.create_menu(items, shake(), shake_back())

    def on_start_game(self):
        director.push(game.get_new_game())

    def on_options(self):
        pass

    def on_scores(self):
        pass

    def on_quit(self):
        pyglet.app.exit()


def new_game():
    director.init(resizable=False, width=1024, height=768)
    scene = Scene()
    scene.add(BackgroundLayer(), z=0)
    scene.add(MultiplexLayer(
        MainMenu(),
    ), z=1)
    director.run(scene)