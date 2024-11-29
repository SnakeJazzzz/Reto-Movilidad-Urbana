# Reto-Movilidad-Urbana
## Link Video 
https://youtu.be/7vqTVw5mSas
## Descripción del Proyecto

Este proyecto es una simulación de tráfico urbano que modela el movimiento de vehículos en una ciudad utilizando sistemas multiagentes y gráficos computacionales. El objetivo es abordar el problema de movilidad urbana en México mediante la simulación y visualización del tráfico vehicular, representando la interacción de múltiples agentes (vehículos, semáforos, etc.) en un entorno urbano.

La simulación permite observar cómo los vehículos transitan por la ciudad, respetando las normas de tránsito, evitando obstáculos, semáforos y evitando congestiones viales. Además, proporciona una visualización gráfica en 3D utilizando WebGL, ofreciendo una representación visual atractiva y detallada de la ciudad y su tráfico.

Este proyecto se desarrolla en el contexto de mejorar la movilidad urbana, reducir la congestión vehicular y contribuir al desarrollo de soluciones para las ciudades mexicanas.

## Descripción de la Parte Servidor (Sistemas Multiagentes)

La parte del servidor se encarga de simular el comportamiento de los agentes en el entorno urbano. Utiliza el framework **Mesa** para implementar el sistema multiagentes, donde cada vehículo, semáforo, carretera y obstáculo es un agente con comportamiento definido.

### Características Principales:

- **Mapa de la Ciudad**: Se utiliza un mapa predefinido que describe las calles, semáforos, destinos y obstáculos de la ciudad.
- **Agentes Vehículos**: Los vehículos tienen como objetivo llegar a un punto de destino, respetando las reglas de tránsito, evitando colisiones y siguiendo las direcciones de las calles.
- **Semáforos Inteligentes**: Los semáforos regulan el flujo vehicular cambiando entre estados de rojo, amarillo y verde según un ciclo predefinido.
- **Evitación de Congestión**: Los vehículos buscan rutas alternativas en caso de encontrar congestión o bloqueos en su camino.
- **Memorización de Rutas**: Implementación de memoización para optimizar la búsqueda de rutas y reducir el tiempo de cómputo.

### Tecnologías Utilizadas:

- **Python 3.9 o superior**
- **Framework Mesa**: Para la implementación del sistema multiagentes.
- **Flask**: Para crear una API RESTful que permite la comunicación con el frontend.
- **Bibliotecas adicionales**: `heapq`, `random`, `os`, `collections`, entre otras.

## Descripción de la Visualización (Gráficos Computacionales)

La visualización del proyecto se realiza en un entorno 3D utilizando **WebGL** y la biblioteca **twgl.js**. Se desarrolla una interfaz gráfica que muestra en tiempo real la simulación del tráfico en la ciudad.

### Características Principales:

- **Modelos 3D**: Representación visual de los vehículos, semáforos, edificios, carreteras y otros elementos del entorno urbano.
- **Animación de Vehículos**: Los vehículos se mueven a través de las calles, giran y respetan las señales de tránsito.
- **Semáforos Dinámicos**: Los semáforos cambian de color según su estado (rojo, amarillo, verde) y afectan el comportamiento de los vehículos.
- **Interfaz de Usuario**: Controles para ajustar la posición de la cámara y controlar la simulación.
- **Iluminación y Texturas**: Uso de fuentes de iluminación para mejorar la visualización y texturas para hacer la ciudad más llamativa.

### Tecnologías Utilizadas:

- **HTML5 y CSS3**
- **JavaScript ES6**
- **WebGL**: Para renderizar gráficos 3D en el navegador.
- **twgl.js**: Biblioteca para simplificar el uso de WebGL.
- **lil-gui**: Para crear una interfaz gráfica de usuario interactiva.

## Documentación de Instalación y Ejecución

A continuación, se describen los pasos necesarios para instalar, configurar y ejecutar la simulación desde cero.

### Requisitos Previos

- **Python 3.9 o superior**: Asegúrate de tener instalado Python en tu sistema.
- **Node.js y npm**: Necesarios para manejar dependencias del frontend.
- **Git**: Para clonar el repositorio.

### Paso 1: Clonar el Repositorio

git clone //link del repo

### Paso 2: Instala las dependencias

pip install -r requirements.txt

o igual

pip install mesa flask flask-cors

### Paso 3: Ejecutar el Servidor

En la terminal, navega al directorio /Servidor y ejecutar:
python agents_server.py

### Paso 4: Configurar el Frontend

En otra terminal, navega al directorio del frontend /Visualizacion y ejecuta:
npx vite

### Paso 5: Ver  Simulación
Ingresa http://localhost:5173/ en tu buscador de preferencia.
