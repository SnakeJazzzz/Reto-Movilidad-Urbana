# model.py

from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from .agent import Car, TrafficLight, Road, Obstacle, Destination
import json

class CityModel(Model):
    def __init__(self):
        super().__init__()
        self.schedule = SimultaneousActivation(self)
        self.running = True
        self.car_id = 0
        self.step_count = 0
        self.load_map()

    def load_map(self):
        with open('city_model/city_files/mapDictionary.json') as f:
            self.map_dict = json.load(f)

        with open('city_model/city_files/2024_base.txt') as f:
            lines = f.readlines()
            self.height = len(lines)
            self.width = len(lines[0].strip())

            self.grid = MultiGrid(self.width, self.height, torus=False)

            for y, line in enumerate(lines):
                for x, char in enumerate(line.strip()):
                    pos = (x, self.height - y - 1)
                    if char in ['>', '<', '^', 'v']:
                        direction = self.map_dict[char]
                        road = Road(f'road_{x}_{y}', self, pos, direction)
                        self.grid.place_agent(road, pos)
                    elif char in ['S', 's']:
                        time_to_change = self.map_dict[char]
                        traffic_light = TrafficLight(f'tl_{x}_{y}', self, pos, state=False, time_to_change=time_to_change)
                        self.grid.place_agent(traffic_light, pos)
                        self.schedule.add(traffic_light)
                    elif char == '#':
                        obstacle = Obstacle(f'ob_{x}_{y}', self, pos)
                        self.grid.place_agent(obstacle, pos)
                    elif char == 'D':
                        destination = Destination(f'dest_{x}_{y}', self, pos)
                        self.grid.place_agent(destination, pos)

    def step(self):
        self.schedule.step()
        self.step_count += 1

        # Cada 10 steps, agregar vehículos
        if self.step_count % 10 == 0:
            self.spawn_cars()

    def spawn_cars(self):
        # Identificar puntos de inicio (por ejemplo, posiciones específicas)
        starting_points = self.get_starting_points()
        for pos in starting_points:
            destination = self.get_random_destination()
            car = Car(f'car_{self.car_id}', self, pos, direction=None, destination=destination)
            self.grid.place_agent(car, pos)
            self.schedule.add(car)
            self.car_id += 1

    def get_starting_points(self):
        # Implementar lógica para obtener puntos de inicio
        starting_points = []
        for cell in self.grid.coord_iter():
            cell_content, x, y = cell
            for agent in cell_content:
                if isinstance(agent, Road) and agent.direction in ['Up', 'Down', 'Left', 'Right']:
                    starting_points.append((x, y))
        return starting_points

    def get_random_destination(self):
        # Implementar lógica para obtener un destino aleatorio
        destinations = [agent.pos for agent in self.grid.agents if isinstance(agent, Destination)]
        return self.random.choice(destinations)
    