from hand_math import HandMath
from video_handler import VideoHandler
from view_model import ViewModel
from action_handler import ActionHandler
import mediapipe as mp


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
        self.hand_model = mp.solutions.hands.hands_model.Hands(
            # static_image_mode=True,
            model_complexity=1,
            static_image_mode=False,
            max_num_hands=3,
            min_detection_confidence=0.1,
            min_tracking_confidence=0.5
        )
        self.view_model = ViewModel()

        self.current_hand = None

    def get_state(self):
        while True:
            frame = self.video.yield_frame()
            hands = self.get_hands_from_frame(frame)
            if len(hands) > 0:
                self.current_hand = hands[0]
                self.hand_oracle.process(self.current_hand)
            else:
                self.current_hand = None
            self.update_current_state()

            yield self.view_model.get_view()

    def get_hands_from_frame(self, frame):
        results = self.hand_model.process(frame)
        results = results.multi_hand_landmarks
        if results:
            # todo determine proper hand to look at
            hand = results[0].landmark
        return results

    def update_current_state(self):
        """
        process logic based on current state
        if not hand, pass
        if current state.action is asleep, set it to nav wheel

        """
        if self.current_hand is None:
            pass

        if len(self.history) == self.n_states:
            self.history = self.history[1:]
        self.history.append(self.variables)





