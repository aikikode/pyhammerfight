import pyglet

__author__ = 'aikikode'

IMAGES_RESOURCE = "data/images"
# SOUNDS_RESOURCE = "data/sounds"
# CONFIG_FILE = "settings.cfg"

pyglet.resource.path = [IMAGES_RESOURCE, "/usr/local/lib/python2.7/dist-packages/cocos/resources/", "/usr/local/lib/python2.7/dist-packages/cocos2d-0.5.5-py2.7.egg/cocos/resources/"]
pyglet.resource.reindex()

FPS = 60
GAME_SPEED = 1