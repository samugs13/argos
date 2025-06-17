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
        trace:          Generar ataque partiendo de una técnica inicial seleccionada por el usuario.
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
- Abrir Neo4j Desktop. La primera vez que se ejecute, es posible que se requiera iniciar sesión o crear una cuenta gratuita en su defecto.

### 2. Creación de un Proyecto:

Dentro de Neo4j Desktop, es posible organizar las bases de datos en proyectos. En el panel `Projects`, accesible clicando en el icono de la carpeta de la parte superior izquierda, hacer clic en `New > Create Project` para crear un nuevo proyecto donde se alojará la base de datos.

### 3. Crear y configurar una Base de Datos Neo4j:
Para crear una base de datos y asociarla con ARGOS se han de seguir los siguientes pasos:

1. Dentro del proyecto, hacer clic en `Add` (situado en la parte superior derecha) y luego seleccionar `Local DBMS` para crear una nueva base de datos local.
2. Asignar un nombre a la base de datos y elige una contraseña para el usuario neo4j.
3. Hacer clic en `Create` y luego en `Start` para iniciar la base de datos.
4. Una vez iniciada, el botón `Open` abrirá la consola de Neo4j en el navegador, donde se podrán ejecutar consultas Cypher para visualizar los ataques.
5. En la parte inferior de la consola aparecerá la información asociada a la conexión (usuario y dirección URL). Es necesario introducir esta información (junto a la contraseña establecida dos pasos atrás) dentro de la función `start neo4j()` en el fichero `argos.py`. Esto permitirá que ARGOS interaccione con la base de datos.
6. Finalmente, se recomienda configurar en la sección `Favorites` de la consola la query `MATCH (n) RETURN n`, que no hace más que devolver todos los nodos y aristas presentes en la base de datos. Este ajuste permitirá ejecutar esta instrucción rápidamente, ya que dicha ejecución será necesaria cada vez que se realice una operación sobre la base de datos.

## Ejemplo de uso 🚀
Teniendo en cuenta el siguiente diagrama de flujo de la herramienta, en esta sección se va presenta un caso de uso a modo de ejemplo.

<p align="center">
  <img src="https://github.com/user-attachments/assets/2a79368f-32d3-4202-87a3-fa1beb16703a"/>
</p>

#### 1. Cargar el escenario de red en la base de datos
Una vez configurada la base de datos, es posible cargar en la base de datos los escenarios de red disponibles en el directorio `scenarios`mediante el comando `prepare`. 
Por ejemplo, para cargar el escenario correspondiente a una pequeña oficina corporativa habría que desplazarse en la terminal hasta el mismo directorio donde se encuentre la herrsamienta y ejecutar lo siguiente:

`python3 argos.py prepare scenarios/industrial.cypher`

Como resultado, al ejecutar la query `MATCH (n) RETURN n` en la consola de Neo4j, se visualizaría dicho escenario como un grafo:

![escenario-oficina](https://github.com/user-attachments/assets/11ce2310-c856-4adc-bc1c-fca7fc3c24a1)

#### 2. Insertar secuencia de ataque sobre el escenario
Con el escenario cargado en la base de datos, el siguiente paso es la creación de una secuencia de ataque que se insertará también en la base de datos, relacionando las técnicas de ataque con los activos afectados del escenario previamente cargado. 

Esta secuencia se puede generar de manera completamente aleatoria mediante el comando `attack` o eligiendo una técnica inicial de entre las disponibles mediante el comando `trace` (útil si ya se ha detectado una técnica y se desean estudiar los posibles pasos a seguir por el atacante).

Por ejemplo, para el comando `attack` el comando sería el siguiente:

`python3 argos.py attack`

Tras el ataque (en el caso de que haya activos afectados) se mostrará en la terminal un dashboard con estadísticas acerca de su ejecución.

![dashboard-oficina](https://github.com/user-attachments/assets/b78b1bca-482f-4645-a9db-5b92dd1fb009)

Si se vuelve a ejecutar la query en la consola de Neo4j, se podrá visualizar las relaciones establecidas con el escenario de red.

![ataque-oficina](https://github.com/user-attachments/assets/3803878f-f49a-450e-bb5b-3985b7e199d3)

#### 3. Mostrar historial de ataques
El comando `history` permite llevar una trazabilidad de los ataques que se han realizado en cada escenario de red:  

`python3 argos.py history`

La información se muestra en formato de tabla a través de la terminal:

![history](https://github.com/user-attachments/assets/05b07d4e-b4e0-45e3-9db9-7aa4f44c7151)


#### 4. Limpiar la base de datos
Antes de realizar una nueva ejecución, el comando `clean` limpia todos los nodos y relaciones presentes en la base de datos de Neo4j. 

`python3 argos.py clean`

## Información Adicional :information_source:
Para mayor detalle sobre el funcionamiento y capacidades de la herramienta, consultar la memoria completa, disponible en el archivo `TFM-SGS.pdf`

## Autor :art:
[Samuel García Sánchez](https://github.com/samugs13)
