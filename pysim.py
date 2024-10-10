#! /usr/bin/env python
"""
pysim.py this script handles the loading of the simulator.
"""
from tkinter import DISABLED

import pyglet
from src.windows.simulator import Simulator
from src.windows.startwindow import StartWindow

# if __name__ == "__main__":
#     try:
#         # run the start window
#         start_window = StartWindow()
#         selected_file, selected_robot = start_window.start()
#         print(selected_file, selected_robot)
#
#         # run the simulator
#         if selected_file is not "None" and selected_robot is not None:
#             simulator = Simulator(selected_file, selected_robot)
#             pyglet.clock.schedule_interval(simulator.update, 1.0 / 30)
#             pyglet.app.run()
#     except KeyboardInterrupt:
#         print("Goodbye!")

if __name__ == "__main__":
    try:
        print(pyglet.version)
        assert (pyglet.version=="2.0.9")
        selected_file = ""
        selected_robot = ""
        start_window = None
        while selected_file == "" or (start_window is not None and start_window.selected_file != "None"):  # if it is None then select simulator dialog did something other than "launch simulator", which then implies that window close operation was carried out and app should quit.
            try:
                print(start_window.window.geometry) # Just a trick to check if start_window.window is anything but healthy - triggers an Exception if anything is amiss so we can create/or hold on to just one Tk() object which will serve the whole app lifecycle.
                # if no exception by here then start_window.window is still alive, and was just quitted
                # so simply restart the event loop
                # start_window.window.mainloop()
                start_window.refresh_world_filelist()
                selected_file, selected_robot = start_window.start()
                print(selected_file, selected_robot)
            except Exception:
                # start window probably doesn't exist, so make one
                # run the start window
                start_window = StartWindow()
                selected_file, selected_robot = start_window.start()
                print(selected_file, selected_robot)
            # run the simulator
            if selected_file != "None" and selected_robot != None:
                simulator = Simulator(selected_file, selected_robot, start_window)
                pyglet.clock.schedule_interval(simulator.update, 1.0 / 30)
                pyglet.app.run()
                # Clean up when simulator window closes
                pyglet.clock.unschedule(simulator.update)
                simulator.clear()
                simulator.close()
                # del(simulator)
                pyglet.app.exit()
    except KeyboardInterrupt:
        print("Goodbye!")
