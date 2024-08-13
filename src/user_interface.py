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
        self.color = "#5A7D8A"
        self.is_hidden = True
        self.last_state = {"selected_index": -1}
        # self.draw_circle_nav()
        self.did_draw_volume = False

        self.nav_wheel_vars = {}
        self.nav_wheel_fields = ["selected_index", "color", "menu_labels"]

    def draw_circle_nav(self, selected_index, menu_labels):
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
                c = "lightgray"
            else:
                c = self.color
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

    def draw_volume_icon(self, volume_percentage):
        self.canvas.delete("all")  # Clear the canvas
        r = min(self.width, self.height) // 4
        cx, cy = self.width // 2, self.width // 2
        self.canvas.create_arc(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            start=-90,
            extent=round(3.6*volume_percentage),
            outline=self.color,
            width=20,
            style=tk.ARC
        )
        volume_text = f"{volume_percentage}%"
        self.canvas.create_text(cx, cy, text=volume_text)

    def process_slice_of_time_view(self, info):
        """
        this function is called in a loop forever with info about the current state
        :param info: dictionary that defines what should be shown in the view
        :return: None
        """
        # print(info)
        # print(json.dumps(info, indent=4))
        print("----------------------------------")
        print(info)
        print(f"is hidden {self.is_hidden}")
        if info["activated"]:
            print("activated view")
            match info["state"]:
                case "menu":
                    print("view menu")
                    self.nav_wheel_fields = ["selected_index", "color", "menu_labels"]
                    self.nav_wheel_vars = {
                        "selected_index": info["selected_index"],
                    }
                    # print(f"equal: {info["selected_index"] != self.last_state["selected_index"]}")
                    # todo these are equal and it is preventing the view from showing
                    if "selected_index" in self.last_state and info["selected_index"] != self.last_state["selected_index"]:
                        # print(f"not equal: {self.nav_wheel_vars != self.last_state}")
                        print("updating")
                        print(f"[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[{info['selected_index']}")
                        self.draw_circle_nav(
                            selected_index=info["selected_index"],
                            menu_labels=info["menu_labels"]
                        )
                    else:
                        print("//////////////////////////////")
                        print(f'last: {self.last_state["selected_index"]} \n new: {info["selected_index"]}')
                        print("//////////////////////////////")
                    if "selected_index" not in self.last_state:
                        self.last_state["selected_index"] = info["selected_index"]
                case "volume":
                    self.draw_volume_icon(info.get("volume", 0))
                case "hidden":
                        pass
                case "play":
                        pass
                case _:
                    print("unknown state")


            if self.is_hidden:
                print("showing")
                self.deiconify()  # Show the menu window
                self.is_hidden = False
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
