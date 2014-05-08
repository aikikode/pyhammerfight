#!/usr/bin/env python
from cocos.layer import Layer
import constants

__author__ = 'aikikode'


class GameCtrl(Layer):
    def __init__(self, game, hud, end_game):
        super(GameCtrl, self).__init__()
        self.game = game
        self.hud = hud
        self.end_game = end_game
        self.game.event_manager.push_handlers(self)
        self.score = 0
        self.enemy_spawn_interval = constants.DEFAULT_SPAWN_INTERVAL
        self.update_score()
        self.player_volume = 0.05
        # self.whistle_sound = pyglet.resource.media('whistle.wav', streaming=False)
        self.change_spawn_interval = False

    def update_score(self):
        self.hud.score.element.text = "Score: {}".format(self.score)
        self.hud.life.element.text = "Armor: {}".format(int(self.game.hammer.life))

    def on_enemy_kill(self, emitter, enemy):
        self.score += 1
        if enemy.bonus_type == constants.HEALTH_BONUS_TYPE:
            self.game.hammer.repair()
        elif enemy.bonus_type == constants.KILLALL_BONUS_TYPE:
            other_enemies = filter(lambda e: e != enemy and e.is_alive, self.game.enemies)
            for enemy in other_enemies:
                self.game.kill_enemy(enemy)
            for enemy in other_enemies:
                self.on_enemy_kill(emitter, enemy)
        self.update_score()
        if self.score % constants.KILL_LIMIT_SPAWN_INTERVAL_CHANGE == 0:
            self.change_spawn_interval = True
            self.game.unschedule(self.game.spawn_enemy)
            self.game.schedule_interval(self.game.spawn_enemy, self.enemy_spawn_interval)

    def on_enemy_hits_player(self, emitter):
        self.update_score()
        if not self.game.hammer.is_alive:
            self.game.game_ended = True
            self.end_game.show_game_end_screen("Score: {}".format(self.score),
                                               (self.game.width / 2., self.game.height / 2.))

    def on_enemy_spawn(self, emitter):
        if self.change_spawn_interval:
            self.enemy_spawn_interval = max(constants.MIN_SPAWN_INTERVAL, self.enemy_spawn_interval * constants.SPAWN_INTERVAL_COEF)
            self.game.unschedule(self.game.spawn_enemy)
            self.game.schedule_interval(self.game.spawn_enemy, self.enemy_spawn_interval)
            self.change_spawn_interval = False
