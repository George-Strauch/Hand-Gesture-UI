import cv2
import mediapipe as mp


class VideoHandler:
    def __init__(self, from_camera=True, recording=False, detect=True):
        """
        :param from_camera: video is captured from the camera or from file
        """
        self.video_file = "./hand.avi"
        self.recording = recording
        self.detect = detect
        self.cap = cv2.VideoCapture(0 if from_camera else self.video_file)
        if recording:
            self.video_out = cv2.VideoWriter(
                self.video_file,
                cv2.VideoWriter_fourcc(*'XVID'),
                20.0,
                (640, 480)
            )

        self.hand_model = mp.solutions.hands.hands_model.Hands(
            # static_image_mode=True,
            model_complexity=1,
            static_image_mode=False,
            max_num_hands=3,
            min_detection_confidence=0.1,
            min_tracking_confidence=0.5
        )

    def yield_frame(self):
        while True:
            success, img = self.cap.read()
            if not success:
                print("end")
                break
            if self.recording:
                self.video_out.write(img)
            else:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                hands = None
                if self.detect:
                    hands = self.get_hands_from_frame(img)

            yield {"raw_image": img, "hands": hands}
        yield None

    def iter_frames(self, func=None):
        try:
            for frame_data in self.yield_frame():
                img = frame_data["raw_image"]
                if func is not None:
                    new_img = func(img)
                    if new_img is not None:
                        img = new_img
                cv2.imshow('Video', img)
                cv2.waitKey(1)
        except (KeyboardInterrupt, Exception):
            pass
        if self.recording:
            self.video_out.release()

    def get_hands_from_frame(self, frame):
        results = self.hand_model.process(frame)
        results = results.multi_hand_landmarks
        if results:
            # todo determine proper hand to look at
            hand = results[0].landmark
        return results


if __name__ == '__main__':
    handler = VideoHandler(from_camera=0)
    handler.iter_frames()
    cv2.destroyAllWindows()
