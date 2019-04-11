#! /usr/bin/env python
"""
pysim.py this script handles the loading of the simulator.
"""
import pyglet
from src.windows.simulator import Simulator
from src.windows.startwindow import StartWindow

if __name__ == "__main__":
    try:
        # run the start window
        start_window = StartWindow()
        selected_file, selected_robot = start_window.start()
        print selected_file, selected_robot

        # run the simulator
        if selected_file is not "None" and selected_robot is not None:
            simulator = Simulator(selected_file, selected_robot)
            pyglet.clock.schedule_interval(simulator.update, 1.0 / 30)
            pyglet.app.run()
    except KeyboardInterrupt:
        print("Goodbye!")







