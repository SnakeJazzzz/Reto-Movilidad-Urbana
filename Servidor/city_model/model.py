# model.py

from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from .agent import Car, TrafficLight, Road, Obstacle, Destination
from collections import deque
import mesa
import random
import os

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
    "V": "down",
    "^": "up",
    "D": "Destination",
    }
    
    trafficLightflow = [
        {"pos": (1, 0), "expected": "<"},
        {"pos": (-1, 0), "expected": ">"},
        {"pos": (0, -1), "expected": "^"},
        {"pos": (0, 1), "expected": "v"},
        {"pos": (0, 1), "expected": "V"},
    ]

    movementvectors = {
        "^": (0, 1),
        "v": (0, -1),
        "V": (0, -1),
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
        "V": [
            {"pos": (-1, 0), "allowed": "<vVD"},
            {"pos": (1, 0), "allowed": ">vVD"},
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

    def __init__(self, width=None, height=None, lines=None, steps_dist_max=100):
        """
        Initializes the CityModel.
        Args:
            width: Width of the grid.
            height: Height of the grid.
            lines: Map layout as a list of strings.
            steps_dist_max: Maximum steps for step distribution tracking.
        """
        super().__init__()

        # Load map data from a file if not provided
        if lines is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            map_file = os.path.join(current_dir, 'city_files', '2024_base.txt')  # Adjust the path if necessary
            try:
                with open(map_file, 'r') as file:
                    lines = [line.rstrip('\n') for line in file]  # Solo eliminamos el salto de línea
            except FileNotFoundError:
                print(f"Map file not found at {map_file}")
                lines = []

        if height is None:
            self.height = len(lines)
        else:
            self.height = height

        if width is None:
            self.width = max(len(line) for line in lines) if lines else 0
        else:
            self.width = width

        self.destinations = []
        self.unique_id = 0
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

        self.signalFlowcontrol = {}
        self._initialize_map(lines)
        self.roadGraphCreator(lines)  # Construimos el grafo después de inicializar el mapa

        # Definir los puntos de aparición solo en las esquinas que son carreteras
        self.spawnPoints = []
        corner_positions = [
            (0, 0),
            (self.width - 1, 0),
            (0, self.height - 1),
            (self.width - 1, self.height - 1)
        ]

        for pos in corner_positions:
            # Verificar si la posición es una carretera
            agents_in_cell = self.grid.get_cell_list_contents([pos])
            if any(isinstance(agent, Road) for agent in agents_in_cell):
                self.spawnPoints.append(pos)
                print(f"Punto de aparición añadido en {pos}")
            else:
                print(f"No es posible añadir punto de aparición en {pos}, no es una carretera")
            

        self.running = True

    def _initialize_map(self, lines):
        """
        Initializes the map by parsing the input lines and placing agents.
        """
        for r in range(self.height):
            line = lines[self.height - r - 1]
            for c in range(self.width):
                pos = (c, self.height - r - 1)
                if c < len(line):
                    col = line[c]
                else:
                    col = ' '
                if col in ["v","V", "^", ">", "<", "S", "s"]:
                    # Determinar la dirección de la carretera
                    if col in ["v", "V", "^", "S", "s"]:
                        direction = 'vertical'
                    elif col in ["<", ">"]:
                        direction = 'horizontal'
                    else:
                        direction = None  # Por si acaso

                    # Crear agente Road
                    road_agent = Road(f"road_{c}_{self.height - r - 1}", self, direction)
                    self.grid.place_agent(road_agent, pos)
                    self.schedule.add(road_agent)
                    # print(f"Placed Road at {pos} with direction {direction}")

                    # Si es un semáforo, creamos el agente TrafficLight
                    if col in ["S", "s"]:
                        self._initialize_traffic_light(pos, col)

                elif col == "#":
                    obstacle = Obstacle(f"obs_{c}_{self.height - r - 1}", self)
                    self.grid.place_agent(obstacle, pos)
                    self.schedule.add(obstacle)
                elif col == "D":
                    destination = Destination(f"dest_{c}_{self.height - r - 1}", self)
                    self.grid.place_agent(destination, pos)
                    self.schedule.add(destination)
                    self.destinations.append(pos)

    def _initialize_traffic_light(self, pos, char):
        """
        Initializes a traffic light agent with red, green, and yellow states.
        """
        red_duration = 7
        green_duration = 6
        yellow_duration = 2
        start_offset = 0 if char == "S" else green_duration

        traffic_light = TrafficLight(
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

        # Generar coches en cada paso en los puntos de aparición
        for pos in self.spawnPoints:
            if self._is_empty(pos):
                # Asignar aleatoriamente el tipo de coche con probabilidades especificadas
                car_type = random.choices(["A", "B"], weights=[0.7, 0.3], k=1)[0]
                car = Car(self.unique_id, self, car_type=car_type)  # Eliminar 'pos' aquí
                self.unique_id += 1
                self.schedule.add(car)
                self.grid.place_agent(car, pos)
                self.activeCars += 1  # Asegúrate de incrementar el contador aquí

    def _is_empty(self, pos):
        """
        Checks if a position is empty of cars.
        """
        agents = self.grid.get_cell_list_contents([pos])
        return not any(isinstance(agent, Car) for agent in agents)

    def roadGraphCreator(self, lines):
        """
        Builds a graph for the road system based on the map.
        """
        for r in range(self.height):
            for c in range(self.width):
                pos = (c, r)
                y_index = self.height - r - 1
                if 0 <= y_index < len(lines):
                    line = lines[y_index]
                    if c < len(line):
                        val = line[c]
                    else:
                        val = ' '
                else:
                    val = ' '

                if val in ["v","V", "^", ">", "<", "S", "s"]:
                    cur_direction = val
                    if val in ["S", "s"]:
                        # Obtener la dirección de la calle debajo del semáforo
                        cur_direction = self.directionsDecode(pos, lines)
                    if cur_direction == "D" or cur_direction is None:
                        continue

                    relative_pos = CityModel.movementvectors.get(cur_direction)
                    if relative_pos is None:
                        continue
                    next_pos = (pos[0] + relative_pos[0], pos[1] + relative_pos[1])

                    if pos not in self.graph:
                        self.graph[pos] = []
                    self.graph[pos].append(next_pos)

                    # Añadir conexiones laterales si existen
                    for side in CityModel.neighborconstraints.get(cur_direction, []):
                        x, y = pos[0] + side["pos"][0], pos[1] + side["pos"][1]
                        if 0 <= x < self.width and 0 <= y < self.height:
                            y_index_side = self.height - y - 1
                            if 0 <= y_index_side < len(lines):
                                side_line = lines[y_index_side]
                                if x < len(side_line):
                                    side_val = side_line[x]
                                else:
                                    side_val = ' '
                            else:
                                side_val = ' '
                            if side_val in side["allowed"]:
                                if pos not in self.graph:
                                    self.graph[pos] = []
                                self.graph[pos].append((x, y))

    def directionsDecode(self, cur, lines):
        """
        Decodes the direction of a road cell.
        """
        y_index = self.height - cur[1] - 1
        if 0 <= y_index < len(lines):
            line = lines[y_index]
            if cur[0] < len(line):
                val = line[cur[0]]
            else:
                val = ' '
        else:
            val = ' '
        if val in "<>^vD":
            return val
        elif val in ["S", "s"]:
            # Determinar la dirección de la carretera debajo del semáforo
            for direction in CityModel.trafficLightflow:
                x, y = cur[0] + direction["pos"][0], cur[1] + direction["pos"][1]
                if 0 <= x < self.width and 0 <= y < self.height:
                    y_index_check = self.height - y - 1
                    if 0 <= y_index_check < len(lines):
                        check_line = lines[y_index_check]
                        if x < len(check_line):
                            check_val = check_line[x]
                        else:
                            check_val = ' '
                    else:
                        check_val = ' '
                    if check_val == direction["expected"]:
                        return direction["expected"]
        else:
            for direction in CityModel.trafficLightflow:
                x, y = cur[0] + direction["pos"][0], cur[1] + direction["pos"][1]
                if 0 <= x < self.width and 0 <= y < self.height:
                    y_index_check = self.height - y - 1
                    if 0 <= y_index_check < len(lines):
                        check_line = lines[y_index_check]
                        if x < len(check_line):
                            check_val = check_line[x]
                        else:
                            check_val = ' '
                    else:
                        check_val = ' '
                    if check_val == direction["expected"]:
                        self.signalFlowcontrol[cur] = CityModel.mapData[direction["expected"]]
                        return direction["expected"]
        return None

    def getRandomDest(self):
        """
        Returns a random destination.
        """
        return self.random.choice(self.destinations) if self.destinations else None

    def addStepCount(self, steps):
        """
        Adds the number of steps taken by a car to reach its destination.
        """
        if steps in self.stepTracker:
            self.stepTracker[steps] += 1
        else:
            self.stepTracker[steps] = 1
    