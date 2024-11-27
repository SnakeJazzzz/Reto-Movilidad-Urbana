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
    direccionesdic = {
        (0, 1): "up",
        (0, -1): "down",
        (1, 0): "right",
        (-1, 0): "left",
    }


    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.originalPosition = pos
        self.position = pos
        self.timeStopped = 0
        self.destination = self.model.getRandomDest()
        self.route = self.GetRoute(self.position)
        self.routeIndex = 0
        self.model.activeCars += 1
        self.stepCount = 0

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

    def step(self):
        if self.position == self.destination:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.activeCars -= 1
            self.model.addStepCount(self.stepCount)
            return

        if not self.route or self.routeIndex >= len(self.route):
            self.timeStopped += 1
            return

        next_move = self.route[self.routeIndex]
        canMove = True

        for agent in self.model.grid.get_cell_list_contents([next_move]):
            if isinstance(agent, Car) or (isinstance(agent, Traffic_Light) and not agent.go):
                canMove = False

        if canMove:
            self.model.grid.move_agent(self, next_move)
            self.position = next_move
            self.routeIndex += 1
            self.timeStopped = 0
        else:
            self.timeStopped += 1
        self.stepCount += 1


    def step(self):
        """
        Moves the car toward its destination.
        """
        if self.position == self.destination:
            print(f"Car {self.unique_id} reached destination {self.destination}")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.activeCars -= 1
            self.model.addStepCount(self.stepCount)
            return

        next_move = self.route[self.routeIndex]
        canMove = True

        for agent in self.model.grid.get_cell_list_contents([next_move]):
            if isinstance(agent, Car):
                canMove = False
            elif isinstance(agent, Traffic_Light) and not agent.go:
                canMove = False

        if canMove:
            self.model.grid.move_agent(self, next_move)
            self.position = next_move
            self.routeIndex += 1
            print(f"Car {self.unique_id} moved to {self.position}")
        else:
            self.timeStopped += 1
            print(f"Car {self.unique_id} stopped at {self.position}")

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
