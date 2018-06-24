#! /usr/bin/env python
"""
main.py this script handles the loading of the simulator. Under OSX TKinter and Pyglet will not work together so
they must be imported separately. This workaround is less than elegant as it slows the loading of the simulator
after the user has selected a world filea and robot but on ther otherhand allows the simulator to run on all platforms.
"""
try:
    # load tkinter + other deps for the start window
    from src.windows.startwindow import StartWindow

    # run the start window
    start_window = StartWindow()
    selected_file, selected_robot = start_window.start()
    print selected_file, selected_robot

    # load pyglet + other deps for the simulator
    import pyglet
    from src.windows.simulator import Simulator

    # run the simulator
    if selected_file is not "None" and selected_robot is not None:
        simulator = Simulator(selected_file, selected_robot)
        pyglet.clock.schedule_interval(simulator.update, 1.0 / 30)
        pyglet.app.run()
except KeyboardInterrupt:
    print "Goodbye!"
