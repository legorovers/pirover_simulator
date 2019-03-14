"""
startwindow.py as opposed to all other windows uses TKinter instead of pyglet to provide a more traditional use
interface. It allows the user to select the world model and robot on startup.
"""
import os
from tkinter import *
import tkinter.simpledialog, tkinter.messagebox
import src.util as util

ROBOTS = ["Initio", "Pi2Go"]
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 500
SPACING = 50
PADDING = 5
DEFAULT_XML = "<?xml version='1.0' encoding='UTF-8'?>" + \
              "<world background_index='0' height='600' sonar_resolution='10' width='800'>" + \
              "<robot position_x='180' position_y='180' rotation='0' /> </world>"


class StartWindow(object):
    def __init__(self):
        self.window = Tk()
        self.window.title("Python Simulator")
        self.window.geometry("680x400")

        self.lbl1 = Label(self.window, text="World Files:", fg='black', font=("Helvetica", 16, "bold"))
        self.lbl1.grid(row=0, column=0, sticky=W)
        self.lbl2 = Label(self.window, text="Robot:", fg='black', font=("Helvetica", 16, "bold"))
        self.lbl2.grid(row=0, column=1, sticky=W)

        self.frm = Frame(self.window)
        self.frm.grid(row=1, column=0, sticky=N + S)
        self.window.rowconfigure(1, weight=1)
        self.window.columnconfigure(1, weight=1)

        self.scrollbar = Scrollbar(self.frm, orient="vertical")
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.files_listbox = Listbox(self.frm, width=40, yscrollcommand=self.scrollbar.set, font=("Helvetica", 12))
        self.files_listbox.pack(expand=True, fill=Y, padx=PADDING, pady=PADDING)

        self.scrollbar.config(command=self.files_listbox.yview)

        self.world_file_path = util.get_world_path()
        self.world_files_list = next(os.walk(self.world_file_path))[2]
        for wrld_file in self.world_files_list:
            self.files_listbox.insert(END, str(wrld_file))

        self.files_listbox.selection_set(first=0)

        self.frm2 = Frame(self.window)
        self.frm2.grid(row=2, column=0, sticky=N + S)
        self.delete_button = Button(self.frm2, text="Delete File", command=self.delete_file_callback)
        self.delete_button.pack(side=RIGHT, padx=PADDING, pady=PADDING)
        self.new_button = Button(self.frm2, text="New File", command=self.new_file_callback)
        self.new_button.pack(side=RIGHT, padx=PADDING, pady=PADDING)

        self.frm3 = Frame(self.window)
        self.frm3.grid(row=2, column=1, sticky=N + S)
        self.quit_button = Button(self.frm3, text="Quit", command=self.quit_callback)
        self.quit_button.pack(side=RIGHT, padx=PADDING, pady=PADDING)
        self.start_button = Button(self.frm3, text="Start Simulation", command=self.start_callback)
        self.start_button.pack(side=RIGHT, padx=PADDING, pady=PADDING)

        self.frm4 = Frame(self.window)
        self.frm4.grid(row=1, column=1, sticky=N + S)
        rover_path = os.path.join(util.get_resource_path(), "robot", "rover_small.gif")
        pi2go_path = os.path.join(util.get_resource_path(), "robot", "pi2go_small.gif")
        self.rover_image = PhotoImage(file=rover_path)
        self.pi2go_image = PhotoImage(file=pi2go_path)
        self.selected_robot = IntVar()
        self.selected_robot.set(-1)
        self.rover_radio = Radiobutton(self.frm4, text="simclient", image=self.rover_image, variable=self.selected_robot,
                                       value=0,
                                       relief=GROOVE)
        self.rover_radio.pack(padx=PADDING, pady=PADDING)
        self.pi2go_radio = Radiobutton(self.frm4, text="pi2go", image=self.pi2go_image, variable=self.selected_robot,
                                       value=1,
                                       relief=GROOVE)
        self.pi2go_radio.pack(padx=PADDING, pady=PADDING)
        self.rover_radio.select()

        self.selected_file = "None"
        self.selected_robot_name = "None"


    def start(self):
        """Provides an entry point to start with gui loop and return the selected file and robot once the window is
        closed."""
        self.window.mainloop()
        return self.selected_file, self.selected_robot_name

    def quit_callback(self):
        """Callback for the quit button."""
        self.window.destroy()
        self.window.quit()

    def start_callback(self):
        """Start button callback, the function extract the users selection from the world file listbox and robot
        radio buttons. Once extracted the window will be closed."""
        print("starting simulator")
        selected_items = list(map(int, self.files_listbox.curselection()))
        if len(selected_items) > 0:
            self.selected_file = self.world_files_list[selected_items[0]]
            selected_robot_idx = self.selected_robot.get()
            if 0 <= selected_robot_idx < len(ROBOTS):
                self.selected_robot_name = ROBOTS[selected_robot_idx]
            else:
                self.selected_robot_name = "None"
            self.quit_callback()
        else:
            print("no world file selected")

    def new_file_callback(self):
        """New file callback, this spawns a dialog box to allow the user to enter the new world file name. The new file
        is created with some default values and added to the list of available world files."""
        new_file = tkinter.simpledialog.askstring("New File", "Enter new filename")
        if new_file is None:
            return
        new_file += ".xml"
        try:
            text_file = open(os.path.join(self.world_file_path, new_file), "w")
            text_file.write(DEFAULT_XML)
            text_file.close()
            self.files_listbox.insert(END, new_file)
            self.world_files_list.append(new_file)
            print("new file created")
        except IOError as e:
            print("Error creating new file: " + str(e))

    def delete_file_callback(self):
        """Delete file callback, this extracts the selected world file and deletes the file from both the disk and
        the available world file list."""
        selected_items = list(map(int, self.files_listbox.curselection()))
        if len(selected_items) > 0:
            selected_file = self.world_files_list[selected_items[0]]
            result = tkinter.messagebox.askquestion("Delete", "Delete world file:" + selected_file + "?", icon='warning')
            if result == 'yes':
                try:
                    self.files_listbox.delete(selected_items[0])
                    to_remove = os.path.join(self.world_file_path, selected_file)
                    print(to_remove)
                    os.remove(to_remove)
                    self.world_files_list.remove(selected_file)
                except IOError as e:
                    print("Error deleting file: " + str(e))
