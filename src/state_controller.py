import math

import numpy as np

from hand_math import HandMath
from video_handler import VideoHandler
from action_handler import ActionHandler
import logging


class StateController:
    """
    hand_oracle: processes all the math used to make decisions about the state
    hand_model: the detection model for a hand
    video: the video handler
    current state: current state that the view will define what is showing
    """
    def __init__(self):
        self.radial_menu_labels = ["Play/Pause", "Volume", "Mouse"]
        self.actions = ActionHandler()
        self.hand_oracle = HandMath()
        self.video = VideoHandler()
        self.current_hand = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_state = {"activated": False}
        self.n_frames_buffer = 5
        self.frames_since_hand = 0
        self.frames_with_hand = 0
        self.frames_until_active = 0
        # self.show_bool = lambda: self.frames_since_hand < self.n_frames_buffer

    def show_bool(self):
        print(self.frames_since_hand, self.frames_with_hand, self.frames_until_active)
        x = self.frames_since_hand < self.n_frames_buffer and self.frames_until_active == 0
        # print(x)
        return x

    def iter_states(self):
        self.logger.debug('get_state')
        for frame_data in self.video.iter_frames():
            self.logger.debug("processed a frame from the video handler. processing hands")
            hands = frame_data['hands']
            if len(hands) > 0:
                self.frames_since_hand = 0
                self.frames_with_hand += 1
                self.logger.info("hand found")
                self.current_hand = hands[0]
                self.hand_oracle.process(self.current_hand)
            else:
                self.frames_since_hand += 1
                self.frames_with_hand = 0
                self.current_hand = None
            self.frames_until_active = max(self.frames_until_active-1, 0)
            self.update_current_state()
            self.perform_actions()
            # print(self.frames_since_hand)
            yield self.current_state

    def update_current_state(self):
        """
        Determines current state of the view
        """
        defaults = {
            "frames_since_last": self.frames_since_hand,
            "frames_with_hand": self.frames_with_hand,
            "menu_labels": self.radial_menu_labels
        }
        self.current_state.update(defaults)
        state = self.current_state.get("state", "menu")

        if self.frames_until_active == 0:
            # if there is a hand and not in cooldown
            color = "#FFFF58"
            middle_pointer_cross_prod_thresh = 0.5

            match state:
                case "menu":
                    if self.current_hand is not None:
                        print(f"NO CLICK {self.hand_oracle.variables["middle_pointer_cross"]} !> {middle_pointer_cross_prod_thresh}")
                        if self.hand_oracle.variables["middle_pointer_cross"] > middle_pointer_cross_prod_thresh:
                            print(f"menu selection here in update state because:")
                            print(f"{self.hand_oracle.variables["middle_pointer_cross"]} > {middle_pointer_cross_prod_thresh}")
                            state = "select_menu_item"
                case "volume":
                    pass
                case "play":
                    pass
                case "select_menu_item":
                    color = "blue"
                case _:
                    print(f"DO NOT KNOW WHAT TO DO WITH STATE: {state}")
                    assert False

            self.current_state.update(
                {
                    "selected_index": self.hand_oracle.get_radial_slice_index(self.radial_menu_labels),
                    "activated": True,
                    "state": state,
                    "color": color,
                }
            )
        else:
            if self.show_bool():
                if self.frames_since_hand < self.n_frames_buffer:
                    state = "menu"
                self.current_state.update(
                    {
                        "activated": True,
                        "state": state,
                    }
                )
            else:
                print("de-activating")
                self.current_state.update(
                    {
                        "activated": False,
                    }
                )


    def perform_actions(self):
        # print(self.current_state)
        # print(self.frames_until_active)
        if self.current_state["activated"]:
            match self.current_state["state"]:
                case "select_menu_item":
                    print("SELECTING MENU ITEM")
                    # selecting an item from the ment
                    if self.current_state["selected_index"] == 0:
                        self.actions.toggle_play()
                        self.frames_until_active = 40
                        self.current_state["state"] = "menu"

                    elif self.current_state["selected_index"] == 1:
                        self.current_state["state"] = "volume"
                case "volume":
                    vol = round(self.hand_oracle.variables["pointer_thumb_cross"]*100)
                    print("setting volume to ", vol)
                    success = self.actions.set_volume(vol)
                    # print(success)
                case _:
                    pass




if __name__ == '__main__':
    state_controller = StateController()
