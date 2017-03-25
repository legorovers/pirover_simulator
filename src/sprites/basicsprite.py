"""
basicsprite.py is a subclass of pyglets sprite class and adds some additional data members and convenience functions
in particular it adds a velocity model, window bounds checking, mouse handlers and AABB collision checking.
"""

import pyglet


class BasicSprite(pyglet.sprite.Sprite):
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
        self.event_handlers = [self, self.on_mouse_press, self.on_mouse_release, self.on_mouse_drag]
        self.prev_x = x
        self.prev_y = y
        self.mouse_target_x = x
        self.mouse_target_y = y
        self.object_type = object_type
        self.idx = idx

    def update(self, dt):
        """Update position based on current velocity also check window bounds."""
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        self.check_bounds()

    def check_bounds(self):
        """Check window bounds"""
        rad = max(self.image.width, self.image.height) / 2.0
        min_x = rad
        min_y = rad
        max_x = self.window_width - rad
        max_y = self.window_height - rad
        if self.x < min_x:
            self.x = min_x
        if self.y < min_y:
            self.y = min_y
        if self.x > max_x:
            self.x = max_x
        if self.y > max_y:
            self.y = max_y

    def on_mouse_press(self, x, y, button, modifiers):
        """Uses a radius check to see if the sprite has been clicked, then sets the mouse move state to True so the
        sprite can be moved using the mouse."""
        if button == 1:
            dsq = (self.x - x) ** 2 + (self.y - y) ** 2
            # print dsq
            if dsq < self.min_rad_sq:
                self.mouse_move_state = True

    def on_mouse_release(self, x, y, button, modifiers):
        """Sets the mouse move state to false once the mouse button is released."""
        self.mouse_move_state = False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """Sets target x,y position for the sprite based on the mouse pointer."""
        if self.mouse_move_state:
            self.mouse_target_x = x
            self.mouse_target_y = y

    def collides_with(self, other_object, use_mouse=False):
        """Simple axis aligned bounding box collision detections to check if this sprite collides with another."""
        # AABB collision detection
        if use_mouse:
            if self.mouse_target_x < other_object.x + other_object.width and \
                                    self.mouse_target_x + self.width > other_object.x and \
                            self.mouse_target_y < other_object.y + other_object.height and \
                                    self.height + self.mouse_target_y > other_object.y:
                return True
        else:
            if self.x < other_object.x + other_object.width and \
                                    self.x + self.width > other_object.x and \
                            self.y < other_object.y + other_object.height and \
                                    self.height + self.y > other_object.y:
                return True
        return False
