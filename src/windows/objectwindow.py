"""
objectwindow.py is a subclass of pyglets window class to create a toolbar of objects and line maps to be used to modify
a simulated wold.
"""

import pyglet
import src.resources
import src.util
from pyglet.window import key
from src.sprites.selectablesprite import SelectSprite

SPACING = 50
PADDING = 8


class ObjectWindow(pyglet.window.Window):
    def __init__(self, window_width, window_height, dyn_assets):
        super(ObjectWindow, self).__init__(window_width, window_height, fullscreen=False,
                                           style=pyglet.window.Window.WINDOW_STYLE_TOOL)
        pyglet.gl.glClearColor(100, 100, 100, 255)
        self.dyn_assets = dyn_assets
        self.set_caption('Objects')
        self.main_batch = pyglet.graphics.Batch()
        self.sprites = []
        self.close_me = False

        # Add object thumbnails to the toolbar
        x = SPACING
        y = window_height - SPACING
        for idx, image in enumerate(src.resources.image_grid):
            src.util.center_image(image)
            sp = SelectSprite("object", idx, image, x, y, self.main_batch)
            self.sprites.append(sp)

            y -= image.height + PADDING
            if y < (SPACING/2.0):
                x += image.width + PADDING
                y = window_height - SPACING
            if x > (window_width - SPACING):
                break

        # Add line map thumbnails to the toolbar
        for idx, image in enumerate(src.resources.line_maps):
            scale = 48.0 / image.width
            sp = SelectSprite("line_map", idx, image, x, y, self.main_batch, scale)
            self.sprites.append(sp)

            y -= 48.0 + PADDING
            if y < (SPACING/2.0):
                x += 48.0 + PADDING
                y = window_height - SPACING

        # Add background thumbnails to the toolbar
        for idx, image in enumerate(src.resources.backgrounds):
            scale = 48.0 / image.width
            sp = SelectSprite("background", idx, image, x, y, self.main_batch, scale)
            self.sprites.append(sp)

            y -= 48.0 + PADDING
            if y < (SPACING/2.0):
                x += 48.0 + PADDING
                y = window_height - SPACING

        # Add the delete icon to the toolbar
        sp = SelectSprite("delete", -1, src.resources.erase_image, x, y, self.main_batch)
        self.sprites.append(sp)

        # Add all the mouse handlers to the window
        for sprite in self.sprites:
            for handler in sprite.event_handlers:
                self.push_handlers(handler)

    def on_key_press(self, symbol, modifiers):
        """Key handler to close the toolbar."""
        if symbol == key.E:
            self.close_me = True

    def get_selected_sprite_name(self):
        """Find the currently selected sprite and return it's name."""

        for sprite in self.sprites:
            if sprite.selected:
                return sprite.object_type, sprite.idx
        return "none", -1

    def get_selected_sprite_image(self):
        """Find the currently selected sprite and return it's image."""
        for sprite in self.sprites:
            if sprite.selected:
                return sprite.image
        return None

    def on_draw(self):
        """Main rendering function for the window."""
        self.clear()
        # self.next_button.draw()
        self.main_batch.draw()

