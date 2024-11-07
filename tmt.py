#!/usr/bin/python3

import csv
import json
import random
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from collections import deque
import sys
from rich.text import Text
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align
from rich.columns import Columns
from rich.bar import Bar
from rich.console import Console
from rich import print as print

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
            print("\n[red][+][reset] Error:" + f"La suma de probabilidades para el estado {state} es {total_prob:.2f}, y no es igual a 1.")
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
            print(f"\n[yellow][+][reset] Estado absorbente alcanzado: {state}. Fin de la secuencia.\n")
            break

        # Detectar bucles recientes (si el estado ya está en los últimos visitados)
        if state in recently_visited:
            print(f"[yellow][+][reset] Bucle detectado en el estado: {state}. Fin de la secuencia.\n")
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
        print("[yellow][+][reset] Secuencia simulada de estados:", str(chain))

    return chain

def create_scenario_graph(driver, scenario_file):
    try:
        with driver.session() as session:
            with open(scenario_file, 'r', encoding='utf-8') as file:
                # Leer el contenido del archivo de escenario
                query = file.read()
                
                # Ejecutar el contenido en Neo4j
                session.run(query)
                print(f"\n[green][+][reset] Escenario desde '{scenario_file}' insertado en Neo4j.\n")
    
    except Neo4jError as e:
        print("\n[red][+][reset] Error connecting to Neo4j: " + f"{e}")
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

# Función para cargar el mapeo de técnicas a activos desde el archivo JSON
def load_techniques_json(json_file):
    mapping = {}
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
        for entry in data:
            technique_id = entry["ID"]
            mapping[technique_id] = {
                "name": entry.get("name", "Desconocido"),
                "tactic": entry.get("tactics", "Desconocido"),
                "platforms": entry.get("platforms", "Desconocido"),
                "defenses_bypassed": entry.get("defenses bypassed", "Desconocido"),
                "permissions_required": entry.get("permissions required", "Desconocido"),
                "system_requirements": entry.get("system requirements", "Desconocido"),
                "effective_permissions": entry.get("effective permissions", "Desconocido")
            }
    return mapping

def create_attack_graph(driver, chain, mapping):
    try:
        with driver.session() as session:
            for i in range(len(chain) - 1):
                origin_state = chain[i]
                destination_state = chain[i + 1]

                # Obtener la información de la técnica para los atributos necesarios
                origin_technique_info = mapping.get(origin_state, {})
                dest_technique_info = mapping.get(destination_state, {})

                # Convertir atributos a listas si no lo son
                origin_platforms = origin_technique_info.get("platforms")
                if isinstance(origin_platforms, str):
                    origin_platforms = [origin_platforms]
                elif origin_platforms is None:
                    origin_platforms = []
                
                origin_permissions = origin_technique_info.get("permissions_required")
                if isinstance(origin_permissions, str):
                    origin_permissions = [origin_permissions]
                elif origin_permissions is None:
                    origin_permissions = []
                
                origin_defenses_bypassed = origin_technique_info.get("defenses_bypassed")
                if isinstance(origin_defenses_bypassed, str):
                    origin_defenses_bypassed = [origin_defenses_bypassed]
                elif origin_defenses_bypassed is None:
                    origin_defenses_bypassed = []

                origin_name = origin_technique_info.get("name")

                # Repetir el mismo proceso para el destino
                dest_platforms = dest_technique_info.get("platforms")
                if isinstance(dest_platforms, str):
                    dest_platforms = [dest_platforms]
                elif dest_platforms is None:
                    dest_platforms = []

                dest_permissions = dest_technique_info.get("permissions_required")
                if isinstance(dest_permissions, str):
                    dest_permissions = [dest_permissions]
                elif dest_permissions is None:
                    dest_permissions = []

                dest_defenses_bypassed = dest_technique_info.get("defenses_bypassed")
                if isinstance(dest_defenses_bypassed, str):
                    dest_defenses_bypassed = [dest_defenses_bypassed]
                elif dest_defenses_bypassed is None:
                    dest_defenses_bypassed = []

                dest_name = dest_technique_info.get("name")

                # Crear nodos de estado con atributos completos
                session.run("""
                    MERGE (a:Estado {
                        nombre: $estado_origen,
                        technique: $name_origen,
                        platforms: $platforms_origen,
                        permissions_required: $permissions_origen,
                        defenses_bypassed: $defenses_origen
                    })
                    MERGE (b:Estado {
                        nombre: $estado_destino,
                        technique: $name_destino,
                        platforms: $platforms_destino,
                        permissions_required: $permissions_destino,
                        defenses_bypassed: $defenses_destino
                    })
                    MERGE (a)-[:TRANSICION_A]->(b)
                """, 
                estado_origen=origin_state, name_origen=origin_name, platforms_origen=origin_platforms,
                permissions_origen=origin_permissions, defenses_origen=origin_defenses_bypassed,
                estado_destino=destination_state, name_destino=dest_name, platforms_destino=dest_platforms,
                permissions_destino=dest_permissions, defenses_destino=dest_defenses_bypassed)

            print("\n[green][+][reset] Secuencia de ataque insertada en Neo4j.\n")

    except Neo4jError as e:
        print("\n[red][+][reset] Error connecting to Neo4j: " + f"{e}")
        exit(1)

def link_attack_to_scenario(driver, chain, mapping):
    
    affected_assets = []
    affecting_techniques_ids = []
    affecting_techniques_names = []
    total_assets = []

    try:
        with driver.session() as session:
            for state in chain:
                # Obtener la información de la técnica actual
                technique_info = mapping.get(state, {})
                
                platforms = technique_info.get("platforms", [])
                if isinstance(platforms, str):
                    platforms = [platforms]
                platforms = [platform.strip() for p in platforms for platform in p.split(",")]

                permissions = technique_info.get("permissions_required", [])
                if permissions is None:
                    permissions = []
                elif isinstance(permissions, str):
                    permissions = [permissions]
                permissions = [permission.strip() for p in permissions for permission in p.split(",")]
                
                defenses_bypassed = technique_info.get("defenses_bypassed", [])
                if defenses_bypassed is None:
                    defenses_bypassed = []
                elif isinstance(defenses_bypassed, str):
                    defenses_bypassed = [defenses_bypassed]
                defenses_bypassed = [defense.strip() for d in defenses_bypassed for defense in d.split(",")]
                
                # Realizar el MATCH en Neo4j con los filtros de plataforma, permisos y defensas
                result = session.run("""
                    MATCH (a:Activo)
                    WHERE a.platform IN $platforms
                      AND ANY(permiso IN a.permissions_required WHERE permiso IN $permissions)
                    MATCH (e:Estado {nombre: $estado})
                    MATCH (n:Activo) 
                    MERGE (e)-[:AFECTA_A]->(a)
                    RETURN a.name, e.nombre, e.technique, count(n) AS total_activos
                """, platforms=platforms, defenses_bypassed=defenses_bypassed, permissions=permissions, estado=state)
                
                # Iterar sobre los registros en el resultado
                for record in result:
                    asset = record["a.name"]
                    technique_id = record["e.nombre"]
                    technique_name = record["e.technique"]
                    total_assets = record["total_activos"]
                    affected_assets.append(asset)
                    affecting_techniques_ids.append(technique_id)
                    affecting_techniques_names.append(technique_name)

        create_dashboard(affected_assets, affecting_techniques_ids, affecting_techniques_names, total_assets)

    except Neo4jError as e:
        print("\n[red][+][reset] Error connecting to Neo4j: " + f"{e}")
        exit(1)

def create_dashboard(affected_assets, affecting_techniques_ids, affecting_techniques_names, total_assets):
    if len(affected_assets) != len(affecting_techniques_ids):
        print("\n[red][+][reset] Error: Las listas deben tener la misma longitud.")
        return

    try:  
        secure_assets = int(total_assets) - int(len(set(affected_assets)))
        affected_assets_count = len(set(affected_assets))
        successful_techniques_count = len(set(affecting_techniques_ids))
        attack_severity = min(100, int((affected_assets_count / total_assets * 50) + (successful_techniques_count / len(affecting_techniques_ids) * 50)))

    except:
        print("\n[red][+][reset] No se han encontrado activos. Recuerda cargar primero el escenario.\n")
        exit(0)

    # Crear el contenido dinámico para el panel "Overview"
    overview_content = "\n"
    for asset, technique_id, technique_name in zip(affected_assets, affecting_techniques_ids, affecting_techniques_names):
        # Generar la cadena de texto con formato
        overview_content += f"· Activo[bold][cyan] {asset}[reset]\tcomprometido por [bold][cyan]{technique_id} - {technique_name}[reset]\n"

    # Crear un Panel con el contenido generado
    overview_panel = Panel(overview_content, title="[blue]RESUMEN")
    
    activos_panel = Panel(
        f"\nActivos afectados {affected_assets_count}\n"
        f"Activos seguros: {secure_assets}\n"
        f"Total de activos: {total_assets}\n",
        title="[green]:laptop_computer: ACTIVOS"
    )

    tecnicas_panel = Panel(
        f"\nTécnicas exitosas: {successful_techniques_count}\n"
        f"Técnicas intentadas: {len(affecting_techniques_ids)}\n",
        title="[red]:old_key: TÉCNICAS"
    )

    # Selección de color de barra en función de la gravedad
    if attack_severity <= 33:
        bar_color = "green"
    elif attack_severity <= 66:
        bar_color = "yellow"
    else:
        bar_color = "red"

    layout = Layout()

    # Divide the "screen" in to three parts
    layout.split(
        Layout("[yellow][+][reset] DASHBOARD"),
        Layout(name="main"),
    )
    # Divide the "main" layout in to "side" and "body"
    layout["main"].split_row(
        Layout(name="Statistics"),
        Layout(overview_panel, ratio=4)
    )
    # Divide the "side" layout in to two
    layout["Statistics"].split_column(Layout(activos_panel), Layout(tecnicas_panel))

    print(layout)
    
    # Crear y mostrar la barra de gravedad del ataque con color condicional y centrada
    bar = Bar(size=100, begin=0, end=attack_severity, color=bar_color, bgcolor="black", width=40)
    criticity_text = Text("CRITICIDAD DEL ATAQUE\n", style="r")
    percentage_text = Text(f"{attack_severity}%", style=bar_color)
    print("\n\n")
    print(Align.center(criticity_text))  # Porcentaje centrado junto a la barra
    print(Align.center(bar))
    print("\n")# Barra centrada
    print(Align.center(percentage_text))  # Porcentaje centrado junto a la barra
    
def create_dashboard2(affected_assets, affecting_techniques_ids, affecting_techniques_names, total_assets):
    # Verificar que ambas listas tienen la misma longitud
    if len(affected_assets) != len(affecting_techniques_ids):
        print("\n[red][+][reset] Error: Las listas deben tener la misma longitud.")
        return
    
    # Mostrar detalles de cada activo afectado
    for asset, technique_id, technique_name in zip(affected_assets, affecting_techniques_ids, affecting_techniques_names):
        print(f"· Activo [yellow]{asset} [reset]afectado por técnica: [red]{technique_id} - {technique_name}\n")

    try:  
        # Calcula la cantidad de activos seguros y afectados
        secure_assets = int(total_assets) - int(len(set(affected_assets)))
        affected_assets_count = len(set(affected_assets))
        successful_techniques_count = len(set(affecting_techniques_ids))

        # Calcula la gravedad del ataque como un porcentaje (basado en la proporción de activos afectados y técnicas exitosas)
        attack_severity = min(100, int((affected_assets_count / total_assets * 50) + (successful_techniques_count / len(affecting_techniques_ids) * 50)))

    except:
        print("\n[red][+][reset] No se han encontrado activos afectados.\n")
        exit(0)

    # Información en dos columnas
    activos_panel = Panel(
        f"\n[green]:laptop_computer: Activos afectados:[reset] {affected_assets_count}\n"
        f"[green]:white_check_mark: Activos seguros:[reset] {secure_assets}\n"
        f"[green]:hourglass: Total de activos:[reset] {total_assets}\n",
        title="[blue]ESTADÍSTICAS DE ACTIVOS"
    )

    tecnicas_panel = Panel(
        f"\n[red]:old_key: Técnicas exitosas:[reset] {successful_techniques_count}\n"
        f"[red]:shield: Técnicas intentadas:[reset] {len(affecting_techniques_ids)}\n",
        title="[blue]ESTADÍSTICAS DE TÉCNICAS"
    )

    # Mostrar paneles en dos columnas
    dashboard = Columns([activos_panel, tecnicas_panel])
    dashboard_centered = Align.center(dashboard, vertical="middle")
    print("\n\n")
    print(dashboard_centered)
    print("\n\n")
   
   # Selección de color de barra en función de la gravedad
    if attack_severity <= 33:
        bar_color = "green"
    elif attack_severity <= 66:
        bar_color = "yellow"
    else:
        bar_color = "red"

    # Crear y mostrar la barra de gravedad del ataque con color condicional y centrada
    bar = Bar(size=100, begin=0, end=attack_severity, color=bar_color, bgcolor="black", width=40)
    percentage_text = Text(f"{attack_severity}%", style=bar_color)

    print(Align.center(bar))
    print("\n")# Barra centrada
    print(Align.center(percentage_text))  # Porcentaje centrado junto a la barra     
        
def clean_database(driver):
    try:
        with driver.session() as session:
            session.run("""
                MATCH (n)
                DETACH DELETE n
            """)
            print("\n[green][+][reset] Database cleared\n")

    except Neo4jError as e:
        print("\n[red][+][reset] Error connecting to Neo4j: " + f"[reset]{e}")
        exit(1)

# Función para conectar a la base de datos de Neo4j
def connect_neo4j(uri, user, password):
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        return driver

    except Neo4jError as e:
        print(f"\n[red][+][reset] Error connecting to Neo4j: {e}")
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
    print("[reset]TMT - Threat Modeling Tool")
    print("[blue]Autor:" + "[reset]\tSamuel García Sánchez")
    print("[blue]\nUSO:")
    print("[reset]\tpython3 tmt [generate|prepare <FILE>|attack|clean] [--help|-h]\n")
    print("[blue]COMMANDS:")
    print("[yellow]\tgenerate:" + "[reset]\tGenerar y mostrar secuencia de ataque.")
    print("[yellow]\tprepare:" + "[reset]\tCargar escenario de red enviado como parámetro en Neo4j.")
    print("[yellow]\tattack:" + "[reset]\t\tGenerar ataque y dirigirlo al escenario creado.")
    print("[yellow]\tclean:" + "[reset]\t\tLimpiar base de datos.\n")
 
def main():
    
    # Verificar argumentos
    if len(sys.argv) <= 1:
        print("[reset]You didn't specify an argument.")
        help()
        exit(1)

    if "--help" in sys.argv or "-h" in sys.argv:
        help()
        exit(0)

    if str(sys.argv[1]) == "generate":
        generate_markov_sequence()
        load_techniques_json('tecnicas_completo.json')
        exit(0)
    
    if str(sys.argv[1]) == "prepare":
        
        if len(sys.argv) < 3:
            print("[reset]Please specify the scenario file.")
            exit(1)
        
        scenario_file = sys.argv[2]
        driver = start_neo4j()
        create_scenario_graph(driver, scenario_file)
        close_neo4j(driver)
        exit(0)

    elif str(sys.argv[1]) == "attack":
        chain = generate_markov_sequence()    
        #mapping = load_techniques_old('tecnicas.csv')
        mapping = load_techniques_json('tecnicas_completo.json')
        driver = start_neo4j()
        create_attack_graph(driver, chain, mapping)
        #link_attack_to_scenario_old(driver, chain, mapping)
        link_attack_to_scenario(driver, chain, mapping)
        
        close_neo4j(driver)
        exit(0)

    elif str(sys.argv[1]) == "clean":
        driver = start_neo4j()
        clean_database(driver)
        close_neo4j(driver)
        exit(0)

    else:
        print("[reset]No valid arguments were introduced")
        help()
        exit(0)

if __name__ == "__main__":
    main()
