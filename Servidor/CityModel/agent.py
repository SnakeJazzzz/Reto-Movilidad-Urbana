# agent.py

from mesa import Agent

class Car(Agent):
    def __init__(self, unique_id, model, pos, direction, destination):
        super().__init__(unique_id, model)
        self.pos = pos
        self.direction = direction  # Dirección actual
        self.destination = destination  # Posición del destino
        self.path = []  # Ruta calculada hacia el destino
        self.rotation = 0  # Rotación para la visualización

    def step(self):
        if self.pos == self.destination:
            # Eliminar el vehículo del modelo
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return

        # Calcular ruta si no existe
        if not self.path:
            self.calculate_path()

        if self.path:
            next_pos = self.path.pop(0)

            # Verificar si el siguiente paso es válido
            if self.check_move(next_pos):
                self.model.grid.move_agent(self, next_pos)
                self.pos = next_pos
                # Actualizar rotación según dirección
                self.update_rotation()
            else:
                # Recalcular ruta si es necesario
                self.calculate_path()

    def calculate_path(self):
        # Implementar algoritmo de búsqueda de ruta (A*)
        pass

    def check_move(self, next_pos):
        # Verificar colisiones y semáforos
        cell_agents = self.model.grid.get_cell_list_contents([next_pos])
        for agent in cell_agents:
            if isinstance(agent, Obstacle) or isinstance(agent, Car):
                return False
            if isinstance(agent, TrafficLight) and not agent.state:
                return False
        return True

    def update_rotation(self):
        # Actualizar la rotación del vehículo según su dirección
        pass  # Implementar lógica para actualizar self.rotation

class TrafficLight(Agent):
    def __init__(self, unique_id, model, pos, state=False, time_to_change=10):
        super().__init__(unique_id, model)
        self.pos = pos
        self.state = state  # True para verde, False para rojo
        self.time_to_change = time_to_change
        self.timer = 0

    def step(self):
        self.timer += 1
        if self.timer >= self.time_to_change:
            self.state = not self.state
            self.timer = 0

class Road(Agent):
    def __init__(self, unique_id, model, pos, direction):
        super().__init__(unique_id, model)
        self.pos = pos
        self.direction = direction  # 'Up', 'Down', 'Left', 'Right'

    def step(self):
        pass

class Obstacle(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos

    def step(self):
        pass

class Destination(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos

    def step(self):
        pass