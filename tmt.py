#!/usr/bin/python3

import csv
import random
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from collections import deque
import sys

# Códigos de color
class color:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"

# Definir los estados candidatos con sus probabilidades de ser absorbentes (finales)
absorbent_probabilities = {
    'T1204': 0.42,
    'T1047': 0.97,
    'T1078': 0.405,
    'T1102': 0.59
}

# Función para cargar las transiciones desde el archivo CSV
def load_transitions(csv_file):
    transitions = {}
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            source = row['source']
            target = row['target']
            probability = float(row['probability'])
            
            if source not in transitions:
                transitions[source] = []
            transitions[source].append((target, probability))
    return transitions

# Función para verificar que la suma de probabilidades sea 1
def verify_probabilities(transitions, is_percentage=False):
    for state, transitions_list in transitions.items():
        total_prob = sum(prob for _, prob in transitions_list)
        if is_percentage:
            total_prob /= 100  # Convertir a decimal
        if not (0.99 <= total_prob <= 1.01):  # Permitimos un pequeño margen de error
            print(f"Error: La suma de probabilidades para el estado {state} es {total_prob:.2f}, y no es igual a 1.")
            exit(0)
        else:
            return

# Simular la transición entre estados de acuerdo a las probabilidades
def get_next_state(current_state, transitions):
    if current_state in transitions:
        states, probabilities = zip(*transitions[current_state])
        next_state = random.choices(states, weights=probabilities)[0]
        return next_state
    else:
        return None  # Si no hay transiciones definidas para el estado actual

# Simular estado final
def is_final_state(state):
    if state in absorbent_probabilities:
        # Usar la probabilidad específica de cada estado para decidir si debe ser absorbente
        return random.random() < absorbent_probabilities[state]
    return False

# Simular una secuencia de estados, deteniéndose en los estados absorbentes o en caso de ciclo reciente
def simulate_chain(start_state, num_steps, transitions, max_recent=5):

    state = start_state
    chain = [state]
    
    # Usar deque para almacenar solo los últimos 'max_recent' estados
    recently_visited = deque(maxlen=max_recent)

    for _ in range(num_steps):
        # Si alcanzamos un estado que, según su probabilidad, es absorbente, terminamos la secuencia
        if is_final_state(state):
            print(f"Estado absorbente alcanzado: {state}. Fin de la secuencia.")
            break

        # Detectar bucles recientes (si el estado ya está en los últimos visitados)
        if state in recently_visited:
            print(f"Bucle detectado en el estado: {state}. Fin de la secuencia.")
            break
        
        recently_visited.append(state)  # Añadir estado a los recientes
        
        # Obtener el siguiente estado
        next_s = get_next_state(state, transitions)
        if next_s is None:  # No hay más transiciones
            break
        chain.append(next_s)
        state = next_s

    return chain

# Generar secuencia de estados mediante cadena de Markov
def generate_markov_sequence():
    
    # Cargar las transiciones desde el archivo CSV generado por el script anterior
    transitions = load_transitions('transitions.csv')

    # Solicitar al usuario que ingrese el estado inicial
    # start_state = input(f"Ingrese el estado inicial (debe ser uno de {list(transitions.keys())}): ")

    # Verificar que las probabilidades sumen correctamente
    verify_probabilities(transitions, is_percentage=True)  # Cambia a False si trabajas con decimales

    # Seleccionar un estado inicial aleatorio de las claves disponibles en transitions
    start_state = random.choice(list(transitions.keys()))

    if start_state not in transitions:
        print("El estado inicial no es válido. Por favor, elija un estado disponible.")
        exit(0)
    else:
        # Simulación de la cadena de Markov
        num_steps = 80  # Número de pasos a simular
        chain = simulate_chain(start_state, num_steps, transitions)
        print("Secuencia simulada de estados:", chain)

    return chain

def create_scenario_graph(driver, scenario_file):
    try:
        with driver.session() as session:
            with open(scenario_file, 'r', encoding='utf-8') as file:
                # Leer el contenido del archivo de escenario
                query = file.read()
                
                # Ejecutar el contenido en Neo4j
                session.run(query)
                print(f"Escenario desde '{scenario_file}' insertado en Neo4j.")
    
    except Neo4jError as e:
        print(f"Error connecting to Neo4j: {e}")
        exit(1)

# Función para cargar el mapeo de técnicas a activos desde un archivo CSV
def load_techniques(csv_file):
    mapping = {}
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            technique = row['tecnica']
            asset = row['activo']
            
            if technique not in mapping:
                mapping[technique] = []
            mapping[technique].append(asset)
    return mapping

# Función para crear nodos y relaciones en Neo4j
def create_attack_graph(driver, chain, mapping):
    try:
        with driver.session() as session:
            for i in range(len(chain) - 1):
                origin_state = chain[i]
                destination_state = chain[i + 1]

                # Obtener el activo afectado por cada técnica
                origin_asset = mapping.get(origin_state, ["Desconocido"])[0]
                destination_asset = mapping.get(destination_state, ["Desconocido"])[0]
                
                # Crear los nodos y la relación con atributos adicionales
                session.run("""
                    MERGE (a:Tecnica {nombre: $estado_origen, activo_afectado: $activo_origen})
                    MERGE (b:Tecnica {nombre: $estado_destino, activo_afectado: $activo_destino})
                    MERGE (a)-[:TRANSICION_A]->(b)
                """, estado_origen=origin_state, activo_origen=origin_asset, 
                     estado_destino=destination_state, activo_destino=destination_asset)
    except Neo4jError as e:
        print(f"Error connecting to Neo4j: {e}")
        exit(1)

# Relacionar nodos de la secuencia de Markov con activos existentes en el escenario de red
def link_attack_to_scenario(driver, chain, mapping):
    try:
        with driver.session() as session:
            for state in chain:
                affected_asset = mapping.get(state, ["Desconocido"])[0]
                # Relacionar estado con activo en el escenario de red
                session.run("""
                    MATCH (a:Tecnica {nombre: $estado}), (b:Activo {name: $activo_afectado})
                    MERGE (a)-[:AFECTA_A]->(b)
                """, estado=state, activo_afectado=affected_asset)

    except Neo4jError as e:
        print(f"Error connecting to Neo4j: {e}")
        exit(1)

def clean_database(driver):
    try:
        with driver.session() as session:
            session.run("""
                MATCH (n)
                DETACH DELETE n
            """)
            print("Database cleared")

    except Neo4jError as e:
        print(f"Error connecting to Neo4j: {e}")
        exit(1)

# Función para conectar a la base de datos de Neo4j
def connect_neo4j(uri, user, password):
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        return driver

    except Neo4jError as e:
        print(f"Error connecting to Neo4j: {e}")
        exit(1)

def start_neo4j():
    # Conectar a la base de datos de Neo4j
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "markov123"
    driver = connect_neo4j(uri, user, password)
    return driver

def close_neo4j(driver):
    # Cerrar la conexión a la base de datos
    driver.close()

def help():
    print("TMT - Threat Modeling Tool")
    print(color.BLUE + "Autor:" + color.END + "\tSamuel García Sánchez")
    print(color.BLUE + "\nUSO:" + color.END)
    print("\tpython3 tmt [generate|prepare <FILE>|attack|clean] [--help|-h]\n")
    print(color.BLUE + "COMMANDS:" + color.END)
    print(color.YELLOW + "\tgenerate:" + color.END + "\tGenerar y mostrar secuencia de ataque.")
    print(color.YELLOW + "\tprepare:" + color.END + "\tCargar escenario de red enviado como parámetro en Neo4j.")
    print(color.YELLOW + "\tattack:" + color.END + "\t\tGenerar ataque y dirigirlo al escenario creado.")
    print(color.YELLOW + "\tclean:" + color.END + "\t\tLimpiar base de datos.\n")
 
def main():
    
    # Verificar argumentos
    if len(sys.argv) <= 1:
        print("You didn't specify an argument.")
        help()
        exit(1)

    if "--help" in sys.argv or "-h" in sys.argv:
        help()
        exit(0)

    if str(sys.argv[1]) == "generate":
        generate_markov_sequence()
        exit(0)
    
    if str(sys.argv[1]) == "prepare":
        
        if len(sys.argv) < 3:
            print("Please specify the scenario file.")
            exit(1)
        
        scenario_file = sys.argv[2]
        driver = start_neo4j()
        create_scenario_graph(driver, scenario_file)
        close_neo4j(driver)
        exit(0)

    elif str(sys.argv[1]) == "attack":
        chain = generate_markov_sequence()    
        mapping = load_techniques('tecnicas.csv')
        driver = start_neo4j()
        create_attack_graph(driver, chain, mapping)
        link_attack_to_scenario(driver, chain, mapping)
        
        close_neo4j(driver)
        exit(0)

    elif str(sys.argv[1]) == "clean":
        driver = start_neo4j()
        clean_database(driver)
        close_neo4j(driver)
        exit(0)

    else:
        print("No valid arguments were introduced")
        help()
        exit(0)

if __name__ == "__main__":
    main()
