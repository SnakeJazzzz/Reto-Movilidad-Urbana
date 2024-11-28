// main.js
'use strict';

import * as twgl from 'twgl.js';
import GUI from 'lil-gui';

// Define the vertex shader code, using GLSL 3.00
const vsGLSL = `#version 300 es
in vec4 position;
in vec3 normal;

uniform mat4 u_worldViewProjection;
uniform mat4 u_worldInverseTranspose;

out vec3 v_normal;

void main() {
    gl_Position = u_worldViewProjection * position;
    v_normal = mat3(u_worldInverseTranspose) * normal;
}
`;

// Define the fragment shader code, using GLSL 3.00
const fsGLSL = `#version 300 es
precision highp float;

in vec3 v_normal;

uniform vec4 u_color;
uniform vec3 u_reverseLightDirection;

out vec4 outColor;

void main() {
    vec3 normal = normalize(v_normal);
    float light = max(dot(normal, u_reverseLightDirection), 0.0);
    outColor = u_color;
    outColor.rgb *= light;
}
`;

// Initialize WebGL-related variables
let gl, programInfo;

// Initialize arrays to store agents and scene objects
let agents = [];
let trafficLights = [];
let sceneObjects = [];

// Variables for models
let models = {};

// Variables for camera position
let cameraPosition = [15, 30, 50];
let cameraSettings = {
    x: cameraPosition[0],
    y: cameraPosition[1],
    z: cameraPosition[2],
};

// Variables for frame count
let frameCount = 0;

// Main function
async function main() {
    const canvas = document.querySelector('#canvas');
    gl = canvas.getContext('webgl2');

    if (!gl) {
        console.error('WebGL2 no es soportado');
        return;
    } else {
        gl.enable(gl.DEPTH_TEST);
        gl.enable(gl.CULL_FACE);
    }

    // Resize canvas and set viewport
    resizeCanvasToDisplaySize(gl.canvas);
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

    // Create program info
    programInfo = twgl.createProgramInfo(gl, [vsGLSL, fsGLSL]);

    // Load models
    loadModels();

    // Initialize simulation
    await initSimulation();

    // Wait briefly to ensure the server has initialized the model
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Get initial agents and traffic lights
    await getAgents();
    await getTrafficLights();

    // Setup scene objects
    setupSceneObjects();

    // Setup UI
    setupUI();

    // Start rendering loop
    requestAnimationFrame(drawScene);
}

// Function to create cube geometries for models
function loadModels() {
    // Modelo para el coche
    models.car = createCube(1);
    models.car.scale = [0.8, 0.5, 1.5]; // Escala ajustada para representar un coche

    // Modelo para el semáforo (no tiene poste, representaremos dos cubos en el aire)
    models.trafficLight = createCube(1);
    models.trafficLight.scale = [0.3, 0.3, 0.3]; // Cubo pequeño para el semáforo

    // Modelo para el edificio
    models.building = createCube(1);
    models.building.scale = [1, 3, 1]; // Cubo más alto para edificios

    // Modelo para la calle
    models.street = createCube(1);
    models.street.scale = [1, 0.1, 1]; // Cubo plano para calles

    // Modelo para el punto de destino
    models.destination = createCube(1);
    models.destination.scale = [0.5, 0.5, 0.5]; // Cubo pequeño

    // Crear el plano del piso
    models.ground = createPlane(100);
    models.ground.scale = [1, 1, 1];
}

// Function to create a cube geometry
function createCube(size = 1) {
    const arrays = twgl.primitives.createCubeVertices(size);
    const bufferInfo = twgl.createBufferInfoFromArrays(gl, arrays);
    return { bufferInfo };
}

function createPlane(size = 100) {
    const arrays = twgl.primitives.createPlaneVertices(size, size, 1, 1);
    const bufferInfo = twgl.createBufferInfoFromArrays(gl, arrays);
    return { bufferInfo };
}

// Function to determine the direction of the street at a given position
function getStreetDirectionAtPosition(x, z) {
    // Busca en el array de agentes para encontrar el agente 'Road' en esa posición
    for (const agent of agents) {
        if (agent.type === 'Road' && agent.position[0] === x && agent.position[2] === z) {
            // Si tenemos información de la dirección en el agente, úsala
            if (agent.direction === 'horizontal') {
                return 'horizontal';
            } else if (agent.direction === 'vertical') {
                return 'vertical';
            }
        }
    }
    // Por defecto, asumimos que es vertical
    return 'vertical';
}

function setupSceneObjects() {
    // Agregar el piso a los objetos de la escena
    sceneObjects.push({
        id: 'ground',
        type: 'Ground',
        position: [15, 0, 15], // Centrar el piso en la escena
        rotation: 0,
        model: models.ground,
        scale: [1, 1, 1],
    });
}

// Function to initialize the simulation
async function initSimulation() {
    try {
        const response = await fetch('http://localhost:8585/init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });

        if (response.ok) {
            console.log('Simulación inicializada');
        } else {
            console.error('Error al inicializar la simulación');
        }
    } catch (error) {
        console.error('Error en initSimulation:', error);
    }
}

// Function to get agents from the server
async function getAgents() {
    try {
        const response = await fetch('http://localhost:8585/getAgents');
        if (!response.ok) {
            console.error(`Error al obtener los agentes: ${response.status} ${response.statusText}`);
            return;
        }
        const data = await response.json();

        if (data && data.agents && Array.isArray(data.agents)) {
            agents = data.agents.map(agentData => {
                // Asignar modelo basado en el tipo de agente
                let model = null;
                let scale = [1, 1, 1];
                let rotation = 0;
                switch (agentData.type) {
                    case 'Car':
                        model = models.car;
                        scale = models.car.scale;
                        // Calcular rotación basada en la dirección
                        rotation = 0; // Valor por defecto
                        if (agentData.direction) {
                            const [dx, dy] = agentData.direction;
                            if (dx === 1 && dy === 0) {
                                rotation = -90; // Hacia el este
                            } else if (dx === -1 && dy === 0) {
                                rotation = 90; // Hacia el oeste
                            } else if (dx === 0 && dy === 1) {
                                rotation = 0; // Hacia el norte
                            } else if (dx === 0 && dy === -1) {
                                rotation = 180; // Hacia el sur
                            }
                        }
                        break;
                    case 'Obstacle':
                        model = models.building;
                        scale = models.building.scale;
                        break;
                    case 'Road':
                        model = models.street;
                        scale = models.street.scale;
                        break;
                    case 'Destination':
                        model = models.destination;
                        scale = models.destination.scale;
                        break;
                    // Otros tipos si es necesario
                    default:
                        console.warn('Tipo de agente desconocido:', agentData.type);
                        return null;
                }

                // Ajustar posición en Y basado en la escala
                let yPos = agentData.y;
                if (agentData.type === 'Obstacle') {
                    yPos += scale[1] / 2; // Centrar el edificio sobre el plano
                } else if (agentData.type === 'Destination') {
                    yPos += scale[1] / 2; // Ajustar la posición del destino
                } else if (agentData.type === 'Road') {
                    yPos += scale[1] / 2; // Asegurar que la calle se ve sobre el plano
                }

                return {
                    id: agentData.id,
                    type: agentData.type,
                    position: [agentData.x, yPos, agentData.z],
                    rotation: rotation,
                    model: model,
                    scale: scale,
                    state: agentData.state || null,
                    direction: agentData.direction || null, // Añadir la dirección si está disponible
                };
            }).filter(agent => agent !== null);
        } else {
            console.error('El formato de datos recibido del servidor no es válido. Falta la propiedad "agents".');
            agents = [];
        }
    } catch (error) {
        console.error('Error en getAgents:', error);
    }
}

// Function to get traffic lights from the server
async function getTrafficLights() {
    try {
        const response = await fetch('http://localhost:8585/getTrafficLights');
        if (response.ok) {
            const data = await response.json();
            trafficLights = data.positions.map(tlData => {
                // Ajustar posición para que los semáforos estén a los lados de la calle y elevados
                let offset = 0.4; // Ajusta este valor según sea necesario
                let x = tlData.x;
                let z = tlData.z;
                let rotation = 0;

                // Obtener la dirección de la calle en la posición del semáforo
                let streetDirection = getStreetDirectionAtPosition(tlData.x, tlData.z);

                if (streetDirection === 'horizontal') {
                    z += offset; // Mover el semáforo en Z para que esté al costado
                    rotation = 90; // Rotar el semáforo para que mire hacia la calle
                } else if (streetDirection === 'vertical') {
                    x += offset; // Mover el semáforo en X para que esté al costado
                    rotation = 0; // No rotar
                }

                // Elevar la posición en Y
                let y = tlData.y; // La altura ya está ajustada en el servidor

                return {
                    id: tlData.id,
                    type: 'TrafficLight',
                    position: [x, y, z],
                    state: tlData.state,
                    model: models.trafficLight,
                    scale: models.trafficLight.scale,
                    rotation: rotation,
                };
            });
        } else {
            console.error('Error al obtener semáforos');
        }
    } catch (error) {
        console.error('Error en getTrafficLights:', error);
    }
}

// Function to update the simulation
async function updateSimulation() {
    try {
        const response = await fetch('http://localhost:8585/update');
        if (response.ok) {
            await getAgents();
            await getTrafficLights();
        } else {
            console.error('Error al actualizar la simulación');
        }
    } catch (error) {
        console.error('Error en updateSimulation:', error);
    }
}

// Function to draw the scene
async function drawScene(time) {
    time *= 0.001; // Convert to seconds

    // Resize canvas and set viewport
    resizeCanvasToDisplaySize(gl.canvas);
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

    // Clear the canvas
    gl.clearColor(0.2, 0.2, 0.2, 1.0);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    // Set up projection and view matrices
    const aspect = gl.canvas.clientWidth / gl.canvas.clientHeight;
    const projectionMatrix = twgl.m4.perspective(degToRad(60), aspect, 0.1, 1000);

    const cameraPosition = [cameraSettings.x, cameraSettings.y, cameraSettings.z];
    const target = [15, 0, 15]; // Centrar la vista en el centro del mapa
    const up = [0, 1, 0];

    const cameraMatrix = twgl.m4.lookAt(cameraPosition, target, up);
    const viewMatrix = twgl.m4.inverse(cameraMatrix);
    const viewProjectionMatrix = twgl.m4.multiply(projectionMatrix, viewMatrix);

    // Draw agents
    for (const agent of agents) {
        drawModel(agent, viewProjectionMatrix);
    }

    // Draw traffic lights
    for (const tl of trafficLights) {
        drawModel(tl, viewProjectionMatrix);
    }

    // Draw scene objects (e.g., ground)
    for (const obj of sceneObjects) {
        drawModel(obj, viewProjectionMatrix);
    }

    // Increment frame count and update simulation periodically
    frameCount++;
    if (frameCount % 60 === 0) {
        await updateSimulation();
    }

    // Request next frame
    requestAnimationFrame(drawScene);
}

// Function to draw a model
function drawModel(object, viewProjectionMatrix) {
    if (!object.model || !object.model.bufferInfo) {
        console.error('El objeto no tiene un modelo asignado o bufferInfo:', object);
        return;
    }

    const { bufferInfo } = object.model;

    // Model matrix
    let worldMatrix = twgl.m4.identity();
    worldMatrix = twgl.m4.translate(worldMatrix, object.position);
    worldMatrix = twgl.m4.rotateY(worldMatrix, degToRad(object.rotation || 0));

    // Apply scale if the object has a 'scale' property
    if (object.scale) {
        worldMatrix = twgl.m4.scale(worldMatrix, object.scale);
    }

    // Si el objeto es un semáforo, dibujamos dos cubos
    if (object.type === 'TrafficLight') {
        drawTrafficLight(object, worldMatrix, viewProjectionMatrix);
        return; // Salimos de la función
    }

    const worldViewProjectionMatrix = twgl.m4.multiply(viewProjectionMatrix, worldMatrix);
    const worldInverseMatrix = twgl.m4.inverse(worldMatrix);
    const worldInverseTransposeMatrix = twgl.m4.transpose(worldInverseMatrix);

    // Set uniforms
    let color = [0.8, 0.8, 0.8, 1];
    if (object.type === 'Car') {
        color = [1, 0, 0, 1]; // Coches de color rojo
    } else if (object.type === 'Obstacle') {
        color = [0.6, 0.6, 0.6, 1]; // Edificios grises
    } else if (object.type === 'Road') {
        color = [0.2, 0.2, 0.2, 1]; // Calles gris oscuro
    } else if (object.type === 'Destination') {
        color = [0.0, 0.0, 1.0, 1]; // Puntos de destino azules
    } else if (object.type === 'Ground') {
        color = [0.5, 0.8, 0.5, 1]; // Color verde para el suelo
    }

    const uniforms = {
        u_worldViewProjection: worldViewProjectionMatrix,
        u_worldInverseTranspose: worldInverseTransposeMatrix,
        u_color: color,
        u_reverseLightDirection: twgl.v3.normalize([0.5, 0.7, 1]),
    };

    gl.useProgram(programInfo.program);
    twgl.setBuffersAndAttributes(gl, programInfo, bufferInfo);
    twgl.setUniforms(programInfo, uniforms);
    twgl.drawBufferInfo(gl, bufferInfo);
}

// Function to draw a traffic light with two cubes
function drawTrafficLight(object, worldMatrixBase, viewProjectionMatrix) {
    const { bufferInfo } = object.model;

    // Colores basados en el estado
    let color;
    switch (object.state) {
        case 'green':
            color = [0, 1, 0, 1];
            break;
        case 'yellow':
            color = [1, 1, 0, 1];
            break;
        case 'red':
            color = [1, 0, 0, 1];
            break;
        default:
            color = [0.8, 0.8, 0.8, 1];
    }

    // Primer cubo (más abajo)
    let worldMatrix1 = twgl.m4.copy(worldMatrixBase);

    // Segundo cubo (más arriba)
    let worldMatrix2 = twgl.m4.translate(twgl.m4.copy(worldMatrixBase), [0, 0.5, 0]); // Mover hacia arriba

    const matrices = [worldMatrix1, worldMatrix2];

    const uniforms = {
        u_color: color,
        u_reverseLightDirection: twgl.v3.normalize([0.5, 0.7, 1]),
    };

    gl.useProgram(programInfo.program);
    twgl.setBuffersAndAttributes(gl, programInfo, bufferInfo);

    // Dibujar ambos cubos
    for (let i = 0; i < matrices.length; i++) {
        let worldMatrix = matrices[i];
        const worldViewProjectionMatrix = twgl.m4.multiply(viewProjectionMatrix, worldMatrix);
        const worldInverseMatrix = twgl.m4.inverse(worldMatrix);
        const worldInverseTransposeMatrix = twgl.m4.transpose(worldInverseMatrix);

        uniforms.u_worldViewProjection = worldViewProjectionMatrix;
        uniforms.u_worldInverseTranspose = worldInverseTransposeMatrix;

        twgl.setUniforms(programInfo, uniforms);
        twgl.drawBufferInfo(gl, bufferInfo);
    }
}

// Function to resize the canvas
function resizeCanvasToDisplaySize(canvas) {
    const displayWidth  = canvas.clientWidth;
    const displayHeight = canvas.clientHeight;

    if (canvas.width !== displayWidth ||
        canvas.height !== displayHeight) {

        canvas.width  = displayWidth;
        canvas.height = displayHeight;
    }
}

// Function to set up the UI
function setupUI() {
    const gui = new GUI();
    const cameraFolder = gui.addFolder('Camera Position');
    cameraFolder.add(cameraSettings, 'x', -100, 100).onChange(updateCameraPosition);
    cameraFolder.add(cameraSettings, 'y', -100, 100).onChange(updateCameraPosition);
    cameraFolder.add(cameraSettings, 'z', -100, 100).onChange(updateCameraPosition);
    cameraFolder.open();
}

// Function to update camera position
function updateCameraPosition() {
    // Camera position is updated automatically from cameraSettings
}

// Function to convert degrees to radians
function degToRad(degrees) {
    return degrees * Math.PI / 180;
}

// Start the main function
main();