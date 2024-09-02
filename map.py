"""M3 - Labyrinth."""


class Map:
    """Map class."""

    def __init__(self, robot):
        """Construct map."""
        self.robot = robot

        self.initial_position = 1, 1
        self.current_position = 1, 1
        self.prev_position = 1, 1

        self.matrix = {}
        self.localization_map = {}

        self.x_min = 0
        self.x_max = 2
        self.y_min = 0
        self.y_max = 2

        for y in range(0, 3):
            for x in range(0, 3):
                self.matrix[x, y] = "?"
                self.localization_map[x, y] = "?"

    def set_position(self, surroundings, yaw):
        """Set position on the map."""
        normalized_surroundings = self.normalize_surroundings(surroundings, yaw)
        if normalized_surroundings[0] == "X" and normalized_surroundings[3] == "X":
            self.current_position = 1, 1
        else:
            self.current_position = 1, 1
        self.initial_position = self.current_position

    def extend_map(self):
        """Add new rows and columns."""
        pos = self.current_position
        if pos[0] < self.x_min:
            self.x_min -= 2
            for y in range(self.y_min, self.y_max + 1):
                for x in range(self.x_min, self.x_min + 2):
                    self.matrix[x, y] = "?"
        elif pos[0] > self.x_max:
            self.x_max += 2
            for y in range(self.y_min, self.y_max + 1):
                for x in range(self.x_max - 2, self.x_max + 1):
                    self.matrix[x, y] = "?"
        elif pos[1] < self.y_min:
            self.y_min -= 2
            for y in range(self.y_min, self.y_min + 2):
                for x in range(self.x_min, self.x_max + 1):
                    self.matrix[x, y] = "?"
        else:
            self.extend_map_complexity_reduction()

    def extend_map_complexity_reduction(self):
        """Complexity reduction."""
        self.y_max += 2
        for y in range(self.y_max - 2, self.y_max + 1):
            for x in range(self.x_min, self.x_max + 1):
                self.matrix[x, y] = "?"

    def update_position(self, yaw):
        """Update the position of the robot on the map."""
        self.prev_position = self.current_position
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
            pos = self.current_position
            if pos[0] < self.x_min or pos[0] > self.x_max or pos[1] < self.y_min or pos[1] > self.y_max:
                self.extend_map()

        if self.current_position in self.matrix.keys():
            self.matrix[self.current_position] = "R"
        if self.prev_position in self.matrix.keys():
            self.matrix[self.prev_position] = " "

    def normalize_surroundings(self, surroundings, yaw):
        """Normalize surroundings based on yaw. Facing up (yaw 90): [left, front, right, behind]."""
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
        self.matrix[pos] = "R"
        self.matrix[pos[0] - 1, pos[1]] = normalized_surroundings[0]  # left
        self.matrix[pos[0], pos[1] + 1] = normalized_surroundings[1]  # front
        self.matrix[pos[0] + 1, pos[1]] = normalized_surroundings[2]  # right
        self.matrix[pos[0], pos[1] - 1] = normalized_surroundings[3]  # behind

    def has_explored_all_squares(self):
        """Check whether the robot has explored all accessible squares."""
        for x in range(self.x_min + 1, self.x_max, 2):
            for y in range(self.y_min + 1, self.y_max, 2):

                if self.matrix[x, y] == "?":
                    if (self.matrix[x + 1, y] == " " or self.matrix[x - 1, y] == " "
                            or self.matrix[x, y + 1] == " " or self.matrix[x, y - 1] == " "):
                        return False
        return True

    def back_in_initial_pos(self):
        """Check whether the robot is back at the initial position."""
        pos = self.current_position
        try:
            if pos == self.initial_position and (
                self.matrix[pos[0] + 2, pos[1]] == " "
                or self.matrix[pos[0] - 2, pos[1]] == " "
                or self.matrix[pos[0], pos[1] + 2] == " "
                or self.matrix[pos[0], pos[1] - 2] == " "
            ):
                return True
            else:
                return False
        except KeyError:
            if pos == self.initial_position and (
                self.matrix[pos[0], pos[1] + 2] == " "
                or self.matrix[pos[0], pos[1] - 2] == " "
                or self.matrix[pos[0] + 2, pos[1]] == " "
                or self.matrix[pos[0] - 2, pos[1]] == " "
            ):
                return True
            else:
                return False

    def has_unexplored_neighbours(self):
        """Check whether the position has more than 1 neighbouring squares that are unexplored."""
        pos = self.current_position
        try:
            if ((self.matrix[pos[0] + 1, pos[1]] != "X" and self.matrix[pos[0] + 2, pos[1]] == "?")
                    or (self.matrix[pos[0] - 1, pos[1]] != "X" and self.matrix[pos[0] - 2, pos[1]] == "?")
                    or (self.matrix[pos[0], pos[1] + 1] != "X" and self.matrix[pos[0], pos[1] + 2] == "?")
                    or (self.matrix[pos[0], pos[1] - 1] != "X" and self.matrix[pos[0], pos[1] - 2] == "?")):
                return True
            return False
        except KeyError:  # right before labyrinth exit
            return False

    def get_map(self):
        """Get map as string."""
        print(f"x_min: {self.x_min}   x_max: {self.x_max}")
        print(f"y_min: {self.y_min}   y_max: {self.y_max}")
        print(f"pos:  {self.current_position}")
        result = ""
        for y in range(self.y_max, self.y_min - 1, -1):
            result += "\n" if result != "" else ""
            for x in range(self.x_min, self.x_max + 1):
                result += self.matrix[x, y]
        return result

    def normalize_map(self):
        """Get map without negative coordinates."""
        if self.x_min < 0:
            x_adjustment = 0 - self.x_min
            old_dict = self.matrix.copy()
            self.matrix.clear()
            self.x_min += x_adjustment
            self.x_max += x_adjustment
            for key in old_dict.keys():
                self.matrix[key[0] + x_adjustment, key[1]] = old_dict[key]
