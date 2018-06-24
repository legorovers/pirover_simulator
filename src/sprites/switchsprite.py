"""
switchsprite.py is a subclass of pyglets sprite class for the Pi2Go Switch.
NOT USED FOR NOW.
"""

import pyglet


class SwitchSprite(pyglet.sprite.Sprite):
    def __init__(self, texture, x, y, batch, subgroup, object_type="sprite", idx=-1, window_width=800,
                 window_height=600):
        self.texture = texture
        super(BasicSprite, self).__init__(self.texture, batch=batch, group=subgroup)
        self.x = x
        self.y = y
        self.window_width = window_width
        self.window_height = window_height
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.mouse_move_state = False
        self.min_rad_sq = (0.5 * min(self.width, self.height)) ** 2
        self.in_collision = False
        self.event_handlers = [self, self.on_mouse_press]
        self.prev_x = x
        self.prev_y = y
        self.mouse_target_x = x
        self.mouse_target_y = y
        self.object_type = object_type
        self.idx = idx

# want to get it to change colour on press - then it is pressed or released.
    def update(self, dt):
        """Update position based on current velocity also check window bounds."""
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt

    def on_mouse_press(self, x, y, button, modifiers):
        """Uses a radius check to see if the sprite has been clicked, then sets the mouse move state to True so the
        sprite can be moved using the mouse."""
        if button == 1:
            dsq = (self.x - x) ** 2 + (self.y - y) ** 2
            # print dsq
            if dsq < self.min_rad_sq:
                self.mouse_move_state = True


