// main.js

import { m4, v3 } from './3dLibs.js';
import GUI from 'lil-gui';

const canvas = document.querySelector('#canvas');
const gl = canvas.getContext('webgl2');

if (!gl) {
    console.error('WebGL2 no es soportado');
}

// Variables globales
let programInfo;
let models = {};
let agents = [];
let trafficLights = [];
let frameCount = 0;

// Función principal
async function main() {
    // Configurar WebGL
    resizeCanvasToDisplaySize(gl.canvas);
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

    // Compilar shaders y crear programa
    programInfo = createProgram(gl);

    // Cargar modelos
    await loadModels();

    // Configurar UI
    setupUI();

    // Inicializar la simulación
    await initSimulation();

    // Empezar el bucle de renderizado
    requestAnimationFrame(drawScene);
}

// Función para cargar modelos
async function loadModels() {
    models.car = await loadObj(gl, 'models/car.obj');
    models.trafficLight = await loadObj(gl, 'models/traffic_light.obj');
    models.building = await loadObj(gl, 'models/building.obj');
    models.wheel = await loadObj(gl, 'models/wheel.obj');
}

// Implementa la función loadObj según tu código anterior

// Función para inicializar la simulación
async function initSimulation() {
    const response = await fetch('http://localhost:8585/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
    });

    if (response.ok) {
        console.log('Simulación inicializada');
    } else {
        console.error('Error al inicializar la simulación');
    }
}

// Función para obtener los agentes del servidor
async function getAgents() {
    const response = await fetch('http://localhost:8585/getAgents');

    if (response.ok) {
        const data = await response.json();
        agents = data.positions.map(agentData => {
            const agent = {
                id: agentData.id,
                position: [agentData.x, agentData.y, agentData.z],
                rotation: agentData.rotation,
                model: models.car,
            };
            return agent;
        });
    } else {
        console.error('Error al obtener agentes');
    }
}

// Función para obtener los semáforos
async function getTrafficLights() {
    const response = await fetch('http://localhost:8585/getTrafficLights');

    if (response.ok) {
        const data = await response.json();
        trafficLights = data.positions.map(tlData => {
            const trafficLight = {
                id: tlData.id,
                position: [tlData.x, tlData.y, tlData.z],
                state: tlData.state,
                model: models.trafficLight,
            };
            return trafficLight;
        });
    } else {
        console.error('Error al obtener semáforos');
    }
}

// Función para actualizar la simulación
async function updateSimulation() {
    const response = await fetch('http://localhost:8585/update');

    if (response.ok) {
        await getAgents();
        await getTrafficLights();
    } else {
        console.error('Error al actualizar la simulación');
    }
}

// Función para dibujar la escena
async function drawScene(time) {
    time *= 0.001; // Convertir a segundos

    // Limpiar el canvas
    gl.clearColor(0.1, 0.1, 0.1, 1.0);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    // Configurar matrices de proyección y vista
    const aspect = gl.canvas.clientWidth / gl.canvas.clientHeight;
    const projectionMatrix = m4.perspective(degToRad(60), aspect, 0.1, 100);
    const cameraPosition = [0, 10, 20];
    const target = [0, 0, 0];
    const up = [0, 1, 0];
    const cameraMatrix = m4.lookAt(cameraPosition, target, up);
    const viewMatrix = m4.inverse(cameraMatrix);
    const viewProjectionMatrix = m4.multiply(projectionMatrix, viewMatrix);

    // Dibujar agentes
    for (const agent of agents) {
        drawModel(agent, viewProjectionMatrix);
    }

    // Dibujar semáforos
    for (const tl of trafficLights) {
        drawModel(tl, viewProjectionMatrix);
    }

    // Actualizar la simulación cada cierto tiempo
    frameCount++;
    if (frameCount % 60 === 0) {
        await updateSimulation();
    }

    requestAnimationFrame(drawScene);
}

// Función para dibujar un modelo
function drawModel(object, viewProjectionMatrix) {
    // Implementa la lógica para configurar las matrices de transformación y dibujar el modelo
}

// Función para configurar la UI
function setupUI() {
    const gui = new GUI();
    // Configura los controles según sea necesario
}

// Función para compilar shaders y crear programa
function createProgram(gl) {
    // Implementa la lógica para compilar shaders y crear el programa
}

// Función para ajustar el tamaño del canvas
function resizeCanvasToDisplaySize(canvas) {
    const displayWidth = canvas.clientWidth;
    const displayHeight = canvas.clientHeight;

    if (canvas.width !== displayWidth || canvas.height !== displayHeight) {
        canvas.width = displayWidth;
        canvas.height = displayHeight;
    }
}

// Función para convertir grados a radianes
function degToRad(degrees) {
    return (degrees * Math.PI) / 180;
}

main();