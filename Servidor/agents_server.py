# agents_server.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from city_model.agent import Car, TrafficLight, Road, Obstacle, Destination
from city_model.model import CityModel

app = Flask(__name__)
CORS(app)

model = None

@app.route('/init', methods=['POST'])
def init_model():
    global model
    if request.method == 'POST':
        try:
            model = CityModel()
            print("Modelo inicializado exitosamente.")
            return jsonify({"message": "Modelo inicializado"}), 200
        except Exception as e:
            print(f"Error al inicializar el modelo: {e}")
            return jsonify({"message": f"Error al inicializar el modelo: {e}"}), 500

@app.route('/getAgents', methods=['GET'])
def get_agents():
    global model
    if model is None:
        return jsonify({"message": "El modelo no está inicializado."}), 400
    try:
        agent_data = []
        for (contents, (x, y)) in model.grid.coord_iter():
            for agent in contents:
                if isinstance(agent, TrafficLight):
                    continue  # Omitir los semáforos, los manejamos en otra ruta
                agent_info = {
                    'id': agent.unique_id,
                    'type': type(agent).__name__,
                    'x': x,
                    'y': 0,  # Ajustaremos la altura según el tipo de agente más adelante
                    'z': y
                }
                # Ajustar la coordenada y y añadir información adicional según el tipo de agente
                if isinstance(agent, Car):
                    agent_info['y'] = 0.25  # Un poco por encima del suelo
                    agent_info['direction'] = agent.direction
                elif isinstance(agent, Road):
                    agent_info['y'] = 0  # Nivel del suelo
                    agent_info['direction'] = agent.direction
                elif isinstance(agent, Obstacle):
                    agent_info['y'] = 0.5  # Ajustar para obstáculos (edificios)
                elif isinstance(agent, Destination):
                    agent_info['y'] = 0.25  # Ajustar para destinos
                else:
                    agent_info['y'] = 0  # Valor por defecto
                # Añadir el agente a la lista
                agent_data.append(agent_info)
        return jsonify({'agents': agent_data}), 200
    except Exception as e:
        print(f"Error en /getAgents: {e}")
        return jsonify({"message": f"Error al obtener los agentes: {e}"}), 500

@app.route('/getTrafficLights', methods=['GET'])
def get_traffic_lights():
    global model
    if model is None:
        return jsonify({"message": "El modelo no está inicializado."}), 400
    try:
        traffic_lights = []
        for agent in model.schedule.agents:
            if isinstance(agent, TrafficLight):
                x, y = agent.pos
                traffic_lights.append({
                    'id': agent.unique_id,
                    'x': x,
                    'y': 1.0,  # Elevar los semáforos
                    'z': y,
                    'state': agent.state
                })
        return jsonify({'positions': traffic_lights}), 200
    except Exception as e:
        print(f"Error en /getTrafficLights: {e}")
        return jsonify({"message": f"Error al obtener los semáforos: {e}"}), 500

@app.route('/getCars', methods=['GET'])
def get_cars():
    global model
    if model is None:
        return jsonify({"message": "El modelo no está inicializado."}), 400
    try:
        car_positions = []
        for agent in model.schedule.agents:
            if isinstance(agent, Car):
                x, y = agent.pos
                car_positions.append({
                    'id': agent.unique_id,
                    'x': x,
                    'y': 0.25,  # Un poco por encima del suelo
                    'z': y,
                    'direction': agent.direction  # Incluir la dirección del coche
                })
        return jsonify({'positions': car_positions}), 200
    except Exception as e:
        print(f"Error en /getCars: {e}")
        return jsonify({"message": f"Error al obtener los carros: {e}"}), 500

@app.route('/getBuildings', methods=['GET'])
def get_buildings():
    global model
    if model is None:
        return jsonify({"message": "El modelo no está inicializado."}), 400
    try:
        building_positions = []
        for agent in model.schedule.agents:
            if isinstance(agent, Obstacle):  # Asumiendo que los edificios son Obstacles
                x, y = agent.pos
                building_positions.append({
                    'id': agent.unique_id,
                    'x': x,
                    'y': 0.5,  # Ajustar para edificios
                    'z': y
                })
        return jsonify({'positions': building_positions}), 200
    except Exception as e:
        print(f"Error en /getBuildings: {e}")
        return jsonify({"message": f"Error al obtener los edificios: {e}"}), 500

@app.route('/getStreets', methods=['GET'])
def get_streets():
    global model
    if model is None:
        return jsonify({"message": "El modelo no está inicializado."}), 400
    try:
        street_positions = []
        for agent in model.schedule.agents:
            if isinstance(agent, Road):
                x, y = agent.pos
                street_positions.append({
                    'id': agent.unique_id,
                    'x': x,
                    'y': 0,  # Nivel del suelo
                    'z': y,
                    'direction': agent.direction  # Incluir la dirección de la calle
                })
        return jsonify({'positions': street_positions}), 200
    except Exception as e:
        print(f"Error en /getStreets: {e}")
        return jsonify({"message": f"Error al obtener las calles: {e}"}), 500

@app.route('/getDestinations', methods=['GET'])
def get_destinations():
    global model
    if model is None:
        return jsonify({"message": "El modelo no está inicializado."}), 400
    try:
        destination_positions = []
        for agent in model.schedule.agents:
            if isinstance(agent, Destination):
                x, y = agent.pos
                destination_positions.append({
                    'id': agent.unique_id,
                    'x': x,
                    'y': 0.25,  # Ajustar para destinos
                    'z': y
                })
        return jsonify({'positions': destination_positions}), 200
    except Exception as e:
        print(f"Error en /getDestinations: {e}")
        return jsonify({"message": f"Error al obtener los destinos: {e}"}), 500

@app.route('/update', methods=['GET'])
def update_model():
    global model
    if model is None:
        return jsonify({"message": "El modelo no está inicializado."}), 400
    try:
        model.step()
        return jsonify({'message': 'Modelo actualizado'}), 200
    except Exception as e:
        print(f"Error al actualizar el modelo: {e}")
        return jsonify({"message": f"Error al actualizar el modelo: {e}"}), 500

# Ruta de inicio para verificar que el servidor está funcionando
@app.route('/', methods=['GET'])
def home():
    return 'Servidor de simulación funcionando', 200

if __name__ == '__main__':
    app.run(host='localhost', port=8585)