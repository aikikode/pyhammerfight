import pyglet

__author__ = 'aikikode'

IMAGES_RESOURCE = "data/images"
# SOUNDS_RESOURCE = "data/sounds"
# CONFIG_FILE = "settings.cfg"

pyglet.resource.path = [IMAGES_RESOURCE]
pyglet.resource.reindex()

MAX_ENEMIES = 10

FPS = 60
GAME_SPEED = 1