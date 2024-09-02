"""M3 - Labyrinth."""


class Localization:
    """Map class."""

    def __init__(self, robot, orig_map):
        """Construct map."""
        self.robot = robot

        self.current_position = 0, 0  # position on the "perceived localization map" until localization
        self.real_position = None  # real position at the real map after successful localization

        self.matrix = orig_map
        self.matrix_down = {}
        self.matrix_left = {}
        self.matrix_right = {}

        # transpose original map
        for key in self.matrix.keys():
            self.matrix_down[-key[0], -key[1]] = self.matrix[key]
            self.matrix_left[-key[1], key[0]] = self.matrix[key]
            self.matrix_right[key[1], -key[0]] = self.matrix[key]

        self.map_edge_positions = []  # for moving to (1, 1) after localization
        self.y_max = max(key[1] for key in self.matrix.keys())
        self.x_max = max(key[0] for key in self.matrix.keys())

        for x in range(1, self.x_max, 2):
            self.map_edge_positions.append((x, 1))
            self.map_edge_positions.append((x, self.y_max - 1))
        for y in range(1, self.y_max, 2):
            self.map_edge_positions.append((1, y))
            self.map_edge_positions.append((self.x_max - 1, y))
        self.map_edge_positions = tuple(self.map_edge_positions)

        self.localization_map = {(0, 0): " "}

        self.match_up = []  # all matches on upright original map
        self.match_down = []  # matches on upside down original map
        self.match_right = []
        self.match_left = []

    def update_position(self, yaw):
        """Update the position of the robot on the map."""
        if yaw == 0:
            self.current_position = self.current_position[0] + 2, self.current_position[1]
        elif yaw == 90:
            self.current_position = self.current_position[0], self.current_position[1] + 2
        elif yaw == 180:
            self.current_position = self.current_position[0] - 2, self.current_position[1]
        elif yaw == 270:
            self.current_position = self.current_position[0], self.current_position[1] - 2

        self.robot.scan_surroundings()
        if "X" in self.robot.surroundings.values() or self.robot.laser_sensed < 1.5:  # has not exited map
            self.localization_map[self.current_position] = " "

    def normalize_surroundings(self, surroundings, yaw):
        """Normalize surroundings based on perceived yaw."""
        result = []
        if yaw == 0:
            result = surroundings["behind"], surroundings["left"], surroundings["front"], surroundings["right"]
        elif yaw == 90:
            result = tuple(surroundings.values())
        elif yaw == 180:
            result = surroundings["front"], surroundings["right"], surroundings["behind"], surroundings["left"]
        elif yaw == 270:
            result = surroundings["right"], surroundings["behind"], surroundings["left"], surroundings["front"]
        return result

    def add_surroundings(self, surroundings, yaw):
        """Add surroundings to a position."""
        normalized_surroundings = self.normalize_surroundings(surroundings, yaw)
        pos = self.current_position
        self.localization_map[pos[0] - 1, pos[1]] = normalized_surroundings[0]  # left
        self.localization_map[pos[0], pos[1] + 1] = normalized_surroundings[1]  # front
        self.localization_map[pos[0] + 1, pos[1]] = normalized_surroundings[2]  # right
        self.localization_map[pos[0], pos[1] - 1] = normalized_surroundings[3]  # behind

    def attempt_localize(self):
        """Try to fit localization map onto original map."""
        self.match_up.clear()
        self.match_down.clear()
        self.match_right.clear()
        self.match_left.clear()
        # try to fit "localization map as a piece " onto the original map
        for key in self.matrix.keys():
            is_match = True
            for pos in self.localization_map.keys():
                to_be_checked = key[0] + pos[0], key[1] + pos[1]
                if to_be_checked not in self.matrix.keys() or self.localization_map[pos] != self.matrix[to_be_checked]:
                    is_match = False
                    break
            if is_match:
                self.match_up.append(key)

        for key in self.matrix_down.keys():
            is_match = True
            for pos in self.localization_map.keys():
                to_be_checked = key[0] + pos[0], key[1] + pos[1]
                if (to_be_checked not in self.matrix_down.keys()
                        or self.localization_map[pos] != self.matrix_down[to_be_checked]):
                    is_match = False
                    break
            if is_match:
                self.match_down.append(key)

        self.attempt_match_left_right()

        if len(self.match_up + self.match_down + self.match_left + self.match_right) == 1:
            self.localize_robot()

        print(f"up: {len(self.match_up)}\ndown: {len(self.match_down)}"
              f"\nright: {len(self.match_right)}\nleft: {len(self.match_left)}")
        print(self.get_map())

    def attempt_match_left_right(self):
        """Attempt to match localization map with original map."""
        for key in self.matrix_right.keys():
            is_match = True
            for pos in self.localization_map.keys():
                to_be_checked = key[0] + pos[0], key[1] + pos[1]
                if (to_be_checked not in self.matrix_right.keys()
                        or self.localization_map[pos] != self.matrix_right[to_be_checked]):
                    is_match = False
                    break
            if is_match:
                self.match_right.append(key)

        for key in self.matrix_left.keys():
            is_match = True
            for pos in self.localization_map.keys():
                to_be_checked = key[0] + pos[0], key[1] + pos[1]
                if (to_be_checked not in self.matrix_left.keys()
                        or self.localization_map[pos] != self.matrix_left[to_be_checked]):
                    is_match = False
                    break
            if is_match:
                self.match_left.append(key)

    def localize_robot(self):
        """Localize robot and adjust its yaw and position on original map."""
        pos = self.current_position
        if len(self.match_up) != 0:
            self.real_position = (self.match_up[0][0] + pos[0], self.match_up[0][1] + pos[1])
        elif len(self.match_down) != 0:
            self.robot.yaw_adjustment += 180
            self.real_position = (-(self.match_down[0][0] + pos[0]), -(self.match_down[0][1] + pos[1]))
        elif len(self.match_left) != 0:
            self.robot.yaw_adjustment += 270
            self.real_position = (self.match_left[0][1] + pos[1], -(self.match_left[0][0] + pos[0]))
        elif len(self.match_right) != 0:
            self.robot.yaw_adjustment += 90
            self.real_position = (-(self.match_right[0][1] + pos[1]), self.match_right[0][0] + pos[0])

        self.current_position = self.real_position
        self.robot.state = "MOVE TO START"
        self.robot.is_localized = True

    def get_map(self):
        """Get localization map as string."""
        result = ""
        for y in range(10, -10, -1):
            result += "\n" if result != "" else ""
            for x in range(-10, 10):
                if (x, y) in self.localization_map.keys():
                    result += self.localization_map[x, y]
                else:
                    result += "o"
        return result
