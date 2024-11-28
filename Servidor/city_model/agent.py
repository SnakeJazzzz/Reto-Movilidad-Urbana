# agent.py

from mesa import Agent
from collections import deque
import random
import heapq

class TrafficLight(Agent):
    """
    Traffic light agent with red, green, and yellow states.
    """

    def __init__(self, unique_id, model, red_duration, green_duration, yellow_duration, start_offset=0):
        """
        Creates a new Traffic Light agent.
        Args:
            unique_id: The agent's ID.
            model: Model reference for the agent.
            red_duration: Number of steps the light stays red.
            green_duration: Number of steps the light stays green.
            yellow_duration: Number of steps the light stays yellow.
            start_offset: Initial offset for the light (modulo total cycle).
        """
        super().__init__(unique_id, model)
        self.red_duration = red_duration
        self.green_duration = green_duration
        self.yellow_duration = yellow_duration
        self.total_cycle = red_duration + green_duration + yellow_duration
        self.cur = start_offset % self.total_cycle
        self.state = self._get_state_from_time(self.cur)
        print(f"Initialized Traffic Light {unique_id} at start {start_offset} with state {self.state}")

    def step(self):
        """
        Updates the traffic light state based on its timer.
        """
        self.cur = (self.cur + 1) % self.total_cycle
        self.state = self._get_state_from_time(self.cur)
        # print(f"Traffic Light {self.unique_id} changed to {self.state}")

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
    Car agent that moves towards a destination following the road graph.
    """

    def __init__(self, unique_id, model, car_type="A"):
        super().__init__(unique_id, model)
        self.timeStopped = 0
        self.destination = self.model.getRandomDest()
        self.route = []
        self.routeIndex = 0
        self.stepCount = 0
        self.car_type = car_type  # "A" or "B"
        self.direction = (0, 0)  # Dirección inicial
        # No establecer self.pos aquí

    def step(self):
        """
        Moves the car toward its destination, following its type rules.
        """
        # Si la ruta está vacía, calcularla
        if not self.route:
            self.route = self.GetRoute(self.pos)
            if not self.route:
                # No se encontró ruta
                print(f"No route found for Car {self.unique_id} from {self.pos} to {self.destination}")
                self.model.grid.remove_agent(self)
                self.model.schedule.remove(self)
                self.model.activeCars -= 1
                return
            self.routeIndex = 0

        if self.pos == self.destination or self.routeIndex >= len(self.route):
            print(f"Car {self.unique_id} reached destination {self.destination}")
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.activeCars -= 1
            self.model.addStepCount(self.stepCount)
            return

        next_move = self.route[self.routeIndex]
        canMove = True

        # Comprobar obstáculos o otros coches en la siguiente posición
        for agent in self.model.grid.get_cell_list_contents([next_move]):
            if isinstance(agent, Car):
                canMove = False
                break  # No es necesario seguir comprobando
            elif isinstance(agent, TrafficLight):
                if agent.state == "red":
                    canMove = False
                    break
                elif agent.state == "yellow" and self.car_type == "A":
                    canMove = False
                    break

        if canMove:
            previous_position = self.pos
            self.model.grid.move_agent(self, next_move)
            self.routeIndex += 1
            self.stepCount += 1
            self.timeStopped = 0
            # print(f"Car {self.unique_id} moved to {self.pos}")

            # Calcular la dirección y normalizar
            delta_x = self.pos[0] - previous_position[0]
            delta_y = self.pos[1] - previous_position[1]
            # Normalizar la dirección
            if delta_x != 0:
                delta_x = int(delta_x / abs(delta_x))
            if delta_y != 0:
                delta_y = int(delta_y / abs(delta_y))
            self.direction = (delta_x, delta_y)
        else:
            self.timeStopped += 1
            # print(f"Car {self.unique_id} stopped at {self.pos}")

    def GetRoute(self, start):
        """
        Calculates the shortest path from start to destination using A* algorithm.
        """
        graph = self.model.graph
        memo = self.model.memo
        destination = self.destination

        # Verificar si la ruta ya está memorizada
        memo_key = (start, destination)
        if memo_key in memo:
            self.model.memoCount += 1
            return memo[memo_key]

        self.model.noMemoCount += 1

        # Implementación del algoritmo A*
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {}
        cost_so_far = {}
        came_from[start] = None
        cost_so_far[start] = 0

        while frontier:
            current_priority, current = heapq.heappop(frontier)

            if current == destination:
                break

            for next_node in graph.get(current, []):
                new_cost = cost_so_far[current] + 1  # Asumimos costo uniforme
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + self.heuristic(destination, next_node)
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current

        # Reconstruir el camino
        if destination not in came_from:
            return None  # No se encontró ruta

        path = []
        current = destination
        while current != start:
            path.append(current)
            current = came_from[current]
        path.reverse()

        # Memorizar la ruta
        memo[memo_key] = path
        return path

    def heuristic(self, a, b):
        """
        Heuristic function for A* algorithm (Manhattan distance).
        """
        (x1, y1) = a
        (x2, y2) = b
        return abs(x1 - x2) + abs(y1 - y2)


class Destination(Agent):
    """
    Destination agent representing a target location for cars.
    """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.pos = None  # La posición se establecerá al colocar en la cuadrícula


class Obstacle(Agent):
    """
    Obstacle agent that blocks car movement.
    """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.pos = None  # La posición se establecerá al colocar en la cuadrícula


class Road(Agent):
    """
    Road agent representing a segment of the road network.
    """

    def __init__(self, unique_id, model, direction):
        super().__init__(unique_id, model)
        self.direction = direction  # 'horizontal' o 'vertical'
        self.pos = None  # La posición se establecerá al colocar en la cuadrícula



