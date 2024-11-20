from mesa import Agent

class Car(Agent):
    """
    Agent that moves randomly.
    Attributes:
        unique_id: Agent's ID 
        direction: Randomly chosen direction chosen from one of eight directions
    """
    def __init__(self, unique_id, model):
        """
        Creates a new random agent.
        Args:
            unique_id: The agent's ID
            model: Model reference for the agent
        """
        super().__init__(unique_id, model)

    def move(self):
        """ 
        Determines if the agent can move in the direction that was chosen
        """        
        self.model.grid.move_to_empty(self)

    def step(self):
        """ 
        Determines the new direction it will take, and then moves
        """
        self.move()

class Traffic_Light(Agent):
    def __init__(self, unique_id, model, initial_state, duration):
        super().__init__(unique_id, model)
        self.state = "red" if not initial_state else "green"  # Initial state
        self.duration = duration  # Duration for each state
        self.timer = 0  # Timer to track state duration

    def step(self):
        # Increment timer
        self.timer += 1

        # State transition logic
        if self.state == "red" and self.timer >= self.duration:
            self.state = "green"
            self.timer = 0
        elif self.state == "green" and self.timer >= self.duration:
            self.state = "yellow"
            self.timer = 0
        elif self.state == "yellow" and self.timer >= self.duration:
            self.state = "red"
            self.timer = 0


class Destination(Agent):
    """
    Destination agent. Where each car should go.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass

class Obstacle(Agent):
    """
    Obstacle agent. Just to add obstacles to the grid.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass

class Road(Agent):
    """
    Road agent. Determines where the cars can move, and in which direction.
    """
    def __init__(self, unique_id, model, direction= "Left"):
        """
        Creates a new road.
        Args:
            unique_id: The agent's ID
            model: Model reference for the agent
            direction: Direction where the cars can move
        """
        super().__init__(unique_id, model)
        self.direction = direction

    def step(self):
        pass
