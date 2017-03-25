"""
simulator.py contains the main class for the simulator. It handles rendering the main window together with the main
user interaction code.
"""
import itertools
import pyglet
import src.util as util
from pyglet.window import key
from src.resources import DynamicAsssets
from src.robots.initio import Initio
from src.robots.pi2go import Pi2Go
from src.sprites.basicsprite import BasicSprite
from src.windows.objectwindow import ObjectWindow


class Simulator(pyglet.window.Window):
    def __init__(self, world_file="default.xml", selected_robot="Initio"):
        # create the rendering batches and groups
        self.sprites = {}
        self.batches = {}
        self.subgroups = {}
        self._handles = {}

        self.batches['bg_batch'] = pyglet.graphics.Batch()
        self.batches['fg_batch'] = pyglet.graphics.Batch()
        self.subgroups['background_group'] = pyglet.graphics.OrderedGroup(0)
        self.subgroups['foreground_group'] = pyglet.graphics.OrderedGroup(1)

        # load all the dynamic assets
        self.dyn_assets = DynamicAsssets(world_file, self.batches['bg_batch'], self.batches['fg_batch'],
                                         self.subgroups['background_group'], self.subgroups['foreground_group'])

        # create the window
        super(Simulator, self).__init__(self.dyn_assets.background_image.width, self.dyn_assets.background_image.height,
                                        fullscreen=False)
        self.object_window = None
        self.edit_mode = False
        self.fps_display = pyglet.clock.ClockDisplay()

        # decide which type of robot to load
        if selected_robot == "Initio":
            self.robot = Initio(line_map_sprite=self.dyn_assets.line_map_sprite,
                                sonar_map=self.dyn_assets.sonar_map,
                                batch=self.batches['fg_batch'],
                                window_width=self.dyn_assets.background_image.width,
                                window_height=self.dyn_assets.background_image.height)
        elif selected_robot == "Pi2Go":
            self.robot = Pi2Go(line_map_sprite=self.dyn_assets.line_map_sprite,
                               sonar_map=self.dyn_assets.sonar_map,
                               batch=self.batches['fg_batch'],
                               window_width=self.dyn_assets.background_image.width,
                               window_height=self.dyn_assets.background_image.height)

        # set the robot position based on the xml file
        self.robot.x = self.dyn_assets.robot_position[0]
        self.robot.y = self.dyn_assets.robot_position[1]
        self.robot.rotation = self.dyn_assets.robot_rotation

        # load all the keyboard and mouse handlers
        self.edit_mode_handlers = []

        self.push_handlers(self.on_mouse_press)
        for handler in self.robot.event_handlers:
            self.push_handlers(handler)

        for obj in self.dyn_assets.static_objects:
            for handler in obj.event_handlers:
                self.edit_mode_handlers.append(handler)

        if self.dyn_assets.line_map_sprite is not None:
            for handler in self.dyn_assets.line_map_sprite.event_handlers:
                self.edit_mode_handlers.append(handler)

        self.switch_handlers()

    def switch_handlers(self):
        """Switches between the edit mode and non edit mode handlers."""
        if self.edit_mode:
            for handler in self.edit_mode_handlers:
                self.push_handlers(handler)
        else:
            for handler in self.edit_mode_handlers:
                self.remove_handlers(handler)

    def on_draw(self):
        """Entry point for the main rendering function."""
        self.render()

    def render(self):
        """Main rendering function."""
        self.clear()
        self.batches['bg_batch'].draw()
        self.batches['fg_batch'].draw()
        # self.fps_display.draw()

    def spawn_edit_window(self):
        """Opens the edit toolbar."""
        self.object_window = ObjectWindow(160, self.dyn_assets.background_image.height, self.dyn_assets)
        x, y = self.get_location()
        self.object_window.set_location(x + self.dyn_assets.background_image.width,
                                        y)

    def on_mouse_press(self, x, y, button, modifiers):
        """Main entry point for a lot of the world editing interface code"""
        try:
            if self.edit_mode and button == 4:
                # if we're in edit mode (edit toolbar visible) and the user presses the right mouse button an
                # an operation is created

                # here we decide what operation is being performed based on the output of the object toolbar
                operation = None
                sprite_name, sprite_idx = self.object_window.get_selected_sprite_name()
                if sprite_name.startswith("delete"):
                    operation = "delete"
                elif sprite_name.startswith("line_map"):
                    operation = "line_map"
                elif sprite_name.startswith("background"):
                    operation = "background"
                else:
                    operation = "add"
                print operation
                selected_obj = None
                too_close = False

                # for add and delete operations we need to know where all the objects (including the line map) are
                # so we make a copy of the dynamic objects list so we can modify it without affecting other
                # parts of the simualator
                objects_list = self.dyn_assets.static_objects[:]

                # here we add the line map to our list of editable objects (only if we are looking to delete)
                if operation == "delete" and self.dyn_assets.line_map_sprite is not None:
                    objects_list.append(self.dyn_assets.line_map_sprite)

                # here we loop through all objects and do a radius check to see if the point at which the user
                # has clicked either contains an object or is very close to an existing object
                for obj in objects_list:
                    dsq = util.distancesq((x, y), (obj.x, obj.y))
                    thresh = min(obj.width, obj.height) ** 2
                    if operation == "delete":
                        thresh *= 0.25
                    if dsq < thresh:
                        selected_obj = obj
                        too_close = True

                # handling the background switching operation
                if operation == "background":
                    self.dyn_assets.background_sprite.delete()
                    sprite_image = self.object_window.get_selected_sprite_image()
                    util.center_image(sprite_image)
                    self.dyn_assets.background_sprite = BasicSprite(sprite_image,
                                                                    sprite_image.width / 2,
                                                                    sprite_image.height / 2,
                                                                    self.batches['bg_batch'],
                                                                    self.subgroups['background_group'], "background",
                                                                    sprite_idx)
                # handling the change line map operation
                elif operation == "line_map":

                    # if a line map already exists we need to delete it's handlers then delete the sprite itself
                    if self.dyn_assets.line_map_sprite is not None:
                        for handler in self.dyn_assets.line_map_sprite.event_handlers:
                            self.edit_mode_handlers.remove(handler)
                        self.dyn_assets.line_map_sprite.delete()

                    # create a new line map sprite
                    sprite_image = self.object_window.get_selected_sprite_image()
                    util.center_image(sprite_image)
                    self.dyn_assets.line_map_sprite = BasicSprite(sprite_image, x, y, self.batches['bg_batch'],
                                                                  self.subgroups['foreground_group'], "line_map",
                                                                  sprite_idx)

                    # update the actual line sensor used by the robot
                    self.robot.line_sensor_map.set_line_map(self.dyn_assets.line_map_sprite)

                    # add the new line maps handlers
                    for handler in self.dyn_assets.line_map_sprite.event_handlers:
                        self.edit_mode_handlers.append(handler)
                    self.switch_handlers()
                elif operation == "add" and not too_close:
                    # get the new object image
                    sprite_image = self.object_window.get_selected_sprite_image()
                    if sprite_image is not None:
                        # create the new sprite
                        sprt_obj = BasicSprite(sprite_image, x, y, self.batches['fg_batch'],
                                               self.subgroups['foreground_group'], "object", sprite_idx)

                        # add it to the list of dynamic objects and update the object handlers
                        self.dyn_assets.static_objects.append(sprt_obj)
                        for handler in sprt_obj.event_handlers:
                            self.edit_mode_handlers.append(handler)
                        self.switch_handlers()
                elif operation == "delete":
                    if selected_obj is not None:
                        # check if the object to delete is a line map or a regular static object
                        if selected_obj is self.dyn_assets.line_map_sprite:
                            self.robot.line_sensor_map.set_line_map(None)
                            self.dyn_assets.line_map_sprite = None
                        else:
                            self.dyn_assets.sonar_map.delete_rectangle(x, y, selected_obj.width, selected_obj.height)
                            self.dyn_assets.static_objects.remove(selected_obj)

                        # remove the object handlers
                        for handler in selected_obj.event_handlers:
                            if handler in self.edit_mode_handlers:
                                self.edit_mode_handlers.remove(handler)

                        # remove the object from the rendering batches and order
                        selected_obj.batch = None
                        selected_obj.group = None

                        # then delete the sprite and update the object handlers
                        selected_obj.delete()
                        self.switch_handlers()
        except AttributeError as e:
            print str(e)

    def on_key_press(self, symbol, modifiers):
        """Handler user keypresses
            E  =  Enable/Disable edit mode
            Q  =  Quit the simulator
        ."""
        if symbol == key.E:
            if self.edit_mode:
                print "edit mode disabled"
                self.edit_mode = False
                self.object_window.close()
                self.object_window = None
                self.redraw_sonar_map()
                self.dyn_assets.save_to_file()
            else:
                print "edit mode enabled"
                self.edit_mode = True
                self.spawn_edit_window()
            self.switch_handlers()
        if symbol == key.Q:
            pyglet.app.exit()

    def redraw_sonar_map(self):
        """This function updates the sonar map ensuring all new objects are added."""
        self.dyn_assets.sonar_map.clear_map()
        for obj in self.dyn_assets.static_objects:
            self.dyn_assets.sonar_map.insert_rectangle(obj.x, obj.y, obj.width, obj.height)

    def update(self, dt):
        """This function updates the simulator at each time step during normal operation this involves
         updating the position of the robot and check for any collisions between the robot and static
         objects.

         In edit mode this function also handles the destruction of the edit mode toolbar, allows static objects to
         be dragged around the screen using the mouse. Allows the line map to be moved using the mouse. And finally
          does collision checking between the static objects (which can be moved as we are in edit mode).
         """
        try:
            if self.edit_mode:
                # handle to closing of the edit toolbar
                if self.object_window is not None and self.object_window.close_me:
                    print "edit mode disabled"
                    self.edit_mode = False
                    self.object_window.close()
                    self.object_window = None
                    self.switch_handlers()
                    self.redraw_sonar_map()

                # handle mouse move for the static objects
                for obj in self.dyn_assets.static_objects:
                    if obj.mouse_move_state:
                        obj.prev_x = obj.x
                        obj.prev_y = obj.y
                        for other_obj in self.dyn_assets.static_objects:
                            if obj is not other_obj and obj.collides_with(other_obj):
                                obj.mouse_target_x = obj.prev_x
                                obj.mouse_target_y = obj.prev_y
                        obj.x = obj.mouse_target_x
                        obj.y = obj.mouse_target_y

                # collision checking for static objects
                for pair in itertools.combinations(self.dyn_assets.static_objects, 2):
                    if pair[0].collides_with(pair[1]):
                        if pair[0].mouse_move_state:
                            pair[0].x = pair[0].prev_x
                            pair[0].y = pair[0].prev_y
                        elif pair[1].mouse_move_state:
                            pair[1].x = pair[1].prev_x
                            pair[1].y = pair[1].prev_y

                # mouse move for the line map
                if self.dyn_assets.line_map_sprite is not None:
                    if self.dyn_assets.line_map_sprite.mouse_move_state:
                        self.dyn_assets.line_map_sprite.x = self.dyn_assets.line_map_sprite.mouse_target_x
                        self.dyn_assets.line_map_sprite.y = self.dyn_assets.line_map_sprite.mouse_target_y

            # update the robot position
            self.robot.update(dt)

            # robot to static object collision checking
            for obj in self.dyn_assets.static_objects:
                if self.robot.robot_collides_with(obj):
                    vec_x = self.robot.x - obj.x
                    vec_y = self.robot.y - obj.y
                    self.robot.velocity_x += vec_x * 2
                    self.robot.velocity_y += vec_y * 2
        except AttributeError:
            pass
