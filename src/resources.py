"""
resources.py loads both the static and dynamic resources required for the simulator. Static resources are hardcoded
values, dynamic resources are loaded from an xml file.
"""
import xml.etree.ElementTree as ET
from tkinter.filedialog import *

import pyglet
from src.sensors.sonar import Map
from src.sprites.basicsprite import BasicSprite
from src.sprites.basicsprite import SwitchSprite
from . import util

NUM_LINE_MAPS = 6
NUM_BACKGROUNDS = 4

# Tell pyglet where to find the resources
pyglet.resource.path = ['resources']
pyglet.resource.reindex()

# Load the static resources
robot_image = pyglet.resource.image("robot/rover.png")
robot_image.width = 100
robot_image.height = 80
util.center_image(robot_image)

pi2go_image = pyglet.resource.image("robot/pi2go.png")
pi2go_image.width = 110
pi2go_image.height = 90
util.center_image(pi2go_image)
# pi2go_image.anchor_x = 26

sonar_image = pyglet.resource.image("robot/sonar.png")
sonar_image.width = 50
sonar_image.height = 32
sonar_image.anchor_x = 5
sonar_image.anchor_y = sonar_image.height / 2

# <Maduka>
# First load the menu buttons
edit_menu_button = pyglet.resource.image("menu_buttons/button_edit.png")
edit_menu_button.width = 50
edit_menu_button.height = 25

save_menu_button = pyglet.resource.image("menu_buttons/button_save.png")
save_menu_button.width = 50
save_menu_button.height = 25

close_menu_button = pyglet.resource.image("menu_buttons/button_close.png")
close_menu_button.width = 50
close_menu_button.height = 25

switch_image_on = pyglet.resource.image("static_objects/on_switch.png")
switch_image_on.width = 50
switch_image_on.height = 50

switch_image_off = pyglet.resource.image("static_objects/off_switch.png")
util.center_image(switch_image_off)
switch_image_off.width = 50
switch_image_off.height = 50

light_source_image = pyglet.resource.image("static_objects/light.png")
util.center_image(light_source_image)
light_source_image.width = 50
light_source_image.height = 48
# </Maduka>

# Load all available line maps
line_maps = []
for i in range(NUM_LINE_MAPS):
    line_map = pyglet.resource.image("line_maps/map" + str(i) + ".png")
    util.center_image(line_map)
    line_maps.append(line_map)

erase_image = pyglet.resource.image("robot/erase.png")
util.center_image(erase_image)

sheet_image = pyglet.resource.image("static_objects/boxesv2.png")
image_grid = pyglet.image.ImageGrid(sheet_image, 1, 9)

# Load all available backgrounds
backgrounds = []
for i in range(NUM_BACKGROUNDS):
    bg = pyglet.resource.image("backgrounds/bg" + str(i) + ".png")
    util.center_image(bg)
    backgrounds.append(bg)


class DynamicAsssets:
    def __init__(self, dynamic_assets_file, selected_robot_name, pyglet_sim_window, tk_start_window, bg_batch, fg_batch, bg_subgroup,
                                                                                                    fg_subgroup):
        # load xml file
        self.dynamic_assets_file = os.path.join(util.get_world_path(), dynamic_assets_file)
        tree = ET.parse(self.dynamic_assets_file)
        root = tree.getroot()

        # setup some member variables
        self.background_sprite = None
        self.static_objects = []
        self.robot_position = [0, 0]
        self.robot_rotation = 0
        self.start_window = pyglet_sim_window
        self.tk_start_window = tk_start_window
        # self.file_save_dialog = None
        # self.process_on_mouse_click = True

        self.original_file_str = None
        self.current_file_str = None

        # load the background image
        background_image_idx = int(root.attrib['background_index'])
        if 0 <= background_image_idx < len(backgrounds):
            self.background_image = backgrounds[background_image_idx]
            self.background_image.width = int(root.attrib['width'])
            self.background_image.height = int(root.attrib['height'])
            util.center_image(self.background_image)
            self.background_sprite = BasicSprite(self.background_image, self.background_image.width / 2,
                                                 self.background_image.height / 2,
                                                 bg_batch, bg_subgroup, "background", background_image_idx)

        # get the sonar map resolution and create the map
        self.sonar_resolution = int(root.attrib['sonar_resolution'])
        self.sonar_map = Map(self.background_image.width, self.background_image.height, self.sonar_resolution)

        # create line map members
        self.line_map_position = [0, 0]
        self.line_map_sprite = None

        # menu buttons
        self.edit_menu_button_sprite = None
        self.save_menu_button_sprite = None
        self.close_menu_button_sprite = None

        # switch
        self.switch_sprite = None

        # light source
        self.light_source_sprite = None

        # create rendering batches
        self.fg_batch = fg_batch
        self.fg_subgroup = fg_subgroup

        for child in root:
            if child.tag == "robot":
                # extract the robot position
                self.robot_position = [int(child.attrib["position_x"]), int(child.attrib["position_y"])]
                self.robot_rotation = int(child.attrib["rotation"])
            elif child.tag == "line_map":
                # load the line map if one exists
                line_map_index = int(child.attrib['index'])
                if 0 <= line_map_index < len(line_maps):
                    self.line_map_position = [int(child.attrib['position_x']), int(child.attrib['position_y'])]
                    self.line_map_sprite = BasicSprite(line_maps[line_map_index], self.line_map_position[0],
                                                       self.line_map_position[1],
                                                       bg_batch, fg_subgroup, "line_map", line_map_index)
            elif child.tag == "static_object":
                # load all static objects and create their sprites (objects are also added to the sonar map).
                index = int(child.attrib['index'])
                if 0 <= index < len(image_grid):
                    x = int(child.attrib['position_x'])
                    y = int(child.attrib['position_y'])
                    util.center_image(image_grid[index])
                    self.sonar_map.insert_rectangle(x, y, image_grid[index].width,
                                                    image_grid[index].height)
                    sprt_obj = BasicSprite(image_grid[index], x, y, bg_batch, bg_subgroup, "object", index)
                    self.static_objects.append(sprt_obj)

            # elif child.tag == "switch":
            #     x = int(child.attrib['position_x'])
            #     y = int(child.attrib['position_y'])
            #     util.center_image(switch_image_on)
            #     sw_obj = SwitchSprite(switch_image_on, x, y, fg_batch, fg_subgroup, "switch", -1)
            #     self.switch_sprite = sw_obj
            #     self.static_objects.append(sw_obj)
            #     # let the switch stay above every other object
            #     #self.fg_batch.append(sw_obj)

        # Load the menu buttons
        # "edit" menu button
        left_margin = 50.0
        top_margin = self.background_image.height - 25.0
        x = left_margin  # margin from the left edge of the window
        y = top_margin  # margin from the top edge of the window
        util.center_image(edit_menu_button)
        sw_obj = SwitchSprite(edit_menu_button, x, y, fg_batch, fg_subgroup, self.start_window, "menu_edit_button", -1)
        self.edit_menu_button_sprite = sw_obj
        self.static_objects.append(self.edit_menu_button_sprite)

        # "save" menu button
        x = left_margin + edit_menu_button.width  # margin from the left edge of the window
        y = top_margin  # margin from the top edge of the window
        util.center_image(save_menu_button)
        sw_obj = SwitchSprite(save_menu_button, x, y, fg_batch, fg_subgroup, self.start_window, "menu_save_button", -1)
        self.save_menu_button_sprite = sw_obj
        self.static_objects.append(self.save_menu_button_sprite)

        # "close" menu button
        x = left_margin + edit_menu_button.width + save_menu_button.width  # margin from the left edge of the window
        y = top_margin  # margin from the top edge of the window
        util.center_image(close_menu_button)
        sw_obj = SwitchSprite(close_menu_button, x, y, fg_batch, fg_subgroup, self.start_window, "menu_close_button",
                              -1)
        self.close_menu_button_sprite = sw_obj
        self.static_objects.append(self.close_menu_button_sprite)

        if selected_robot_name == "Pi2Go":
            x = self.background_image.width / 2.0  # Position the switch button at the lower center of the simulator window.
            y = 35.0
            util.center_image(switch_image_on)
            sw_obj = SwitchSprite(switch_image_on, x, y, fg_batch, fg_subgroup, self.start_window, "switch", -1)
            self.switch_sprite = sw_obj
            self.static_objects.append(sw_obj)
            # let the switch stay above every other object
            # self.fg_batch.append(sw_obj)

    ### Saving the world.
    def save_to_file(self):
        """Extract the current state of the world and save it to the xml file."""
        # Save off original file string
        print("In Save to file...")
        original_file = open(self.dynamic_assets_file, "r")
        self.original_file_str = original_file.read()
        original_file.close()

        root = ET.Element("world")
        tree = ET.ElementTree(root)
        root.set("background_index", str(self.background_sprite.idx))
        root.set("width", str(self.background_sprite.width))
        root.set("height", str(self.background_sprite.height))
        root.set("sonar_resolution", str(self.sonar_resolution))

        robot_element = ET.SubElement(root, "robot")
        robot_element.set("position_x", str(self.robot_position[0]))
        robot_element.set("position_y", str(self.robot_position[1]))
        robot_element.set("rotation", str(self.robot_rotation))

        if self.line_map_sprite is not None:
            line_map_element = ET.SubElement(root, "line_map")
            line_map_element.set("position_x", str(self.line_map_sprite.x))
            line_map_element.set("position_y", str(self.line_map_sprite.y))
            line_map_element.set("index", str(self.line_map_sprite.idx))

        for sprite_object in self.static_objects:
            if (sprite_object.object_type.startswith("switch")
                    or sprite_object.object_type.startswith("menu")):
                print("skipped menu or switch")
                continue  # No need to save the menu buttons and the switch buttons

            static_element = None
            if sprite_object.object_type.startswith("switch"):
                static_element = ET.SubElement(root, "switch")
            else:
                static_element = ET.SubElement(root, "static_object")
            static_element.set("position_x", str(sprite_object.x))
            static_element.set("position_y", str(sprite_object.y))
            static_element.set("index", str(sprite_object.idx))

        # tree.decode("UTF-8")
        tree.write(open(self.dynamic_assets_file, 'w'), encoding="unicode")
        current_file = open(self.dynamic_assets_file, "r")
        self.current_file_str = current_file.read()
        current_file.close()

        # compare original file and current file; if current is different create a new file for it and leave original as it is
        if self.original_file_str != self.current_file_str:
            # write the original to the original file, and write the updated to a new file
            original_file = open(self.dynamic_assets_file, "w")
            original_file.write(self.original_file_str)
            original_file.close()

            # fileExt = ".xml"
            # fileTypes = [('all files', '*.*'), ('world files', '*.xml')]
            # # define options for opening
            # options = {}
            # options['defaultextension'] = fileExt
            # options['filetypes'] = tuple(fileTypes)
            # options['initialdir'] = util.get_world_path()
            # options['initialfile'] = None
            # options['title'] = "Save As"

            savefile = self.my_save_file_proc()

            # Now make the original file string and current file string the same
            # to prevent the above dialog from loading up again unnecessarily - #quickfix
            # to the problem of tkinter file dialog that keeps reloading and reloading
            if savefile is not None:
                self.dynamic_assets_file = savefile
            print("-----Original world description-------")
            print(self.original_file_str)
            print("-----Current world description--------")
            print(self.current_file_str)
            print("File ", savefile, " has been updated")

    def my_save_file_proc(self):
        # root = Tk()
        # root.withdraw()
        fd = SaveAs(self.tk_start_window.window)
        filename = fd.show()
        if filename is not None and str(filename).strip() != "":
            new_file = open(filename, "w")
            new_file.write(self.current_file_str)
        return filename
