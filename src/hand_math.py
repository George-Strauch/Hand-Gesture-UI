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
        self.get_radial_section()
        self.variables.update({"radial_section": self.radial_section})
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
            vector = np.subtract(tip, knuckel)
            # todo x or y here?
            vector[0] = -vector[0]
            norm = np.linalg.norm(vector)
            vector = vector / norm
            info.update(
                {
                    f"{finger}_tip": tip,
                    f"{finger}_direction": vector,
                    f"{finger}_norm": norm,
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

    def get_radial_section(self):
        direction = self.variables.get(
            "index_direction", np.array([0, 0, 0])
        )
        direction_2d = np.array([direction[0], direction[1]])
        angle = self.vector_angle(direction_2d)
        return angle
        # todo to determine which radial slice
        # const = 5
        # slice_angle = 2 * math.pi / const
        # x = int(angle // slice_angle)
        # print(f"enum {angle} // {slice_angle} = {x}")
