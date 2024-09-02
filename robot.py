"""M3 - Labyrinth."""
import math
import random

import PiBot
import map
import localization_map


WALL_CALIBRATION_DIST = 0.0675
IR_THRESHOLD = 550  # lower value -> no wall


class Robot:
    """Robot class."""

    def __init__(self):
        """Class constructor."""
        self.robot = PiBot.PiBot()
        self.shutdown = False

        # laser stuff
        self.laser_sensed = 0
        self.ir_right = 0
        self.ir_left = 0
        self.ir_behind = 0

        # encoders
        self.sensed_left_encoder = 0
        self.sensed_right_encoder = 0
        self.moving_start_left_encoder = 0
        self.moving_start_right_encoder = 0

        # wheels
        self.right_wheel_speed = 0
        self.left_wheel_speed = 0
        self.moving_state_begin_encoder = 0

        # states
        self.state = "INITIALIZE"
        self.mapping_state = "REGULAR"

        # mapping
        self.map = map.Map(self)
        self.follow_wall = "LEFT"
        self.island_mapping_initial_yaw = 0
        self.island_mapping_initial_pos = 0, 0

        # localization
        self.localize = False
        self.timeout = 500
        self.loc_map = None
        self.is_localized = False
        self.reached_edge = False
        self.moving_to_start_pos_history = []

        # turning
        self.degrees_turned_total = 0
        self.destination_degrees = 0
        self.yaw = 0
        self.yaw_adjustment = 90

        # scanning turn results
        self.surroundings = {"left": "X", "front": "X", "right": "X", "behind": "X"}

        # distances
        self.distance_moved = 0

    def set_robot(self, robot: PiBot.PiBot()) -> None:
        """Set Robot reference."""
        self.robot = robot

    def calculate_wheel_moved_distance(self):
        """Calculate wheels moved distance."""
        delta_right = self.sensed_right_encoder - self.moving_start_right_encoder
        wheel_moved_dist_r = self.robot.WHEEL_DIAMETER * math.pi * (delta_right / 360)
        delta_left = self.sensed_left_encoder - self.moving_start_left_encoder
        wheel_moved_dist_l = self.robot.WHEEL_DIAMETER * math.pi * (delta_left / 360)
        return (wheel_moved_dist_l + wheel_moved_dist_r) / 2

    def scan_surroundings(self):
        """Scan surroundings."""
        self.surroundings["left"] = " " if self.ir_left < IR_THRESHOLD else "X"
        self.surroundings["front"] = " " if self.laser_sensed > 0.25 else "X"
        self.surroundings["right"] = " " if self.ir_right < IR_THRESHOLD else "X"
        self.surroundings["behind"] = " " if self.ir_behind < IR_THRESHOLD else "X"

    def initialize(self):
        """Initialize total degrees turned variable."""
        if self.degrees_turned_total != 0:
            self.destination_degrees += round(self.degrees_turned_total)
            self.scan_surroundings()
            self.map.set_position(self.surroundings, self.yaw)
            self.map.add_surroundings(self.surroundings, self.yaw)
            self.right_wheel_speed = 0
            self.state = "FIND DIRECTION"
        else:
            self.right_wheel_speed = 8

    def calculate_yaw(self):
        """Calculate yaw."""
        print(f"desti: {self.destination_degrees}")
        print(f"total: {self.degrees_turned_total}")
        deg_turned = int(round(self.degrees_turned_total, -1)) + self.yaw_adjustment
        if deg_turned < 0:
            self.yaw = deg_turned
            while self.yaw < 0:
                self.yaw += 360
        else:
            self.yaw = deg_turned % 360
        print(f"yaw: {self.yaw}")

    def move_forwards(self):
        """Move forwards."""
        was_aligning = self.right_wheel_speed == 10 or self.left_wheel_speed == 10
        self.left_wheel_speed = 9
        self.right_wheel_speed = 9

        self.distance_moved = self.calculate_wheel_moved_distance()
        if (abs(self.degrees_turned_total - self.destination_degrees) > 0.06) and not was_aligning:
            if self.degrees_turned_total > self.destination_degrees:
                self.left_wheel_speed = 10
            else:
                self.right_wheel_speed = 10
        aligning_with_wall = False

        if self.laser_sensed < 0.2:
            aligning_with_wall = True
            if self.laser_sensed < WALL_CALIBRATION_DIST:
                self.map.update_position(self.yaw)
                self.state = "MANAGE MAPPING"

        if not aligning_with_wall and (self.distance_moved >= 0.3 or self.laser_sensed < 0.07):
            self.map.update_position(self.yaw)
            self.state = "MANAGE MAPPING"

    def manage_mapping(self):
        """Manage states related to mapping."""
        self.state = "FIND DIRECTION"

        if self.map.back_in_initial_pos() and self.mapping_state == "REGULAR":
            self.mapping_state = "SEARCHING UNEXPLORED NEIGHBOURS"

        if self.mapping_state == "MAPPING ISLAND":
            if self.map.current_position == self.island_mapping_initial_pos:
                self.mapping_state = "CALIBRATING"
                self.destination_degrees += (self.island_mapping_initial_yaw - self.yaw)

        if self.mapping_state == "SEARCHING UNEXPLORED NEIGHBOURS":
            if self.map.has_unexplored_neighbours():
                self.island_mapping_initial_pos = self.map.current_position
                self.island_mapping_initial_yaw = self.yaw
                self.follow_wall = "RIGHT"
                self.mapping_state = "MAPPING ISLAND"

        if self.mapping_state == "CALIBRATING":
            self.state = "MANAGE MAPPING"
            if self.degrees_turned_total > self.destination_degrees:
                self.left_wheel_speed = 8
                self.right_wheel_speed = -8
            else:
                self.left_wheel_speed = -8
                self.right_wheel_speed = 8

            if abs(self.degrees_turned_total - self.destination_degrees) < 0.75:
                self.follow_wall = "LEFT"
                self.state = "FIND DIRECTION"
                self.mapping_state = "SEARCHING UNEXPLORED NEIGHBOURS"

    def find_direction(self):
        """Find direction."""
        self.state = "FACING TURN"

        self.scan_surroundings()

        if "X" not in self.surroundings.values() and self.laser_sensed > 1.5:
            self.state = "EXITED"
            self.left_wheel_speed = 0
            self.right_wheel_speed = 0
        else:
            self.map.add_surroundings(self.surroundings, self.yaw)
            if self.follow_wall == "LEFT":
                if self.surroundings["left"] == " ":
                    self.distance_moved = 0
                    self.destination_degrees += 90
                elif self.surroundings["front"] == " ":
                    self.distance_moved -= 0.3
                    self.destination_degrees += 0
                elif self.surroundings["right"] == " ":
                    self.distance_moved = 0
                    self.destination_degrees -= 90
                else:  # self.surroundings["behind"] == " ":
                    self.distance_moved -= 0.3
                    self.destination_degrees += 180

            elif self.follow_wall == "RIGHT":
                if self.surroundings["right"] == " ":
                    self.distance_moved = 0
                    self.destination_degrees -= 90
                elif self.surroundings["front"] == " ":
                    self.distance_moved -= 0.3
                    self.destination_degrees += 0
                elif self.surroundings["left"] == " ":
                    self.distance_moved = 0
                    self.destination_degrees += 90
                else:  # self.surroundings["behind"] == " ":
                    self.distance_moved -= 0.3
                    self.destination_degrees += 180

    def face_direction(self):
        """Make the robot face given destination direction."""
        if self.degrees_turned_total > self.destination_degrees:
            self.left_wheel_speed = 8
            self.right_wheel_speed = -8
        else:
            self.left_wheel_speed = -8
            self.right_wheel_speed = 8

        if abs(self.degrees_turned_total - self.destination_degrees) < 0.75:
            self.state = "MOVE FORWARDS"
            self.moving_start_left_encoder = self.sensed_left_encoder
            self.moving_start_right_encoder = self.sensed_right_encoder

    def analyze_exit(self):
        """Analyze whether the robot can exit the map."""
        if not self.map.has_explored_all_squares():
            self.destination_degrees += 180
            self.state = "FACING TURN"
        else:
            self.localize = True
            self.map.normalize_map()
            self.state = "FIND DIRECTION"
            print("final map:")
            print(self.map.get_map())
            print(self.map.matrix)
            self.left_wheel_speed = 0
            self.right_wheel_speed = 0
            self.loc_map = localization_map.Localization(self, self.map.matrix)

    def mange_localization(self):
        """Manage localization."""
        if self.timeout >= 0:
            self.timeout -= 1
            print(f"localizing in: {self.timeout}")
        if self.timeout == 150:
            # construct new possibly inaccurate yaw adjustment
            # new inaccurate (P=0.75) yaw needs to be normalized by using localization
            self.yaw_adjustment = [0, 90, 180, 270][random.randint(0, 3)]
            self.destination_degrees = int(round(self.degrees_turned_total, -1))
        self.calculate_yaw()
        if self.timeout < 0:
            self.plan_loc()

    def plan(self):
        """Plan method as per SPA architecture."""
        self.calculate_yaw()

        if not self.localize:
            print(f"laser:  {round(self.laser_sensed, 2)}    degrees turned:  {round(self.degrees_turned_total, 2)}"
                  f"  state: {self.state}   mapping state:  {self.mapping_state}")
            print(f"destination:  {self.destination_degrees}   yaw: {self.yaw}")
            print(f"wall: {self.follow_wall}   unexplored: {self.map.has_unexplored_neighbours()}")
            print(" ")
            print(self.map.get_map())
            print("")
            if self.state == "INITIALIZE":
                self.initialize()

            if self.state == "MOVE FORWARDS":
                self.move_forwards()

            if self.state == "MANAGE MAPPING":
                self.manage_mapping()

            if self.state == "FIND DIRECTION":
                self.find_direction()

            if self.state == "FACING TURN":
                self.face_direction()

            if self.state == "EXITED":
                self.analyze_exit()

        else:
            self.mange_localization()

    def sense(self):
        """Sense method according to the SPA architecture."""
        self.degrees_turned_total = self.robot.get_rotation()
        self.sensed_left_encoder = self.robot.get_left_wheel_encoder()
        self.sensed_right_encoder = self.robot.get_right_wheel_encoder()
        self.laser_sensed = self.robot.get_front_middle_laser()
        self.ir_right = self.robot.get_rear_right_side_ir()
        self.ir_left = self.robot.get_rear_left_side_ir()
        self.ir_behind = self.robot.get_rear_left_straight_ir()

    def act(self):
        """Make robot act."""
        self.robot.set_right_wheel_speed(self.right_wheel_speed)
        self.robot.set_left_wheel_speed(self.left_wheel_speed)

#  localization

    def move_forwards_loc(self):
        """Move forwards loc."""
        was_aligning = self.right_wheel_speed == 10 or self.left_wheel_speed == 10
        self.left_wheel_speed = 9
        self.right_wheel_speed = 9

        self.distance_moved = self.calculate_wheel_moved_distance()
        if (abs(self.degrees_turned_total - self.destination_degrees) > 0.06) and not was_aligning:
            if self.degrees_turned_total > self.destination_degrees:
                self.left_wheel_speed = 10
            else:
                self.right_wheel_speed = 10
        aligning_with_wall = False

        if self.laser_sensed < 0.2:
            aligning_with_wall = True
            if self.laser_sensed < WALL_CALIBRATION_DIST:
                self.loc_map.update_position(self.yaw)
                self.state = "FIND DIRECTION"

        if not aligning_with_wall and (self.distance_moved >= 0.3 or self.laser_sensed < 0.07):
            self.loc_map.update_position(self.yaw)
            self.state = "FIND DIRECTION"

    def find_direction_loc(self):
        """Find direction M4."""
        self.state = "FACING TURN"

        self.scan_surroundings()

        if "X" not in self.surroundings.values() and self.laser_sensed > 1.5:
            self.state = "EXITED"
            self.left_wheel_speed = 0
            self.right_wheel_speed = 0
        else:
            self.loc_map.add_surroundings(self.surroundings, self.yaw)
            if self.follow_wall == "LEFT":
                if self.surroundings["left"] == " ":
                    self.distance_moved = 0
                    self.destination_degrees += 90
                elif self.surroundings["front"] == " ":
                    self.distance_moved -= 0.3
                    self.destination_degrees += 0
                elif self.surroundings["right"] == " ":
                    self.distance_moved = 0
                    self.destination_degrees -= 90
                else:  # self.surroundings["behind"] == " ":
                    self.distance_moved -= 0.3
                    self.destination_degrees += 180
            else:
                self.find_direction_front_right_loc()

    def find_direction_front_right_loc(self):
        """Move the robot to the right."""
        if self.follow_wall == "FRONT":
            if self.surroundings["front"] == " ":
                self.distance_moved -= 0.3
                self.destination_degrees += 0
            elif self.surroundings["left"] == " ":
                self.distance_moved = 0
                self.destination_degrees += 90
            elif self.surroundings["right"] == " ":
                self.distance_moved = 0
                self.destination_degrees -= 90
            else:  # self.surroundings["behind"] == " ":
                self.distance_moved -= 0.3
                self.destination_degrees += 180

        elif self.follow_wall == "RIGHT":
            if self.surroundings["right"] == " ":
                self.distance_moved = 0
                self.destination_degrees -= 90
            elif self.surroundings["front"] == " ":
                self.distance_moved -= 0.3
                self.destination_degrees += 0
            elif self.surroundings["left"] == " ":
                self.distance_moved = 0
                self.destination_degrees += 90
            else:  # self.surroundings["behind"] == " ":
                self.distance_moved -= 0.3
                self.destination_degrees += 180

    def face_direction_loc(self):
        """Make the robot face given destination direction loc."""
        if self.degrees_turned_total > self.destination_degrees:
            self.left_wheel_speed = 8
            self.right_wheel_speed = -8
        else:
            self.left_wheel_speed = -8
            self.right_wheel_speed = 8

        if abs(self.degrees_turned_total - self.destination_degrees) < 0.75:
            self.state = "TRY TO LOCALIZE"
            self.left_wheel_speed = 0
            self.right_wheel_speed = 0
            self.moving_start_left_encoder = self.sensed_left_encoder
            self.moving_start_right_encoder = self.sensed_right_encoder

    def move_to_start_loc(self):
        """Move the robot to (1, 1)."""
        pos = self.loc_map.current_position
        if (pos[0], pos[1], self.yaw) in self.moving_to_start_pos_history and self.follow_wall != "RIGHT":
            self.moving_to_start_pos_history.clear()
            print("repeating position")
            self.follow_wall = "RIGHT"
            self.state = "FIND DIRECTION"

        if (not self.reached_edge
                and self.loc_map.current_position not in self.loc_map.map_edge_positions):
            self.follow_wall = "FRONT"
        elif (not self.reached_edge
              and self.loc_map.current_position in self.loc_map.map_edge_positions):
            self.reached_edge = True
            self.follow_wall = "LEFT"
        else:
            self.moving_to_start_pos_history.append((pos[0], pos[1], self.yaw))

        if self.loc_map.current_position == (1, 1):
            self.state = "DONE M4"

    def plan_loc(self):
        """Localization M4."""
        print(f"state: {self.state}  wall: {self.follow_wall}  localized: {self.is_localized}"
              f"  edge: {self.reached_edge}")
        print(f"pos: {self.loc_map.current_position}  yaw: {self.yaw} ")
        if self.state == "MOVE FORWARDS":
            self.move_forwards_loc()
        if self.state == "FIND DIRECTION":
            self.find_direction_loc()
        if self.state == "FACING TURN":
            self.face_direction_loc()
        if self.state == "TRY TO LOCALIZE":
            self.state = "MOVE FORWARDS"  # directs to "MOVE TO START" if localized
            if self.is_localized:
                self.state = "MOVE TO START"
            else:
                self.loc_map.attempt_localize()
        if self.state == "EXITED":
            self.destination_degrees += 180
            self.state = "FACING TURN"
        if self.state == "MOVE TO START":
            self.state = "MOVE FORWARDS"
            self.move_to_start_loc()

    def spin(self):
        """Execute the spin loop."""
        while not self.shutdown:
            self.sense()
            self.plan()
            self.act()
            self.robot.sleep(0.05)


def main():
    """Execute the main loop."""
    robot = Robot()
    robot.spin()


if __name__ == "__main__":
    main()
