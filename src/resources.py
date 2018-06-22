"""
resources.py loads both the static and dynamic resources required for the simulator. Static resources are hardcoded
values, dynamic resources are loaded from an xml file.
"""
import os
import xml.etree.ElementTree as ET

import pyglet
import util
from src.sensors.sonar import Map
from src.sprites.basicsprite import BasicSprite

NUM_LINE_MAPS = 5
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
pi2go_image.anchor_x = 26

sonar_image = pyglet.resource.image("robot/sonar.png")
sonar_image.width = 50
sonar_image.height = 32
sonar_image.anchor_x = 5
sonar_image.anchor_y = sonar_image.height / 2

switch_image = pyglet.resource.image("static_objects/switch.png")
switch_image.width = 50
switch_image.height = 50

# Load all available line maps
line_maps = []
for i in range(NUM_LINE_MAPS):
    line_map = pyglet.resource.image("line_maps/map" + str(i) + ".png")
    util.center_image(line_map)
    line_maps.append(line_map)

erase_image = pyglet.resource.image("robot/erase.png")
util.center_image(erase_image)

sheet_image = pyglet.resource.image("static_objects/boxes.png")
image_grid = pyglet.image.ImageGrid(sheet_image, 1, 10)

# Load all available backgrounds
backgrounds = []
for i in range(NUM_BACKGROUNDS):
    bg = pyglet.resource.image("backgrounds/bg" + str(i) + ".png")
    util.center_image(bg)
    backgrounds.append(bg)


class DynamicAsssets:
    def __init__(self, dynamic_assets_file, bg_batch, fg_batch, bg_subgroup, fg_subgroup):
        # load xml file
        self.dynamic_assets_file = os.path.join(util.get_world_path(), dynamic_assets_file)
        tree = ET.parse(self.dynamic_assets_file)
        root = tree.getroot()

        # setup some member variables
        self.background_sprite = None
        self.static_objects = []
        self.robot_position = [0, 0]
        self.robot_rotation = 0

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
        
        # switch
        self.switch_sprite = None

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
                    sprt_obj = BasicSprite(image_grid[index], x, y, fg_batch, fg_subgroup, "object", index)
                    self.static_objects.append(sprt_obj)
                        
            elif child.tag == "switch":
                x = int(child.attrib['position_x'])
                y = int(child.attrib['position_y'])
                sw_obj = BasicSprite(switch_image, x, y, bg_batch, fg_subgroup, "switch", 5)
                self.switch_sprite = sw_obj

    def save_to_file(self):
        """Extract the current state of the world and save it to the xml file."""
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
            static_element = ET.SubElement(root, "static_object")
            static_element.set("position_x", str(sprite_object.x))
            static_element.set("position_y", str(sprite_object.y))
            static_element.set("index", str(sprite_object.idx))

        tree.write(open(self.dynamic_assets_file, 'w'), encoding="UTF-8")
