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
        self.current_state.update(
            {"frames_since_last": self.frames_since_hand, "frames_with_hand": self.frames_with_hand, "menu_labels": self.radial_menu_labels,}
        )
        if self.current_hand is not None and self.frames_until_active == 0:
            state = "menu"
            index_norm_thresh = 0.5
            cross_norm = np.linalg.norm(np.cross(self.hand_oracle.variables["index_direction"], self.hand_oracle.variables["middle_direction"]))
            # print(cross_norm)
            if cross_norm > index_norm_thresh:
                state = "click"
                color = "blue"
            else:
                # color = f"#FFFF{hex(int(cross_norm * 255))[2:].zfill(2).upper()}"
                color = "#FFFF58"
            self.current_state.update(
                {
                    "selected_index": self.hand_oracle.get_radial_slice_index(self.radial_menu_labels),
                    "activated": True,
                    "state": state,
                    "color": color,
                    # "color": f"#FFFF{hex(int(0.5 * 255))[2:].zfill(2).upper()}"
                }
            )
        else:
            if self.show_bool():
                # print
                pass  # leave current state the same
            else:
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
                case "click":
                    if self.current_state["selected_index"] == 0:
                        self.actions.toggle_play()
                        self.frames_until_active = 40
                case _:
                    pass




if __name__ == '__main__':
    state_controller = StateController()
