<img src="https://user-images.githubusercontent.com/78796980/168422761-4be1d1b5-c065-4f44-86d7-44d346971897.png" width="215" height="100">


# ARGOS

                                      _    ____   ____  ___  ____
                                     / \  |  _ \ / ___|/ _ \/ ___|
                                    / _ \ | |_) | |  _| | | \___ \
                                   / ___ \|  _ <| |_| | |_| |___) |
                                  /_/   \_\_| \_\\____|\___/|____/


Este repositorio contiene la herramienta desarrollada para mi Trabajo de Fin de Máster "Desarrollo de una herramienta para la simulación de rutas de ataque en entornos de conciencia cibersituacional basada en procesos estocásticos".


## Descripción :clipboard:
Attack Route Graph Observation System (ARGOS) permite simular rutas de ataque en entornos de conciencia cibersituacional, apoyando la detección de vulnerabilidades y la toma de decisiones en ciberseguridad. Esta herramienta de línea de comandos permite la generación de secuencias de ataque basadas en técnicas de la matriz MITRE ATT&CK mediante Cadenas de Markov y la visualización de su impacto sobre escenarios de red previamente definidos y completamente configurables sobre la base de datos orientada a grafos Neo4j.

<p align="center">
  <img src="https://github.com/user-attachments/assets/710bcfae-f648-4ab4-a7af-af877c413d3c"/>
</p>

## Uso :gear:

```
python3 argos.py [comando] [parámetros]

COMANDOS:
        prepare:        Cargar escenario de red enviado como argumento en Neo4j.
        attack:         Generar ataque y dirigirlo al escenario creado.
        trace:          Generar ataque partiendo de una técnica inicial.
        history:        Mostrar historial de ataques.
        clean:          Limpiar base de datos.

PARÁMETROS:
        --help|-h:      Mostrar ayuda y salir.
```

## Dependencias :bookmark:
- **Python 3.7+**
- **Neo4j 4.0+**
- Dependencias de Python:
  - `neo4j`
  - `rich`

## Estructura del proyecto :open_file_folder:

Además del propio programa escrito en Python, este repositorio contiene una serie de ficheros y directorios de los que se hace uso para proporcionar las funcionalidades descritas. Estos son los siguientes:

- `scenarios`: este directorio contiene ficheros de texto que representan los escenarios de red sobre los que realizar las simulaciones de ataque. Los escenarios están definidos usando Cypher Query Language, el lenguaje de consulta para Neo4j (es similar a SQL pero diseñado específicamente para grafos) y se pueden cargar en la base de datos mediante el comando *prepare*.
  
- `transitions.csv`: proporciona información acerca de las transiciones entre técnicas MITRE ATT&CK. Se utiliza en la implementación de una cadena de Markov para generar una secuencia aleatoria de técnicas, formando así un ataque.
  
- `tecnicas_completo.json`: contiene información detallada sobre las técnicas MITRE ATT&CK.

- `ttp_cwe_cve.json`: permite establecer una relación entre las técnicas de ataque y los CWEs/CVEs que explotan.
  
- `ttp_mitigations.json`: contiene información sobre las mitigaciones asociadas a cada técnica.

## Preparación del entorno en Neo4j :wrench:
Una vez instaladas las dependencias y clonado el repositorio, es necesaria la configuración de Neo4j, siguiendo los pasos que se indican a continuación:

### 1. Instalación y Configuración Inicial:

- Descargar e instalar Neo4j Desktop desde el [sitio oficial](https://neo4j.com/download/).
- Abrir Neo4j Desktop. La primera vez que se ejecute, es posible que se requiera iniciar sesión o crear una cuenta gratuita.

### 2. Creación de un Proyecto:

Dentro de Neo4j Desktop, es posible organizar las bases de datos en proyectos. Hacer clic en "New Project" para crear un nuevo proyecto donde se alojará la base de datos.

### 3. Crear una Base de Datos Neo4j:

- Dentro del proyecto, hacer clic en "Add Database" y luego seleccionar "Local DBMS" para crear una nueva base de datos local.
- Asignar un nombre a la base de datos y elige una contraseña para el usuario neo4j. Estas credenciales han de incluirse dentro de la función `start_neo4j()` dentro del archivo `tmt.py`
- Hacer clic en "Create" y luego en "Start" para iniciar la base de datos.
- Una vez iniciada, el botón "Open Browser" abrirá la consola de Neo4j en el navegador, donde se podrán ejecutar consultas Cypher para visualizar los ataques.

## Ejemplo 🚀

#### Prepare
`python3 tmt.py prepare <FILE>`

Carga un escenario de red en la base de datos desde un archivo que se pasa como parámetro.

#### Attack
`python3 tmt.py attack`

Genera una secuencia de ataque y la inserta en la base de datos, relacionando las técnicas de ataque con los activos afectados del escenario previamente cargado. Una vez realizado el ataque se muestra un dashboard con estadísticas acerca de su ejecución.

#### History
`python3 tmt.py history`

Muestra un historial de los ataques realizados en formato de tabla.

#### Clean
`python3 tmt.py clean`

Limpia todos los nodos y relaciones de la base de datos de Neo4j.


## Autor :art:
[Samuel García Sánchez](https://github.com/samugs13)
