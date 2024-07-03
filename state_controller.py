from hand_math import HandMath
from video_handler import VideoHandler
import mediapipe as mp


class StateController:
    """
    hand_oracle: processes all the math used to make decisions about the state
    hand_model: the detection model for a hand
    video: the video handler
    current state: current state that the view will define what is showing
    """
    def __init__(self):
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

    def get_state(self):
        while True:
            frame = self.video.yield_frame()
            hand = self.get_hands_from_frame(frame)
            if len(hand) > 0:
                hand = hand[0]
            else:
                yield None
            self.hand_oracle.process(hand)
            self.update_current_state()
            yield self.current_state

    def get_hands_from_frame(self, frame):
        results = self.hand_model.process(frame)
        results = results.multi_hand_landmarks
        if results:
            # todo determine proper hand
            hand = results[0].landmark
        return results

    def update_current_state(self):
        pass




