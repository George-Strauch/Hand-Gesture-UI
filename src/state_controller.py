import math

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
        self.radial_menu_labels = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        self.actions = ActionHandler
        self.hand_oracle = HandMath()
        self.video = VideoHandler()
        self.current_hand = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_state = {}

    def iter_states(self):
        self.logger.debug('get_state')
        for frame_data in self.video.iter_frames():
            self.logger.debug("processed a frame from the video handler. processing hands")
            hands = frame_data['hands']
            if len(hands) > 0:
                self.logger.info("hand found")
                self.current_hand = hands[0]
                self.hand_oracle.process(self.current_hand)
            else:
                self.current_hand = None
            self.update_current_state()
            yield self.current_state

    def update_current_state(self):
        """
        process logic based on current state
        if not hand, pass
        if current state.action is asleep, set it to nav wheel
        """
        if self.current_hand is not None:
            self.current_state = {
                "selected_idx": self.hand_oracle.get_radial_slice_index(self.radial_menu_labels),
                "show": True,
                "show_menu": True
            }
        else:
            self.current_state = {
                "show": False,
            }


if __name__ == '__main__':
    state_controller = StateController()
