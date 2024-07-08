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
        self.actions = ActionHandler
        self.hand_oracle = HandMath()
        self.video = VideoHandler()
        self.current_hand = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_state = {}

    def get_state(self):
        self.logger.debug('get_state')
        while True:
            self.logger.debug("getting current state")
            frame_info = self.video.yield_frame()
            hands = frame_info['hands']
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
        pass
