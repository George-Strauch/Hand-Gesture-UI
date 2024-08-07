import math
import traceback
import cv2
import time
import mediapipe as mp
import numpy as np
import matplotlib.pyplot as plt

GRAB_MAD = 0.0





class HandState:
    def __init__(self):
        self.nth_state = 0
        self.n_states = 20
        self.state = {}
        self.state_serializable = {}
        self.delta_t = 0.000001
        self.history = []
        self.last_time = 0
        self.events = []
        self.radial_section = 0
        self.n_slices = 5
        self.click = False

    def update(self, single_hand):
        # print("update ", not bool(single_hand))
        try:
            if not single_hand:
                self.events.append("no_hand")
                self.delta_t = 1
                self.last_time = time.time()
            else:
                self.events.append("hand_found")
                self.delta_t = time.time() - self.last_time
                self.last_time = time.time()
                self.state = {
                    ** self.get_pointer_vector(single_hand),
                    ** self.get_cluster_center(single_hand),
                    ** self.get_frame_location_and_movement(single_hand),
                }
            self.nth_state += 1
            self.set_is_click()
        except Exception:
            print(traceback.format_exc())
            print("Exception occurred")
        self.get_radial_section()
        self.state.update({"events": self.events, "radial_section": self.radial_section, "click": self.click})
        for k, v in self.state.items():
            if isinstance(v, np.ndarray):
                self.state_serializable[k] = v.tolist()
            else:
                self.state_serializable[k] = v
        if len(self.history) == self.n_states:
            self.history = self.history[1:]
        self.history.append(self.state)
        # print(f"State updated in: {time.time() - self.last_time}")

    @staticmethod
    def vector_angle(direction):
        if np.linalg.norm(direction) < 0.5:
            return 0.0
        normalized_vector = direction / np.linalg.norm(direction)
        angle = np.arctan2(normalized_vector[1], normalized_vector[0])
        if angle < 0:
            angle += 2 * np.pi
        return angle

    def set_is_click(self):
        cool_off = 20
        self.click = False
        if not all(x in self.state for x in ["index_direction_vector_derivative"]):
            return
        if "no_hand" in self.events[-cool_off:]:
            return
        if any(["MOVED" in x for x in self.history[-cool_off:]]):
            return
        click_history = [x["click"] for x in self.history[-cool_off:]]
        z_movements = [self.state["index_direction_vector_derivative"][2]] + [x["index_direction_vector_derivative"][2] for x in self.history[-4:]]
        # todo condition should be if index point moves more than palm center
        click_condition = bool(np.mean(z_movements) > 0.6)
        if not any(click_history):
            if click_condition:
                print("CLICK")
                print(self.state["index_direction_vector_derivative"][2])
                self.click = True
            else:
                pass
        else:
            print("cool_down")

    def get_pointer_vector(self, hand):
        wrist = np.array([hand[0].x, hand[0].y, hand[0].z])
        tip = np.array([hand[8].x, hand[8].y, hand[8].z])
        vector = np.subtract(tip, wrist)
        vector[0] = -vector[0]
        norm = np.linalg.norm(vector)
        vector = vector / norm
        info = {
            "index": tip,
            "index_direction_vector": vector,
        }
        if len(self.history) > 0 and "index_direction_vector" in self.history[-1]:
            info["index_direction_vector_derivative"] = (vector - self.history[-1]["index_direction_vector"])/self.delta_t
        else:
            info["index_direction_vector_derivative"] = np.zeros(3)
        return info

    def get_frame_location_and_movement(self, hand):
        n_frames = 3
        tip = np.array([hand[8].x, 1-hand[8].y, hand[8].z])

        average_movement = np.zeros_like(tip)
        if len(self.history) > n_frames and all(["tip_with_middle_origin" in x for x in self.history[-n_frames:]]):
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

        if all(["finger_tips" in x for x in self.history[-2:]]) and len(self.history) > 2:
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

    def get_radial_section(self):
        direction = self.state.get("index_direction_vector", np.array([0, 0, 0]))
        # print("direction", direction)
        direction_2d = np.array([direction[0], direction[1]])
        # print("direction_2d", direction_2d)
        angle = self.vector_angle(direction_2d)
        # print("angle ", angle)
        # print()
        CONST = 5
        slice_angle = 2*math.pi / CONST
        x = int(angle // slice_angle)
        # print(f"enum {angle} // {slice_angle} = {x}")
        if x != self.radial_section:
            self.events.append("MOVED")
        self.radial_section = x


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
