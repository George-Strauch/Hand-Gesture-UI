import json
import tkinter as tk
import math
from time import sleep
from threading import Thread
from state_controller import StateController


class DisplayModule(tk.Toplevel):
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        super().__init__(self.root)
        # self.width, self.height = self.winfo_screenwidth(), self.winfo_screenheight()
        self.width, self.height = 400, 400
        self.overrideredirect(True)  # Remove window decorations
        self.attributes("-topmost", True)  # Keep on top
        self.geometry(f"{self.width}x{self.height}+1200+500")  # Full screen overlay
        self.config(bg='white')
        # self.attributes("-alpha", 0.5 )  # Make white color transparent
        self.canvas = tk.Canvas(self, width=400, height=400, bg='white', highlightthickness=0)
        self.canvas.pack()
        self.is_hidden = False
        self.last_state = None
        # self.draw_circle_nav()

        self.nav_wheel_vars = {}
        self.nav_wheel_fields = ["selected_index", "color", "menu_labels"]

    def draw_circle_nav(self, selected_index, color, menu_labels):
        self.canvas.delete("all")  # Clear the canvas
        r = min(self.width, self.height) // 4
        cx, cy = self.width // 2, self.width // 2

        # print(labels)

        angle_step = 2.0 * math.pi / len(menu_labels)
        # print("highlight_index", highlight_index)
        for i, label in enumerate(menu_labels):
            start_angle = i * angle_step
            end_angle = start_angle + angle_step

            if i != selected_index:
                c = "gray"
            else:
                c = color
            # color = "orange" if label == f"{highlight_index}" else "white"
            self.canvas.create_arc(
                cx - r,
                cy - r,
                cx + r,
                cy + r,
                start=start_angle * 180 / math.pi,
                extent=angle_step * 180 / math.pi,
                fill=c,
                width=2,
                style=tk.PIESLICE
            )
            # Draw the label
            label_angle = start_angle + angle_step / 2
            label_radius = r * 0.5
            label_x = cx + label_radius * math.cos(label_angle)
            label_y = cy + label_radius * -math.sin(label_angle)
            self.canvas.create_text(label_x, label_y, text=label)

    def process_slice_of_time_view(self, info):
        """
        this function is called in a loop forever with info about the current state
        :param info: dictionary that defines what should be shown in the view
        :return: None
        """
        # print(info)
        # print(json.dumps(info, indent=4))
        print("----------------------------------")

        if info.get("activated", False):
            print("activated")
            print(info["state"])
            print(f"is hidden {self.is_hidden}")
            if info["state"] == "menu":
                print("view menu")
                self.nav_wheel_vars = dict((k, v) for k, v in info.items() if k in self.nav_wheel_fields)
                print(f"equal: {self.nav_wheel_vars != self.last_state}")
                # todo these are equal and it is preventing the view from showing
                if self.nav_wheel_vars != self.last_state:
                    # print(f"not equal: {self.nav_wheel_vars != self.last_state}")
                    print("updating")
                    if self.is_hidden:
                        print("showing")
                        self.deiconify()  # Show the menu window
                    self.is_hidden = False
                    self.draw_circle_nav(**self.nav_wheel_vars)
                    self.last_state = self.nav_wheel_vars
                else:
                    # dont do anything since this the menu should not have changed
                    pass
        else:
            if not self.is_hidden:
                print("hiding")
                self.withdraw()
                self.is_hidden = True


def control_window(menu):
    # menu.deiconify()  # Show the menu window
    states = StateController()
    for state in states.iter_states():
        # print(state)
        menu.process_slice_of_time_view(state)



def start_thread():
    """
    main source of the program
    :return: None, runs for the duration of the program
    """
    menu = DisplayModule()
    control_thread = Thread(target=control_window, args=(menu,))
    control_thread.daemon = True
    control_thread.start()
    menu.root.mainloop()


if __name__ == "__main__":
    # run the program
    start_thread()
