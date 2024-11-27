// main.js
import * as twgl from 'twgl.js';
import GUI from 'lil-gui';

import { OBJ } from 'webgl-obj-loader';



// Función para compilar shaders y crear programa
function createProgram(gl) {
    const vertexShaderSource = `#version 300 es
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

    const fragmentShaderSource = `#version 300 es
    precision highp float;

    in vec3 v_normal;

    uniform vec3 u_reverseLightDirection;
    uniform vec4 u_color;

    out vec4 outColor;

    void main() {
        vec3 normal = normalize(v_normal);
        float light = max(dot(normal, u_reverseLightDirection), 0.0);
        outColor = u_color;
        outColor.rgb *= light;
    }
    `;

    const programInfo = twgl.createProgramInfo(gl, [vertexShaderSource, fragmentShaderSource]);
    return programInfo;
}



const canvas = document.querySelector('#canvas');
const gl = canvas.getContext('webgl2');

if (!gl) {
    console.error('WebGL2 no es soportado');
} else {
    gl.enable(gl.DEPTH_TEST);
    gl.enable(gl.CULL_FACE);
}

// Variables globales
let programInfo;
let models = {};
let agents = [];
let trafficLights = [];
let frameCount = 0;

// Variables globales para el mapa y el diccionario
let mapData;
let mapDictionary;

// Lista para almacenar los objetos estáticos de la escena
let sceneObjects = [];

// Variables globales para la posición de la cámara
let cameraPosition = [15, 30, 50];
let cameraSettings = {
    x: cameraPosition[0],
    y: cameraPosition[1],
    z: cameraPosition[2],
};

// Función principal
async function main() {
    // Configurar WebGL
    resizeCanvasToDisplaySize(gl.canvas);
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

    // Compilar shaders y crear programa
    programInfo = createProgram(gl);

    // Cargar modelos
    await loadModels();

    // Cargar el mapa y el diccionario
    await loadMapAndDictionary();

    // Parsear el mapa
    const grid = parseMap();

    // Generar los objetos de la escena
    generateSceneObjects(grid);

    // Configurar UI
    setupUI();

    // Inicializar la simulación
    await initSimulation();

    // Empezar el bucle de renderizado
    requestAnimationFrame(drawScene);
}


// Modificar la función loadObj
async function loadObj(url) {
    // Cargar el archivo OBJ
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`No se pudo cargar el modelo: ${url}`);
    }
    const text = await response.text();

    // Parsear el modelo
    const mesh = new OBJ.Mesh(text);

    // Agregar logs para verificar el contenido de mesh
    console.log(`Cargando modelo desde ${url}`);
    console.log('mesh:', mesh);
    console.log('mesh.vertices:', mesh.vertices);
    console.log('mesh.textures:', mesh.textures);
    console.log('mesh.vertexNormals:', mesh.vertexNormals);
    console.log('mesh.indices:', mesh.indices);

    // Verificar que las propiedades existen y no están vacías
    if (!mesh.vertices || mesh.vertices.length === 0) {
        throw new Error(`El modelo ${url} no tiene vértices.`);
    }

    // Crear los buffers con twgl.js
    const bufferInfo = twgl.createBufferInfoFromArrays(gl, {
        position: mesh.vertices,
        texcoord: mesh.textures,
        normal: mesh.vertexNormals,
        indices: mesh.indices,
    });

    return {
        bufferInfo,
    };
}


// Función para parsear el contenido de un archivo OBJ
function parseOBJ(text) {
    // Arrays para almacenar los datos
    const positions = [];
    const texcoords = [];
    const normals = [];

    // Objetos para almacenar los datos intermedios
    const vertexData = [positions, texcoords, normals];
    const webglVertexData = [[], [], []];

    // Expresiones regulares para parsear las líneas
    const keywordRE = /^(v|vn|vt|f|mtllib|usemtl)\b/;
    const lines = text.split('\n');

    for (let lineNo = 0; lineNo < lines.length; ++lineNo) {
        let line = lines[lineNo].trim();
        if (line === '' || line.startsWith('#')) {
            continue;
        }

        const keywordMatch = line.match(keywordRE);
        if (!keywordMatch) {
            continue;
        }

        const keyword = keywordMatch[1];
        const parts = line.split(/\s+/).slice(1);

        switch (keyword) {
            case 'v':
                positions.push(parts.map(parseFloat));
                break;
            case 'vn':
                normals.push(parts.map(parseFloat));
                break;
            case 'vt':
                texcoords.push(parts.map(parseFloat));
                break;
            case 'f':
                const numTriangles = parts.length - 2;
                for (let tri = 0; tri < numTriangles; ++tri) {
                    const indices = [0, tri + 1, tri + 2];
                    indices.forEach((vertIndex) => {
                        const ptn = parts[vertIndex].split('/');
                        ptn.forEach((objIndexStr, i) => {
                            if (!vertexData[i]) {
                                return;
                            }
                            const objIndex = parseInt(objIndexStr);
                            if (isNaN(objIndex)) {
                                return;
                            }
                            const index = objIndex >= 0 ? objIndex - 1 : vertexData[i].length + objIndex;
                            const value = vertexData[i][index];
                            if (value) {
                                webglVertexData[i].push(...value);
                            }
                        });
                    });
                }
                break;
            default:
                // Ignorar otras palabras clave
                break;
        }
    }

    const obj = {
        position: webglVertexData[0],
        texcoord: webglVertexData[1],
        normal: webglVertexData[2],
    };

    return obj;
}


// Función para cargar modelos
async function loadModels() {
    try {
        models.car = await loadObj('/models/car1.obj');
    } catch (error) {
        console.error('Error al cargar el modelo del carro:', error);
    }

    try {
        models.trafficLight = await loadObj('/models/Semaforo.obj');
    } catch (error) {
        console.error('Error al cargar el modelo del semáforo:', error);
    }

    try {
        models.building = await loadObj('/models/building1.obj');
    } catch (error) {
        console.error('Error al cargar el modelo del edificio:', error);
    }

    try {
        models.street = await loadObj('/models/street.obj');
    } catch (error) {
        console.error('Error al cargar el modelo de la calle:', error);
    }

    // Si tienes un modelo para el destino, puedes cargarlo así:
    /*
    try {
        models.destination = await loadObj('/models/destination.obj');
    } catch (error) {
        console.error('Error al cargar el modelo del destino:', error);
    }
    */
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
    const projectionMatrix = twgl.m4.perspective(degToRad(60), aspect, 0.1, 100);
    const cameraPosition = [0, 10, 20];
    const target = [15, 0, 15];
    const up = [0, 1, 0];

    const cameraMatrix = twgl.m4.lookAt(cameraPosition, target, up);
    const viewMatrix = twgl.m4.inverse(cameraMatrix);
    const viewProjectionMatrix = twgl.m4.multiply(projectionMatrix, viewMatrix);

    // Dibujar los objetos de la escena
    for (const object of sceneObjects) {
        drawModel(object, viewProjectionMatrix);
    }

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
    console.log('Dibujando modelo:', object);
    const { bufferInfo } = object.model;
    
    // Matriz de modelo
    let worldMatrix = twgl.m4.identity();
    worldMatrix = twgl.m4.translate(worldMatrix, object.position);
    worldMatrix = twgl.m4.rotateY(worldMatrix, degToRad(object.rotation || 0));
    
    // Aplicar escala si el objeto tiene una propiedad 'scale'
     if (object.scale) {
        worldMatrix = twgl.m4.scale(worldMatrix, object.scale);
     }

    const worldViewProjectionMatrix = twgl.m4.multiply(viewProjectionMatrix, worldMatrix);
    const worldInverseMatrix = twgl.m4.inverse(worldMatrix);
    const worldInverseTransposeMatrix = twgl.m4.transpose(worldInverseMatrix);
    
    // Establecer los uniforms
    const uniforms = {
        u_worldViewProjection: worldViewProjectionMatrix,
        u_worldInverseTranspose: worldInverseTransposeMatrix,
        u_color: [0.8, 0.8, 0.8, 1],
        u_reverseLightDirection: twgl.v3.normalize([0.5, 0.7, 1]),
    };
    
    gl.useProgram(programInfo.program);
    twgl.setBuffersAndAttributes(gl, programInfo, bufferInfo);
    twgl.setUniforms(programInfo, uniforms);
    twgl.drawBufferInfo(gl, bufferInfo);
}

// Función para configurar la UI
function setupUI() {
    const gui = new GUI();
    // Configura los controles según sea necesario
    gui.add(cameraSettings, 'x', -100, 100).onChange(updateCameraPosition);
    gui.add(cameraSettings, 'y', -100, 100).onChange(updateCameraPosition);
    gui.add(cameraSettings, 'z', -100, 100).onChange(updateCameraPosition);
}

function updateCameraPosition() {
    cameraPosition = [cameraSettings.x, cameraSettings.y, cameraSettings.z];
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

// Función para cargar el mapa y el diccionario
async function loadMapAndDictionary() {
    // Cargar el mapa
    const mapResponse = await fetch('/2024_base.txt');
    if (!mapResponse.ok) {
        throw new Error('No se pudo cargar el archivo del mapa');
    }
    const mapText = await mapResponse.text();

    // Cargar el diccionario
    const dictResponse = await fetch('/mapDictionary.json');
    if (!dictResponse.ok) {
        throw new Error('No se pudo cargar el diccionario del mapa');
    }
    mapDictionary = await dictResponse.json();

    // Almacenar los datos del mapa como un array de líneas
    mapData = mapText.trim().split('\n');
}

// Función para parsear el mapa en una matriz 2D
function parseMap() {
    const grid = [];
    for (let y = 0; y < mapData.length; y++) {
        const line = mapData[y];
        const row = [];
        for (let x = 0; x < line.length; x++) {
            const char = line[x];
            const cellType = mapDictionary[char] || null;
            row.push({
                x,
                y,
                char,
                type: cellType,
            });
        }
        grid.push(row);
    }
    return grid;
}


// Función para generar los objetos de la escena a partir del grid
function generateSceneObjects(grid) {
    const cellSize = 1; // Tamaño de cada celda en unidades

    for (let y = 0; y < grid.length; y++) {
        const row = grid[y];
        for (let x = 0; x < row.length; x++) {
            const cell = row[x];
            const position = [
                x * cellSize, // Posición X
                0,            // Posición Y (altura)
                y * cellSize  // Posición Z
            ];
            let rotation = 0;
            let model = null;
            let scale = [1, 1, 1];

            switch (cell.char) {
                case '#':
                    // Edificio u obstáculo
                    model = models.building;
                    scale = [1, 2, 1];
                    break;
                case '>':
                case '<':
                case '^':
                case 'v':
                case 'V':
                    // Calle con dirección
                    model = models.street;
                    rotation = getRotationForDirection(cell.char);
                    scale = [1, 1, 1];
                    break;
                case 'D':
                    // Punto de destino
                    // Si tienes un modelo específico para el destino, asígnalo aquí
                    // model = models.destination;
                    // Si no, puedes usar un modelo existente o un cubo
                    model = models.building; // Por ejemplo, usar el edificio como placeholder
                    scale = [1, 1, 1];
                    break;
                case 'S':
                case 's':
                    // Semáforo
                    model = models.trafficLight;
                    rotation = getRotationForDirection(cell.char);
                    scale = [0.5, 0.5, 0.5];
                    break;
                // Agrega más casos según sea necesario
                default:
                    // Celdas vacías o caracteres no manejados
                    continue;
            }

            // Verificar si el modelo existe antes de agregarlo
            if (model) {
                sceneObjects.push({
                    position,
                    rotation,
                    model,
                    scale,
                });
            } else {
                console.warn(`Modelo no encontrado para el carácter '${cell.char}' en la posición (${x}, ${y})`);
            }
        }
    }
}

// Función para obtener la rotación basada en el carácter de dirección
function getRotationForDirection(char) {
    switch (char) {
        case '>':
            return degToRad(0);
        case '^':
            return degToRad(90);
        case '<':
            return degToRad(180);
        case 'v':
        case 'V':
            return degToRad(270);
        default:
            return 0;
    }
}


main();