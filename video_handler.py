import cv2


class VideoHandler:
    def __init__(self, from_camera=True):
        """
        :param from_camera: video is captured from the camera or from file
        """
        self.video_file = "./hand.avi"
        self.recording = from_camera
        self.cap = cv2.VideoCapture(0 if from_camera else self.video_file)
        self.video_out = cv2.VideoWriter(
            self.video_file,
            cv2.VideoWriter_fourcc(*'XVID'),
            20.0,
            (640, 480)
        ) if from_camera else None

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
            yield img
        yield None

    def iter_frames(self, func=None):
        try:
            for img in self.yield_frame():
                if func is not None:
                    new_img = func(img)
                    if new_img is not None:
                        img = new_img
                cv2.imshow('Video', img)
                cv2.waitKey(1)
        except (KeyboardInterrupt, Exception):
            pass
        if self.video_out:
            self.video_out.release()


if __name__ == '__main__':
    handler = VideoHandler(from_camera=0)
    handler.iter_frames()
    cv2.destroyAllWindows()
