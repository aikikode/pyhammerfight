#!/usr/bin/env python
from cocos.layer import Layer

__author__ = 'aikikode'


class GameCtrl(Layer):
    def __init__(self, game, hud, end_game):
        super(GameCtrl, self).__init__()
        self.game = game
        self.hud = hud
        self.end_game = end_game
        self.game.event_manager.push_handlers(self)
        self.score = 0
        self.enemy_spawn_interval = 5
        self.update_score()
        self.player_volume = 0.05
        # self.whistle_sound = pyglet.resource.media('whistle.wav', streaming=False)

    def update_score(self):
        self.hud.score.element.text = "Score: {}".format(self.score)
        self.hud.life.element.text = "Armor: {}".format(int(self.game.hammer.life))

    def on_enemy_kill(self, emitter):
        self.score += 1
        self.update_score()
        if self.score % 3 == 0:
            self.enemy_spawn_interval = max(1, self.enemy_spawn_interval * 0.8)
            self.game.unschedule(self.game.spawn_enemy)
            self.game.schedule_interval(self.game.spawn_enemy, self.enemy_spawn_interval)


    def on_enemy_hits_player(self, emitter):
        self.update_score()
        if not self.game.hammer.is_alive:
            self.game.game_ended = True
            self.end_game.show_game_end_screen("Score: {}".format(self.score),
                                               (self.game.width / 2., self.game.height / 2.))
