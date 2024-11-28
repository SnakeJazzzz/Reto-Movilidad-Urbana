from mesa import Agent
from collections import deque
import copy

class Traffic_Light(Agent):
    """
    Traffic light agent with red, green, and yellow states.
    """

    def __init__(self, unique_id, model, red_duration, green_duration, yellow_duration, start):
        """
        Creates a new Traffic Light agent.
        Args:
            unique_id: The agent's ID.
            model: Model reference for the agent.
            red_duration: Number of steps the light stays red.
            green_duration: Number of steps the light stays green.
            yellow_duration: Number of steps the light stays yellow.
            start: Initial offset for the light (modulo total cycle).
        """
        super().__init__(unique_id, model)
        self.red_duration = red_duration
        self.green_duration = green_duration
        self.yellow_duration = yellow_duration
        self.total_cycle = red_duration + green_duration + yellow_duration
        self.cur = start % self.total_cycle
        self.state = self._get_state_from_time(self.cur)
        self.go = self.state == "green"
        print(f"Initialized Traffic Light {unique_id} at start {start} with state {self.state}")

    def step(self):
        """
        Updates the traffic light state based on its timer.
        """
        self.cur = (self.cur + 1) % self.total_cycle
        self.state = self._get_state_from_time(self.cur)
        self.go = self.state == "green"
        print(f"Traffic Light {self.unique_id} changed to {self.state}")

    def _get_state_from_time(self, time_step):
        """
        Determines the current light state based on the time step.
        Args:
            time_step: Current time step within the cycle.
        Returns:
            The current state: "red", "yellow", or "green".
        """
        if time_step < self.red_duration:
            return "red"
        elif time_step < self.red_duration + self.green_duration:
            return "green"
        else:
            return "yellow"

class Car(Agent):
    possibleLaneChange = {
        (0, 1): [(-1, 1), (1, 1)],
        (0, -1): [(-1, -1), (1, -1)],
        (1, 0): [(1, 1), (1, -1)],
        (-1, 0): [(-1, 1), (-1, -1)],
    }
    directionsDecode = {
        (0, 1): "up",
        (0, -1): "down",
        (1, 0): "right",
        (-1, 0): "left",
    }

    def __init__(self, unique_id, model, pos, car_type="A"):
        """
        Initializes a Car agent.
        Args:
            unique_id: Unique ID of the car.
            model: Reference to the simulation model.
            pos: Starting position of the car.
            car_type: Type of car, which affects behavior (e.g., "A" or "B").
        """
        super().__init__(unique_id, model)
        self.originalPosition = pos
        self.position = pos
        self.time_stopped = 0  # Tracks how long the car has been stopped
        self.destination = self.model.getRandomDest()
        self.route = self.GetRoute(self.position)
        self.routeIndex = 0
        self.model.activeCars += 1
        self.stepCount = 0
        self.direction = 0
        self.directionWritten = "up"
        self.car_type = car_type  # Store car type (e.g., "A" or "B")
        self.patience_level = 3 if car_type == "A" else 1  # Patience level differs by car type

    def GetRoute(self, start):
        """
        Finds the shortest route from start to the destination.
        Uses memoization to avoid recalculating routes.
        """
        key = str(start) + str(self.destination)
        if key in self.model.memo:
            self.model.memoCount += 1
            return self.model.memo[key]

        self.model.noMemoCount += 1
        q = deque([(start, [])])
        visited = {start}

        while q:
            cur, path = q.popleft()
            if cur == self.destination:
                self.model.memo[key] = path
                return path

            if cur not in self.model.graph:
                continue

            for move in self.model.graph[cur]:
                if move not in visited:
                    visited.add(move)
                    q.append((move, path + [move]))

        return []

    def can_change_lane(self):
        """
        Checks if the car can change lanes based on its patience level.
        Expands the search for alternative positions when initial diagonal moves fail.
        """
        if self.time_stopped >= self.patience_level:
            print(f"Car {self.unique_id} attempting lane change from {self.position}")
            
            # Check diagonal positions first
            for direction in self.possibleLaneChange[self.direction]:
                new_pos = (self.position[0] + direction[0], self.position[1] + direction[1])
                if self._is_valid_lane_change(new_pos):
                    print(f"Car {self.unique_id} successfully changing to {new_pos}")
                    self.ChangeRoute(new_pos)
                    return True
            
            # Expand search to adjacent non-diagonal positions
            print(f"Car {self.unique_id} expanding search for lane change.")
            for offset in [(0, 1), (0, -1), (1, 0), (-1, 0)]:  # Adjacent positions
                new_pos = (self.position[0] + offset[0], self.position[1] + offset[1])
                if self._is_valid_lane_change(new_pos):
                    print(f"Car {self.unique_id} changing to adjacent position {new_pos}")
                    self.ChangeRoute(new_pos)
                    return True
            
            print(f"Car {self.unique_id} could not find a valid lane change.")
        return False

    def _is_valid_lane_change(self, new_pos):
        """
        Helper method to check if a lane change position is valid.
        """
        x, y = new_pos
        if 0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height:
            if self.model.grid.is_cell_empty(new_pos):
                return True
        return False

    def ChangeRoute(self, next_move):
        """
        Updates the route starting from the new position after a lane change.
        Args:
            next_move: The new position after the lane change.
        """
        print(f"Car {self.unique_id} updating route after lane change to {next_move}")
        self.route = [next_move] + self.GetRoute(next_move)  # Update route from the new position
        self.routeIndex = 0  # Reset route index
        print(f"Car {self.unique_id} new route: {self.route}")

    def move(self):
        """
        Moves the car along its route or attempts a lane change if blocked.
        Recalculates the route or removes stalled cars to reduce gridlock.
        """
        if self.position == self.destination:
            print(f"Car {self.unique_id} has arrived at destination {self.destination}")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.activeCars -= 1
            self.model.arrived += 1
            self.model.addStepCount(self.stepCount)
            return

        next_move = self.route[self.routeIndex]
        self.direction = (next_move[0] - self.position[0], next_move[1] - self.position[1])
        if self.direction in self.directionsDecode:
            self.directionWritten = self.directionsDecode[self.direction]

        canMove = True
        for agent in self.model.grid.get_cell_list_contents([self.position]):
            if isinstance(agent, Traffic_Light) and not agent.go:
                print(f"Car {self.unique_id} stopped at traffic light at {self.position}")
                canMove = False

        if canMove:
            for agent in self.model.grid.get_cell_list_contents([next_move]):
                if isinstance(agent, Car):
                    print(f"Car {self.unique_id} blocked by another car at {next_move}")
                    if len(self.route) > 0 and self.time_stopped >= 1 and self.can_change_lane():
                        print(f"Car {self.unique_id} lane change successful")
                        next_move = self.route[self.routeIndex]
                    else:
                        canMove = False

        if canMove:
            print(f"Car {self.unique_id} moving to {next_move}")
            self.model.grid.move_agent(self, next_move)
            self.position = next_move
            self.routeIndex += 1
            self.time_stopped = 0
        else:
            self.time_stopped += 1
            print(f"Car {self.unique_id} is blocked and has waited {self.time_stopped} steps")
            
            # Recalculate route or remove car after prolonged blockage
            if self.time_stopped > 10:
                print(f"Car {self.unique_id} recalculating route due to prolonged blockage.")
                self.route = self.GetRoute(self.position)
                self.routeIndex = 0
                if not self.route:
                    print(f"Car {self.unique_id} removed due to inability to proceed.")
                    self.model.grid.remove_agent(self)
                    self.model.schedule.remove(self)
                    self.model.activeCars -= 1

    def step(self):
        """
        Steps through the simulation.
        """
        self.move()
        self.stepCount += 1
class Destination(Agent):
    """
    Destination agent representing a target location for cars.
    """

    def __init__(self, unique_id, model):
        """
        Initializes a Destination agent.
        Args:
            unique_id: Unique ID of the destination.
            model: Reference to the simulation model.
        """
        super().__init__(unique_id, model)


class Obstacle(Agent):
    """
    Obstacle agent that blocks car movement.
    """

    def __init__(self, unique_id, model):
        """
        Initializes an Obstacle agent.
        Args:
            unique_id: Unique ID of the obstacle.
            model: Reference to the simulation model.
        """
        super().__init__(unique_id, model)


class Peaton(Agent):
    """
    Peaton (pedestrian) agent that crosses the road at traffic lights.
    """

    def __init__(self, unique_id, model, start_pos, end_pos):
        """
        Initialize a pedestrian.
        Args:
            unique_id: Unique ID for the pedestrian.
            model: Reference to the model.
            start_pos: Starting position of the pedestrian.
            end_pos: End position for crossing.
        """
        super().__init__(unique_id, model)
        self.position = start_pos
        self.end_pos = end_pos
        self.crossing = False

    def step(self):
        """
        Move the pedestrian if the traffic light allows it.
        """
        if self.position == self.end_pos:
            # Peaton has crossed, remove them
            print(f"Peaton {self.unique_id} has finished crossing at {self.end_pos}")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return

        # Check the traffic light state at the crossing
        for agent in self.model.grid.get_cell_list_contents([self.position]):
            if isinstance(agent, Traffic_Light) and agent.state == "red":
                self.crossing = True

        if self.crossing:
            # Move one step toward the end position
            move_x = self.end_pos[0] - self.position[0]
            move_y = self.end_pos[1] - self.position[1]
            next_pos = (
                self.position[0] + (1 if move_x > 0 else -1 if move_x < 0 else 0),
                self.position[1] + (1 if move_y > 0 else -1 if move_y < 0 else 0),
            )

            if self.model.grid.is_cell_empty(next_pos):
                print(f"Peaton {self.unique_id} moving to {next_pos}")
                self.model.grid.move_agent(self, next_pos)
                self.position = next_pos


class Road(Agent):
    """
    Road agent where cars can move.
    """

    def __init__(self, pos, model, direction):
        """
        Creates a new road agent.
        Args:
            pos: Position of the agent.
            model: Model reference.
            direction: Movement direction for cars.
        """
        super().__init__(pos, model)
        self.direction = direction
        print(f"Road created at {pos} with direction {direction}")
