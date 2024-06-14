import math
import traceback
import cv2
import time
import mediapipe as mp
import numpy as np
import matplotlib.pyplot as plt

GRAB_MAD = 0.0


def max_min(max, min, value):
    return max(min, max(value, max))



def vector_angle(direction):
    normalized_vector = direction / np.linalg.norm(direction)
    angle = np.arctan2(normalized_vector[1], normalized_vector[0])
    if angle < 0:
        angle += 2 * np.pi
    # norm = np.linalg.norm(direction)
    # direction_norm = direction / norm
    # unit_vector = np.array([0, 1])
    # angle = np.arccos(np.dot(direction_norm, unit_vector))
    return angle


class HandState:
    def __init__(self):
        self.nth_state = 0
        self.n_states = 7
        self.state = {}
        self.state_serializable = {}
        self.delta_t = 0.000001
        self.history = []
        self.last_time = 0
        self.action = ""
        self.radial_section = 0
        self.n_slices = 5

    def update(self, single_hand):
        try:
            if not single_hand:
                self.action = "no_hand"
                self.delta_t = 1
                self.last_time = time.time()
            else:
                self.action = "hand_found"
                self.delta_t = time.time() - self.last_time
                self.last_time = time.time()
                self.state = {
                    ** self.get_pointer_vector(single_hand),
                    ** self.get_cluster_center(single_hand),
                    ** self.get_frame_location_and_movement(single_hand),
                    ** self.get_thumb(single_hand),
                }
            self.nth_state += 1

            # print(self.state["finger_tips_delta_norms"] > 2 * self.state["palm_delta_norms"])
            # print(type(self.state["finger_tips_delta_norms"] > 2 * self.state["palm_delta_norms"]))
            # print(type(True))

            if self.action == "hand_found":
                if "click" not in[x["action"] for x in self.history[-20:]]:
                    # todo verify click
                    self.state["click"] = bool(self.state["finger_tips_delta_norms"] < 1.2 * self.state["palm_delta_norms"])
                self.get_radial_section()
        except Exception:
            print(traceback.format_exc())
            print("Exception occurred")

        self.state["click"] = self.state.get("click", False)
        self.state.update({"action": self.action, "radial_section": self.radial_section})
        for k, v in self.state.items():
            if isinstance(v, np.ndarray):
                self.state_serializable[k] = v.tolist()
            else:
                self.state_serializable[k] = v
        if len(self.history) == self.n_states:
            self.history = self.history[1:]
        self.history.append(self.state)
        # print(f"State updated in: {time.time() - self.last_time}")


    def get_pointer_vector(self, hand):
        wrist = np.array([hand[0].x, hand[0].y, hand[0].z])
        tip = np.array([hand[8].x, hand[8].y, hand[8].z])
        vector = np.subtract(tip, wrist)
        vector[0] = -vector[0]
        norm = np.linalg.norm(vector)
        vector = vector / norm
        vector = np.array([vector[0], vector[1]])
        info = {
            "index": tip,
            "index_direction_vector": vector,

        }
        if len(self.history) > 0 and not self.history[-1]["action"] == "no_hand":
            info["index_direction_vector_derivative"] = (vector - self.history[-1]["index_direction_vector"])/self.delta_t
        else:
            info["index_direction_vector_derivative"] = np.zeros(2)

        # info["jerk"] = np.linalg.norm((info["index_direction_vector_derivative"] - (self.history[-2]["index_direction_vector_derivative"] if len(self.history) > 2 else np.zeros(2))) / self.delta_t)
        return info

    def get_frame_location_and_movement(self, hand):
        n_frames = 3
        # tip = np.array([0.5-hand[8].x, 0.5-hand[8].y, 0.5-hand[8].z])
        tip = np.array([hand[8].x, 1-hand[8].y, hand[8].z])

        average_movement = np.zeros_like(tip)
        if len(self.history) > n_frames and not "no_hand" not in [x["action"] for x in self.history[-n_frames:]]:
            index_history = [x["tip_with_middle_origin"] for x in self.history[-n_frames:]]
            average_movement = np.average(index_history, axis=0)
        movement_vector = average_movement - tip
        return {
            "tip_with_middle_origin": tip,
            "movement_vector": movement_vector,
            "average_movement": average_movement
        }

    def get_cluster_center(self, hand):
        tips = [8, 12, 16, 20]

        all_points = np.array([np.array([h.x, h.y, h.z])for h in hand])
        center = np.mean(all_points, axis=0)

        finger_tips = np.array([np.array([h.x, h.y, h.z]) for i, h in enumerate(hand) if i in tips])
        finger_tips_center = np.mean(finger_tips, axis=0)

        palm = np.array([np.array([h.x, h.y, h.z]) for i, h in enumerate(hand) if i not in tips])
        palm_center = np.mean(palm, axis=0)

        if self.nth_state > 1 and "no_hand" not in [x["action"] for x in self.history[-2:]]:
            finger_tips_delta = np.subtract(finger_tips, self.history[-1]["finger_tips"])
            palm_delta = np.subtract(palm, self.history[-1]["palm"])
            palm_delta_norms = np.mean(np.linalg.norm(palm_delta, axis=1))
            finger_tips_delta_norms = np.mean(np.linalg.norm(finger_tips_delta, axis=1))
        else:
            finger_tips_delta = np.array([0, 0, 0])
            palm_delta = np.array([0, 0, 0])
            finger_tips_delta_norms = 0
            palm_delta_norms = 0

        return_vars = {
            "center_cluster": center,
            "graph_center": np.subtract(np.array([.5, .5, .5]), center),
            "finger_tips_center": finger_tips_center,
            "hand_length": np.subtract(np.array([hand[0].x, hand[0].y, hand[0].z]), finger_tips_center),
            "finger_tip_mad": np.mean(np.linalg.norm(finger_tips - finger_tips_center, axis=1)),
            "plam_mad": np.mean(np.linalg.norm(palm - palm_center, axis=1)),
            "finger_tips_delta": finger_tips_delta,
            "palm_delta": palm_delta,
            "palm_delta_norms": palm_delta_norms,
            "finger_tips_delta_norms": finger_tips_delta_norms,
            "finger_tips": finger_tips,
            "palm": palm,
            "palm_center": palm_center,
        }
        return return_vars


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

    def get_radial_section(self):
        # todo set to change from current by mod operator of the previous section
        # n_weights = 2
        # weights = [2 ** x for x in range(n_weights)]
        # weights = list(reversed([a / sum(weights) for a in weights]))
        # if len(self.history) < n_weights+3:
        #     return 0
        # direction = np.sum(
        #     [a["index_direction_vector"] * b for a, b in zip(self.history[-len(weights):], weights)],
        #     axis=0
        # )
        direction = self.state["index_direction_vector"]
        angle = vector_angle(direction)
        CONST = 5
        slice_angle = 2*math.pi / CONST
        x = int(angle // slice_angle)
        print(f"enum {angle} // {slice_angle} = {x}")
        self.radial_section = x
        # self.state["radial_section"] = x

    # def get_radial_section(self):
    #     n_frame_wait_to_move = 3
    #     threshold = .5
    #     # over_thresh = np.linalg.norm(self.state["index_direction_vector"]) > threshold
    #     over_thresh = True
    #     print(np.linalg.norm(self.state["index_direction_vector"]))
    #     direction = ""
    #     direction_vector = self.state["index_direction_vector"] / np.linalg.norm(self.state["index_direction_vector"])
    #     if over_thresh:
    #         print("--1: ", self.state["index"][1], self.state["palm_center"][1])
    #         if self.state["index"][1] > self.state["palm_center"][1]:
    #             if direction_vector[0] > 0:
    #                 direction = "-"
    #             else:
    #                 direction = "+"
    #         else:
    #             if direction_vector[0] > 0:
    #                 direction = "+"
    #             else:
    #                 direction = "-"
    #     if direction:
    #         hist = [x["action"] for x in self.history[-n_frame_wait_to_move:]]
    #         if "+" in hist or "-" in hist:
    #             # print("----------", hist)
    #             self.action = ""
    #         else:
    #             self.action = direction
    #             if direction == "+":
    #                 self.radial_section = (self.radial_section+1) % self.n_slices
    #             else:
    #                 self.radial_section = (self.radial_section-1) % self.n_slices
    #     self.state["radial_section"] = self.radial_section

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
        self.ax = None
        self.ani = None
        self.fig = None


    @staticmethod
    def show():
        print("calling show")
        plt.show()

    def process_frame(self, i):
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
            # x = int(self.hand_states.state["index"][0] * img.shape[1])
            # y = int(self.hand_states.state["index"][1] * img.shape[0])
            # Define the radius and the color of the circle
            radius = 15
            color = (0, 0, 255)
            # if self.hand_states.state["finger_tip_mad"] > GRAB_MAD:
            #     color = (0, 255, 0)
            # Draw the circle
            # cv2.circle(img, (x, y), radius, color, -1)
        else:
            self.hand_states.update(None)

        a = time.time()
        # cv2.imshow("Image", img)
        # print("cv2 time: ", time.time() - a)
        # cv2.waitKey(1)
        return self.hand_states.state_serializable
