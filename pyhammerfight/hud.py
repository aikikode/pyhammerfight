#!/usr/bin/env python
from cocos.director import director
from cocos.layer import Layer
from cocos.text import Label

__author__ = 'aikikode'


class Hud(Layer):
    def __init__(self):
        super(Hud, self).__init__()
        self.width, self.height = director.get_window_size()
        self.life = Label(text="0", position=((10, self.height - 50)),
                          font_name="Edit Undo Line BRK", font_size=35, italic=True)
        self.add(self.life)
        self.score = Label(text="0", position=((self.width - 260, self.height - 50)), anchor_x="left",
                           font_name="Edit Undo Line BRK", font_size=35, italic=True)
        self.add(self.score)
