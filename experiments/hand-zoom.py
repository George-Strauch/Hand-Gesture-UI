import cv2
import time
import mediapipe as mp
import numpy as np
import json
from matplotlib import pyplot as plt
import matplotlib.animation as animation



GRAB_MAD = .04


def max_min(max, min, value):
    return max(min, max(value, max))


class HandState:
    def __init__(self):
        self.n_states = 7
        self.state = {}
        self.delta_t = 0.000001
        self.history = []
        self.last_time = 0
        self.action = ""  # todo, update this in the updater, not post

    def update(self, single_hand):
        self.delta_t = time.time() - self.last_time
        self.last_time = time.time()
        self.state = {
            ** self.get_pointer_vector(single_hand),
            ** self.get_cluster_center(single_hand),
            ** self.get_frame_location_and_movement(single_hand),
            ** self.get_thumb(single_hand),
            "delta_t": self.delta_t,
            "action": self.action
        }
        # print(self.state)
        # print(json.dumps({k: list(v) if isinstance(v, np.ndarray) else v for k,v in self.state.items()}, indent=4))
        if len(self.history) == self.n_states:
            self.history = self.history[1:]
        self.history.append(self.state)
        # print(f"State updated in: {time.time() - self.last_time}")

    def get_pointer_vector(self, hand):
        wrist = np.array([hand[0].x, hand[0].y])
        tip = np.array([hand[8].x, hand[8].y])
        vector = np.subtract(tip, wrist)
        vector[0] = -vector[0]
        info = {
            "index": tip,
            "index_direction_vector": vector,
            "index_direction_vector_derivative": (vector - self.history[-1]["index_direction_vector"])/self.delta_t
            if len(self.history) > 0 else np.zeros(2),
        }
        info["jerk"] = np.linalg.norm((info["index_direction_vector_derivative"] - (self.history[-2]["index_direction_vector_derivative"] if len(self.history) > 2 else np.zeros(2))) / self.delta_t)
        return info

    def get_frame_location_and_movement(self, hand):
        n_frames = 3
        # tip = np.array([0.5-hand[8].x, 0.5-hand[8].y, 0.5-hand[8].z])
        tip = np.array([hand[8].x, 1-hand[8].y, hand[8].z])

        average_movement = np.zeros_like(tip)
        if len(self.history) > n_frames:
            index_history = [x["tip_with_middle_origin"] for x in self.history][-n_frames:]
            average_movement = np.average(index_history, axis=0)
        movement_vector = average_movement - tip
        return {
            "tip_with_middle_origin": tip,
            "movement_vector": movement_vector,
            "average_movement": average_movement
        }

    def get_cluster_center(self, hand):
        tips =  [8, 12, 16, 20]
        all_points = np.array([np.array([h.x, h.y, h.z])for h in hand])
        center = np.mean(all_points, axis=0)
        finger_tips = np.array([np.array([h.x, h.y, h.z]) for i, h in enumerate(hand) if i in tips])
        palm = np.array([np.array([h.x, h.y, h.z]) for i, h in enumerate(hand) if i in tips])
        finger_tips_center = np.mean(finger_tips, axis=0)
        return {
            "center_cluster": center,
            "graph_center": np.subtract(np.array([.5, .5, .5]), center),
            "finger_tips_center": finger_tips_center,
            "hand_length": np.subtract(np.array([hand[0].x, hand[0].y, hand[0].z]), finger_tips_center),
            "finger_tip_mad": np.mean(np.linalg.norm(finger_tips - finger_tips_center, axis=1))
        }

    def get_thumb(self, hand):
        thumb_points = np.array(
            [
                np.array([h.x, h.y, h.z]) for i, h in enumerate(hand)
                if i in [0, 2, 4]
            ]
        )

        # Your points are vectors A, B and C
        A = thumb_points[0]
        B = thumb_points[1]
        C = thumb_points[2]

        # Vectors AB and BC
        BA = np.subtract(A, B)
        BC = np.subtract(C, B)

        # normalize the vectors (to get the direction)
        BA_norm = np.linalg.norm(BA)
        BC_norm = np.linalg.norm(BC)

        # Calculate dot product
        dot_prod = np.dot(BA, BC)

        # Divide by the magnitudes of the vectors
        div = BA_norm * BC_norm

        # And finally, get the angle.
        # We need to ensure the value lies between -1 and 1 before applying arccos,
        # hence the use of numpy's clip function.
        angle = np.arccos(np.clip(dot_prod / div, -1.0, 1.0))

        return {
            "thumb_angle": angle,
        }





# https://www.youtube.com/watch?v=Ercd-Ip5PfQ
class Runner:
    def __init__(self):
        self.will_plot = 0
        self.cap = cv2.VideoCapture(0)
        self.hand_state = HandState()
        hands_model = mp.solutions.hands
        self.hands_model = hands_model.Hands(
            # static_image_mode=True,
            model_complexity=1,
            static_image_mode=False,
            max_num_hands=3,
            min_detection_confidence=0.1,
            min_tracking_confidence=0.5
        )
        self.draw = mp.solutions.drawing_utils
        self.hand_states = HandState()
        # self.interference = InterfaceInput()
        if self.will_plot:
            fig = plt.figure(figsize=(8, 8))
            ax = fig.add_subplot(111)
            # ax = fig.add_subplot(111, projection='3d')

            self.fig = fig
            self.ax = ax
            # self.ax.set_xlim3d(-1, 1)
            # self.ax.set_ylim3d(-1, 1)
            # self.ax.set_zlim3d(-1, 1)
            self.ani = animation.FuncAnimation(self.fig, self.animate_plot, frames=1, repeat=True)
            plt.show()
        else:
            self.ax = None
            self.ani = None
            self.fig = None
            while True:
                self.process_frame()

    @staticmethod
    def show():
        print("calling show")
        plt.show()

    def animate_plot(self, i):
        success, img = self.cap.read()
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        a = time.time()
        results = self.hands_model.process(img)
        # print("model time: ", time.time() - a)
        results = results.multi_hand_landmarks
        if results:
            # print("hand detected")
            hand = results[0].landmark
            self.hand_states.update(hand)
            # print("delta t: ", self.hand_states.delta_t,)
            self.draw.draw_landmarks(img, results[0])
            # draw the circle and color if grab
            x = int(self.hand_states.state["index"][0] * img.shape[1])
            y = int(self.hand_states.state["index"][1] * img.shape[0])
            # Define the radius and the color of the circle
            radius = 15
            color = (0, 0, 255)
            if self.hand_states.state["finger_tip_mad"] > GRAB_MAD:
                color = (0, 255, 0)
            # Draw the circle
            cv2.circle(img, (x, y), radius, color, -1)
            self.interference.do_action(self.hand_states, self.ax)
        else:
            # print("hand not detected")
            self.interference.do_nothing(self.ax)
        a = time.time()
        cv2.imshow("Image", img)
        # print("cv2 time: ", time.time() - a)
        cv2.waitKey(1)
        return True

    def process_frame(self):
        success, img = self.cap.read()
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        a = time.time()
        results = self.hands_model.process(img)
        # print("model time: ", time.time() - a)
        results = results.multi_hand_landmarks

        if results:
            # print("hand detected")
            hand = results[0].landmark
            self.hand_states.update(hand)
            # print("delta t: ", self.hand_states.delta_t,)
            self.draw.draw_landmarks(img, results[0])
            # draw the circle and color if grab
            x = int(self.hand_states.state["index"][0] * img.shape[1])
            y = int(self.hand_states.state["index"][1] * img.shape[0])
            # Define the radius and the color of the circle
            radius = 15
            color = (0, 0, 255)
            if self.hand_states.state["finger_tip_mad"] > GRAB_MAD:
                color = (0, 255, 0)
            # Draw the circle
            cv2.circle(img, (x, y), radius, color, -1)
        else:
            pass
        a = time.time()
        cv2.imshow("Image", img)
        # print("cv2 time: ", time.time() - a)
        cv2.waitKey(1)
        return True



if __name__ == '__main__':
    r = Runner()
    r.show()
