import numpy as np
import time
import traceback
import math


class HandMath:
    """
    todo update
    move all logical states to state controller
    """
    def __init__(self):
        self.nth_state = 0
        self.n_states = 20
        self.variables = {}
        self.vars_serializable = {}
        self.delta_t = 1
        self.history = []
        self.last_time = 0
        self.n_slices = 5

    def process(self, single_hand):
        # print("update ", not bool(single_hand))
        try:
            if not single_hand:
                self.delta_t = 1
                self.last_time = time.time()
            else:
                self.delta_t = time.time() - self.last_time
                self.last_time = time.time()
                self.variables = {
                    **self.get_finger_directions(single_hand),
                }
            self.nth_state += 1
        except Exception:
            print(traceback.format_exc())
            print("Exception occurred")
            assert False
        angle = self.get_radial_direction()
        self.variables.update({"radial_angle": angle})
        for k, v in self.variables.items():
            if isinstance(v, np.ndarray):
                self.vars_serializable[k] = v.tolist()
            else:
                self.vars_serializable[k] = v
        if len(self.history) == self.n_states:
            self.history = self.history[1:]
        self.history.append(self.variables)

    @staticmethod
    def get_finger_directions(hand):
        tips = {
            "thumb": [1, 4],
            "index": [5, 8],
            "middle": [9, 12],
            "ring": [13, 16],
            "pinky": [17, 20],
        }
        info = {}
        for finger, points in tips.items():
            knuckel = np.array([hand[points[0]].x, hand[points[0]].y, hand[points[0]].z])
            tip = np.array([hand[points[1]].x, hand[points[1]].y, hand[points[1]].z])
            vector = np.subtract(knuckel, tip)
            norm = np.linalg.norm(vector)
            norm_2d = (vector[0] ** 2 + vector[1] ** 2) ** 0.5
            vector = vector / norm
            info.update(
                {
                    f"{finger}_tip": tip,
                    f"{finger}_direction": vector,
                    f"{finger}_norm": norm,
                    f"{finger}_norm2d": norm_2d,

                }
            )
        return info

    @staticmethod
    def vector_angle(direction):
        if np.linalg.norm(direction) < 0.5:
            return 0.0
        normalized_vector = direction / np.linalg.norm(direction)
        angle = np.arctan2(normalized_vector[1], normalized_vector[0])
        if angle < 0:
            angle += 2 * np.pi
        return angle

    def get_radial_direction(self):
        direction = self.variables.get(
            "index_direction", np.array([0, 0, 0])
        )
        direction_2d = np.array([direction[0], direction[1]])
        print(self.variables.get("index_norm"))
        print(self.variables.get("index_norm2d"))
        print(self.variables.get("index_direction", [0])[2])
        # print(self.variables["index_norm2d"] / self.variables["index_norm"])

        print("------------------------")

        angle = self.vector_angle(direction_2d)
        return angle


    def get_radial_slice_index(self, labels):
        if "radial_angle" in self.variables:
            # print(self.variables["radial_angle"])
            const = len(labels)
            slice_angle = 2 * math.pi / const
            angle = self.variables["radial_angle"]
            return int(angle // slice_angle)
        else:
            print("radial_angle not found")
            return 0
