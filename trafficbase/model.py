from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from agent import *
from collections import deque
import pprint
import mesa
import random


class CityModel(Model):
    """
    Simulates a city traffic system using agents for roads, cars, traffic lights, and destinations.
    """

    mapData = {
        ">": "right",
        "<": "left",
        "S": 15,  # Standard traffic light
        "s": 7,   # Traffic light with offset
        "#": "Obstacle",
        "v": "down",
        "^": "up",
        "D": "Destination",
    }

    trafficLightflow = [
        {"pos": (1, 0), "expected": "<"},
        {"pos": (-1, 0), "expected": ">"},
        {"pos": (0, -1), "expected": "^"},
        {"pos": (0, 1), "expected": "v"},
    ]

    movementvectors = {
        "^": (0, 1),
        "v": (0, -1),
        "<": (-1, 0),
        ">": (1, 0),
    }

    neighborconstraints = {
        "^": [
            {"pos": (-1, 0), "allowed": "<^D"},
            {"pos": (1, 0), "allowed": ">^D"},
        ],
        "v": [
            {"pos": (-1, 0), "allowed": "<vD"},
            {"pos": (1, 0), "allowed": ">vD"},
        ],
        "<": [
            {"pos": (0, -1), "allowed": "<vD"},
            {"pos": (0, 1), "allowed": "<^D"},
        ],
        ">": [
            {"pos": (0, -1), "allowed": ">vD"},
            {"pos": (0, 1), "allowed": ">^D"},
        ],
    }

    def __init__(self, width, height, lines, steps_dist_max):
        """
        Initializes the CityModel.
        Args:
            width: Width of the grid.
            height: Height of the grid.
            lines: Map layout as a list of strings.
            steps_dist_max: Maximum steps for step distribution tracking.
        """
        super().__init__()

        self.destinations = []
        self.unique_id = 0
        self.width = width
        self.height = height
        self.grid = MultiGrid(self.width, self.height, torus=False)
        self.schedule = RandomActivation(self)
        self.activeCars = 0
        self.memoCount = 0
        self.noMemoCount = 0

        self.stepTracker = {i: 0 for i in range(1, steps_dist_max + 1)}

        self.datacollector = mesa.DataCollector(
            {
                **{f"Steps_{i}": lambda m, i=i: m.stepTracker[i]
                   for i in self.stepTracker},
                "ActiveCars": lambda m: m.activeCars,
                "Memoization": lambda m: m.memoCount,
                "NoMemoization": lambda m: m.noMemoCount,
            }
        )

        self.graph = {}
        self.memo = {}

        self.spawnPoints = [
            (x, y) for x in [0, self.width - 1] for y in [0, self.height - 1]
        ]

        self.signalFlowcontrol = {}
        self._initialize_map(lines)
        self.running = True

    def _initialize_map(self, lines):
        """
        Initializes the map by parsing the input lines and placing agents.
        """
        graphCreated = False
        for r, row in enumerate(lines):
            for c, col in enumerate(row):
                pos = (c, self.height - r - 1)
                if col in ["v", "^", ">", "<"]:
                    agent = Road(pos, self, CityModel.mapData[col])
                    self.grid.place_agent(agent, pos)
                    if not graphCreated:
                        self.roadGraphCreator(lines, pos)
                        graphCreated = True
                elif col in ["S", "s"]:
                    self._initialize_traffic_light(pos, col)
                elif col == "#":
                    self.grid.place_agent(Obstacle(f"obs_{r}_{c}", self), pos)
                elif col == "D":
                    self.grid.place_agent(Destination(f"dest_{r}_{c}", self), pos)
                    self.destinations.append(pos)

    def _initialize_traffic_light(self, pos, char):
        """
        Initializes a traffic light agent with red, green, and yellow states.
        """
        red_duration = 7
        green_duration = 6
        yellow_duration = 2
        start_offset = 0 if char == "S" else green_duration

        traffic_light = Traffic_Light(
            f"tl_{pos[0]}_{pos[1]}",
            self,
            red_duration,
            green_duration,
            yellow_duration,
            start_offset
        )
        self.grid.place_agent(traffic_light, pos)
        self.schedule.add(traffic_light)

    def step(self):
        """
        Advances the model by one step.
        """
        self.schedule.step()
        self.datacollector.collect(self)

        # Add new cars every 2 steps
        if self.schedule.steps % 2 == 0:
            for pos in self.spawnPoints:
                if self._is_empty(pos):
                    # Randomly assign car type with specified probabilities
                    car_type = random.choices(["A", "B"], weights=[0.7, 0.3], k=1)[0]
                    car = Car(self.unique_id, self, pos, car_type=car_type)
                    self.unique_id += 1
                    self.schedule.add(car)
                    self.grid.place_agent(car, pos)

    def _is_empty(self, pos):
        """
        Checks if a position is empty of cars.
        """
        agents = self.grid.get_cell_list_contents([pos])
        return not any(isinstance(agent, Car) for agent in agents)

    def roadGraphCreator(self, lines, start):
        """
        Builds a graph for the road system based on the map.
        """
        queue = deque([start])
        visited = {start}

        while queue:
            cur = queue.popleft()
            cur_direction = self.directionsDecode(cur, lines)
            if cur_direction == "D":
                continue

            relative_pos = CityModel.movementvectors[cur_direction]
            next_pos = (cur[0] + relative_pos[0], cur[1] + relative_pos[1])

            if cur not in self.graph:
                self.graph[cur] = []
            self.graph[cur].append(next_pos)

            if next_pos not in visited:
                visited.add(next_pos)
                queue.append(next_pos)

            for side in CityModel.neighborconstraints[cur_direction]:
                x, y = cur[0] + side["pos"][0], cur[1] + side["pos"][1]
                if 0 <= x < self.width and 0 <= y < self.height:
                    if lines[self.height - y - 1][x] in side["allowed"]:
                        self.graph[cur].append((x, y))
                        if (x, y) not in visited:
                            visited.add((x, y))
                            queue.append((x, y))

    def directionsDecode(self, cur, lines):
        """
        Decodes the direction of a road cell.
        """
        val = lines[self.height - cur[1] - 1][cur[0]]
        if val in "<>^vD":
            return val

        for direction in CityModel.trafficLightflow:
            x, y = cur[0] + direction["pos"][0], cur[1] + direction["pos"][1]
            if 0 <= x < self.width and 0 <= y < self.height:
                if lines[self.height - y - 1][x] == direction["expected"]:
                    self.signalFlowcontrol[cur] = CityModel.mapData[direction["expected"]]
                    return direction["expected"]

    def getRandomDest(self):
        """
        Returns a random destination.
        """
        return self.random.choice(self.destinations) if self.destinations else None

    def addStepCount(self, steps):
        """
        Updates the step count distribution.
        """
        if steps in self.stepTracker:
            self.stepTracker[steps] += 1
