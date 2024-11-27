# agents_server.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from city_model.model import CityModel
from city_model.agent import Car, TrafficLight, Road, Obstacle, Destination

app = Flask(__name__)
CORS(app)

model = None

@app.route('/init', methods=['POST'])
def init_model():
    global model
    #model = CityModel()
    try:
        model = CityModel()
        return jsonify({"message": "Modelo inicializado"}), 200
    except Exception as e:
        print(f"Error al inicializar el modelo: {e}")
        return jsonify({"message": "Error al inicializar el modelo"}), 500

@app.route('/getAgents', methods=['GET'])
def get_agents():
    car_positions = []
    for agent in model.schedule.agents:
        if isinstance(agent, Car):
            car_positions.append({
                'id': agent.unique_id,
                'x': agent.pos[0],
                'y': 1,  # Altura en la visualización
                'z': agent.pos[1],
                'rotation': agent.rotation  # Para orientar el modelo 3D
            })
    return jsonify({'positions': car_positions})

@app.route('/getTrafficLights', methods=['GET'])
def get_traffic_lights():
    traffic_lights = []
    for agent in model.schedule.agents:
        if isinstance(agent, TrafficLight):
            traffic_lights.append({
                'id': agent.unique_id,
                'x': agent.pos[0],
                'y': 1,
                'z': agent.pos[1],
                'state': agent.state
            })
    return jsonify({'positions': traffic_lights})

@app.route('/update', methods=['GET'])
def update_model():
    global model
    if model is None:
        return jsonify({"message": "El modelo no está inicializado"}), 400
    try:
        model.step()
        return jsonify({"message": "Modelo actualizado"}), 200
    except Exception as e:
        print(f"Error al actualizar el modelo: {e}")
        return jsonify({"message": "Error al actualizar el modelo"}), 500

#Checar si sirve el servidor
@app.route('/', methods=['GET'])
def home():
    return 'Servidor de simulación funcionando', 200

if __name__ == '__main__':
    app.run(host='localhost', port=8585)