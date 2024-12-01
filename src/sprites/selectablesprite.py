"""
selectablesprite.py is a subclass of pyglets sprite class to create a selectable thumbnail for the objectwindow.
"""

import pyglet


class SelectSprite(pyglet.sprite.Sprite):
    def __init__(
        self, object_type, idx, texture, x, y, batch, scale=1.0, image_data=None
    ):
        self.texture = texture
        super(SelectSprite, self).__init__(self.texture, batch=batch)
        self.scale = scale
        self.x = x
        self.y = y
        self.object_type = object_type
        self.idx = idx
        self.event_handlers = [self, self.on_mouse_press]
        self.min_rad_sq = (0.5 * min(self.width, self.height)) ** 2
        self.opacity = 120
        self.selected = False
        self.image_data = image_data

    def on_mouse_press(self, x, y, button, modifiers):
        """Uses a radius check to see if this sprite has been click and sets the opacity of the image to indicate
        selection."""
        if button == 1:
            dsq = (self.x - x) ** 2 + (self.y - y) ** 2
            if dsq < self.min_rad_sq:
                self.selected = True
                self.opacity = 255
            else:
                self.selected = False
                self.opacity = 120
