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
    """
    Car agent with type differentiation.
    Args:
        unique_id: Unique ID for the car.
        model: Reference to the model.
        pos: Initial position.
        car_type: "A" or "B", determines behavior at traffic lights.
    """
    possibleLaneChange = {
        (0, 1): [(-1, 1), (1, 1)],
        (0, -1): [(-1, -1), (1, -1)],
        (1, 0): [(1, 1), (1, -1)],
        (-1, 0): [(-1, 1), (-1, -1)],
    }

    def __init__(self, unique_id, model, pos, car_type="A"):
        super().__init__(unique_id, model)
        self.originalPosition = pos
        self.position = pos
        self.timeStopped = 0
        self.destination = self.model.getRandomDest()
        self.route = self.GetRoute(self.position)
        self.routeIndex = 0
        self.model.activeCars += 1
        self.stepCount = 0
        self.direction = 0
        self.car_type = car_type
        self.patience = 3 if car_type == "A" else 1  # Set patience based on car type

    def GetRoute(self, start):
        key = str(start) + str(self.destination)
        if key in self.model.memo:
            self.model.memoCount += 1
            return self.model.memo[key]

        # Increment noMemoCount when no memoized route is found
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

        return []  # Return empty if no route found

    def _is_valid_lane_change(self, target):
        """
        Checks if a lane change is valid.
        """
        if not (0 <= target[0] < self.model.width and 0 <= target[1] < self.model.height):
            print(f"[DEBUG] Lane change invalid for Car {self.unique_id}: {target} out of bounds")
            return False

        for agent in self.model.grid.get_cell_list_contents([target]):
            if isinstance(agent, (Car, Obstacle)):
                print(f"[DEBUG] Lane change invalid for Car {self.unique_id}: {target} occupied by {agent}")
                return False

        print(f"[DEBUG] Lane change valid for Car {self.unique_id}: {target}")
        return True

    def step(self):
        """
        Moves the car toward its destination, following its type rules.
        """
        if self.position == self.destination:
            print(f"Car {self.unique_id} reached destination {self.destination}")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.activeCars -= 1
            self.model.addStepCount(self.stepCount)
            return

        if not self.route:
            print(f"Car {self.unique_id} has no route to destination {self.destination}")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.activeCars -= 1
            return

        next_move = self.route[self.routeIndex]
        canMove = True
        reason = "clear path"

        for agent in self.model.grid.get_cell_list_contents([next_move]):
            if isinstance(agent, Car):
                canMove = False
                reason = f"blocked by another car {agent.unique_id}"
            elif isinstance(agent, Traffic_Light):
                if agent.state == "red":
                    canMove = False
                    reason = "red light"
                elif agent.state == "yellow" and self.car_type == "A":
                    canMove = False
                    reason = "yellow light (Type A car)"

        if canMove:
            self.model.grid.move_agent(self, next_move)
            self.position = next_move
            self.routeIndex += 1
            self.timeStopped = 0
            print(f"Car {self.unique_id} moved to {self.position}")
        else:
            self.timeStopped += 1
            print(f"[DEBUG] Car {self.unique_id} stopped at {self.position}. Reason: {reason}")

            if self.timeStopped >= self.patience:
                print(f"[DEBUG] Car {self.unique_id} exceeded patience ({self.patience}). Evaluating lane change.")
                if self.direction in self.possibleLaneChange:
                    for lane_change in self.possibleLaneChange[self.direction]:
                        target = (self.position[0] + lane_change[0], self.position[1] + lane_change[1])
                        if self._is_valid_lane_change(target):
                            self.model.grid.move_agent(self, target)
                            self.position = target
                            self._update_direction()
                            self.changeRoute()
                            self.timeStopped = 0
                            print(f"[DEBUG] Car {self.unique_id} successfully changed lane to {self.position}")
                            return

    def _update_direction(self):
        """
        Updates the car's direction based on the next route step.
        """
        if self.routeIndex < len(self.route):
            next_pos = self.route[self.routeIndex]
            self.direction = (next_pos[0] - self.position[0], next_pos[1] - self.position[1])
        else:
            self.direction = (0, 0)
    def step(self):
        """
        Moves the car toward its destination, following its type rules.
        """
        if self.position == self.destination:
            print(f"Car {self.unique_id} reached destination {self.destination}")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.activeCars -= 1
            self.model.addStepCount(self.stepCount)
            return

        if not self.route:
            print(f"Car {self.unique_id} has no route to destination {self.destination}")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.activeCars -= 1
            return

        next_move = self.route[self.routeIndex]
        canMove = True
        reason = "clear path"

        for agent in self.model.grid.get_cell_list_contents([next_move]):
            if isinstance(agent, Car):
                canMove = False
                reason = f"blocked by another car {agent.unique_id}"
            elif isinstance(agent, Traffic_Light):
                if agent.state == "red":
                    canMove = False
                    reason = "red light"
                elif agent.state == "yellow" and self.car_type == "A":
                    canMove = False
                    reason = "yellow light (Type A car)"

        if canMove:
            self.model.grid.move_agent(self, next_move)
            self.position = next_move
            self.routeIndex += 1
            self.timeStopped = 0  # Reset stop time after moving
            print(f"Car {self.unique_id} moved to {self.position}")
        else:
            self.timeStopped += 1
            print(f"[DEBUG] Car {self.unique_id} stopped at {self.position}. Reason: {reason}")

            # Attempt lane change if patience is exceeded
            if self.timeStopped >= self.patience:
                if self.direction in self.possibleLaneChange:
                    for lane_change in self.possibleLaneChange[self.direction]:
                        target = (self.position[0] + lane_change[0], self.position[1] + lane_change[1])
                        if self._is_valid_lane_change(target):
                            self.model.grid.move_agent(self, target)
                            self.position = target
                            self._update_direction()
                            self.changeRoute()  # Recalculate route after lane change
                            self.timeStopped = 0  # Reset stop time after lane change
                            print(f"[DEBUG] Car {self.unique_id} changed lane to {self.position}")
                            return

    def _update_direction(self):
        """
        Updates the car's direction based on the next route step.
        """
        if self.routeIndex < len(self.route):
            next_pos = self.route[self.routeIndex]
            self.direction = (next_pos[0] - self.position[0], next_pos[1] - self.position[1])
        else:
            self.direction = (0, 0)

    """
    Car agent with type differentiation.
    Args:
        unique_id: Unique ID for the car.
        model: Reference to the model.
        pos: Initial position.
        car_type: "A" or "B", determines behavior at traffic lights.
    """
    possibleLaneChange = {
        (0, 1): [(-1, 1), (1, 1)],
        (0, -1): [(-1, -1), (1, -1)],
        (1, 0): [(1, 1), (1, -1)],
        (-1, 0): [(-1, 1), (-1, -1)],
    }

    def __init__(self, unique_id, model, pos, car_type="A"):
        super().__init__(unique_id, model)
        self.originalPosition = pos
        self.position = pos
        self.timeStopped = 0
        self.destination = self.model.getRandomDest()
        self.route = self.GetRoute(self.position)
        self.routeIndex = 0
        self.model.activeCars += 1
        self.stepCount = 0
        self.direction = 0
        self.car_type = car_type  # Store car type

    def GetRoute(self, start):
        key = str(start) + str(self.destination)
        if key in self.model.memo:
            self.model.memoCount += 1
            return self.model.memo[key]

        # Increment noMemoCount when no memoized route is found
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

        return []  # Return empty if no route found

    def _is_valid_lane_change(self, target):
        """
        Checks if a lane change is valid.
        """
        # Ensure the target is within bounds
        if not (0 <= target[0] < self.model.width and 0 <= target[1] < self.model.height):
            print(f"[DEBUG] Lane change invalid: {target} out of bounds")
            return False

        # Ensure the target cell is free of cars and obstacles
        for agent in self.model.grid.get_cell_list_contents([target]):
            if isinstance(agent, (Car, Obstacle)):
                print(f"[DEBUG] Lane change invalid: {target} occupied by {agent}")
                return False

        return True

    def changeRoute(self):
        """
        Recalculates the route to the destination from the car's current position
        after a lane change.
        """
        self.route = self.GetRoute(self.position)  # Recalculate the route
        self.routeIndex = 0  # Reset the index to start following the new route
        print(f"[DEBUG] Car {self.unique_id} recalculated route: {self.route}")

    def step(self):
        """
        Moves the car toward its destination, following its type rules.
        """
        if self.position == self.destination:
            print(f"Car {self.unique_id} reached destination {self.destination}")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.activeCars -= 1
            self.model.addStepCount(self.stepCount)
            return

        if not self.route:
            print(f"Car {self.unique_id} has no route to destination {self.destination}")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.activeCars -= 1
            return

        next_move = self.route[self.routeIndex]
        canMove = True
        reason = "clear path"

        # Check cell contents for movement rules
        for agent in self.model.grid.get_cell_list_contents([next_move]):
            if isinstance(agent, Car):
                canMove = False
                reason = f"blocked by another car {agent.unique_id}"
            elif isinstance(agent, Traffic_Light):
                if agent.state == "red":
                    canMove = False
                    reason = "red light"
                elif agent.state == "yellow" and self.car_type == "A":
                    canMove = False
                    reason = "yellow light (Type A car)"

        if canMove:
            self.model.grid.move_agent(self, next_move)
            self.position = next_move
            self.routeIndex += 1
            print(f"Car {self.unique_id} moved to {self.position}")
        else:
            print(f"[DEBUG] Car {self.unique_id} stopped at {self.position}. Reason: {reason}")

            # Attempt lane change if blocked
            if self.direction in self.possibleLaneChange:
                for lane_change in self.possibleLaneChange[self.direction]:
                    target = (self.position[0] + lane_change[0], self.position[1] + lane_change[1])
                    if self._is_valid_lane_change(target):
                        self.model.grid.move_agent(self, target)
                        self.position = target
                        self._update_direction()
                        self.changeRoute()  # Recalculate route after lane change
                        print(f"[DEBUG] Car {self.unique_id} changed lane to {self.position}")
                        return

            # Increment stop time if no movement
            self.timeStopped += 1

    def _update_direction(self):
        """
        Updates the car's direction based on the next route step.
        """
        if self.routeIndex < len(self.route):
            next_pos = self.route[self.routeIndex]
            self.direction = (next_pos[0] - self.position[0], next_pos[1] - self.position[1])
        else:
            self.direction = (0, 0)

class Destination(Agent):
    """
    Destination agent representing a target location for cars.
    """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class Obstacle(Agent):
    """
    Obstacle agent that blocks car movement.
    """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

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