from agent import *
from model import CityModel
from mesa.visualization import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer


def agent_portrayal(agent):
    """
    Determines how agents are visualized in the simulation.
    """
    if agent is None:
        return

    portrayal = {"Shape": "rect", "Filled": "true", "Layer": 1, "w": 1, "h": 1}

    if isinstance(agent, Road):
        portrayal["Color"] = "grey"
        portrayal["Layer"] = 0

    elif isinstance(agent, Destination):
        portrayal["Color"] = "lightgreen"
        portrayal["Layer"] = 0

    elif isinstance(agent, Traffic_Light):
        if agent.state == "red":
            portrayal["Color"] = "red"
        elif agent.state == "green":
            portrayal["Color"] = "green"
        elif agent.state == "yellow":
            portrayal["Color"] = "yellow"
        portrayal["Layer"] = 0
        portrayal["w"] = 0.8
        portrayal["h"] = 0.8

    elif isinstance(agent, Obstacle):
        portrayal["Color"] = "cadetblue"
        portrayal["Layer"] = 0
        portrayal["w"] = 0.8
        portrayal["h"] = 0.8

    elif isinstance(agent, Car):
        if agent.car_type == "A":
            portrayal["Color"] = "black"
        elif agent.car_type == "B":
            portrayal["Color"] = "blue"  # Different color for Type B cars
        portrayal["Shape"] = "circle"
        portrayal["Layer"] = 1
        portrayal["r"] = 0.5

    return portrayal

# Load the map file to determine grid size and content
map_file_path = "city_files/2022_base.txt"
with open(map_file_path) as baseFile:
    lines = baseFile.readlines()
    width = len(lines[0].strip())  # Calculate the width of the grid
    height = len(lines)           # Calculate the height of the grid

# Define model parameters
model_params = {
    "width": width,
    "height": height,
    "lines": lines,
    "steps_dist_max": 100,
}

# Configure visualization grid
grid = CanvasGrid(agent_portrayal, width, height, 500, 500)

# Start the server
server = ModularServer(
    CityModel,
    [grid],
    "Traffic Simulation with Yellow Lights",
    model_params,
)

server.port = 8521  # The default port
server.launch()