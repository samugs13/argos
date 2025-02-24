#!/usr/bin/python3

import csv
import json
import random
import os
import datetime
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from collections import deque
import sys
import pandas as pd
import json
from collections import defaultdict
from rich.text import Text
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align
from rich.bar import Bar
from rich.console import Group
from rich.table import Table
from rich import print as print
from collections import Counter

# Definir los estados candidatos con sus probabilidades de ser absorbentes (finales)
absorbent_probabilities = {
    'T1204': 0.42,
    'T1047': 0.97,
    'T1078': 0.405,
    'T1102': 0.59
}

current_scenario=""

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
        num_steps = 80  # Número de pasos máximo a simular
        chain = simulate_chain(start_state, num_steps, transitions)
        print("[yellow][+][reset] Secuencia simulada de estados:", str(chain))
        print("\n")
    return chain

def create_scenario_graph(driver, scenario_file):
    global current_scenario
    current_scenario=os.path.basename(scenario_file)[:-7]
    guardar_escenario(current_scenario)
    try:
        with driver.session() as session:
            with open(scenario_file, 'r', encoding='utf-8') as file:
                # Leer el contenido del archivo de escenario
                query = file.read()
                
                # Ejecutar el contenido en Neo4j
                session.run(query)
                print(f"\n[green][+][reset] Escenario '{current_scenario}' insertado en Neo4j desde el fichero '{scenario_file}'.\n")
    
    except Neo4jError as e:
        print("\n[red][+][reset] Error connecting to Neo4j: " + f"{e}")
        exit(1)

def load_cwes_json(json_file):
    
    with open(json_file, 'r') as file:
        data = json.load(file)

    ttp_to_cwes = defaultdict(set)

    for entry in data:
        # Redondear el TTP al nivel principal
        ttp_main = entry["TTP"].split('.')[0]
        for cwe in entry.get("CWEs", []):
            ttp_to_cwes[ttp_main].add(cwe["CWE"])

    # Convertimos sets a listas para el resultado final
    return {ttp: list(cwes) for ttp, cwes in ttp_to_cwes.items()}

def load_cves_json(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)

    ttp_to_cves = defaultdict(set)

    for entry in data:
        # Redondear el TTP al nivel principal
        ttp_main = entry["TTP"].split('.')[0]
        for cwe in entry.get("CWEs", []):
            for cve in cwe.get("CVEs", []):
                ttp_to_cves[ttp_main].add(cve)

    # Convertimos sets a listas para el resultado final
    return {ttp: list(cves) for ttp, cves in ttp_to_cves.items()}

# Función para cargar el mapeo de técnicas a activos desde el archivo JSON
def load_techniques_json(json_file):
    techniques = {}
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
        for entry in data:
            technique_id = entry["ID"]
            techniques[technique_id] = {
                "name": entry.get("name", "Desconocido"),
                "tactic": entry.get("tactics", "Desconocido"),
                "platforms": entry.get("platforms", "Desconocido"),
                "defenses_bypassed": entry.get("defenses bypassed", "Desconocido"),
                "permissions_required": entry.get("permissions required", "Desconocido"),
                "system_requirements": entry.get("system requirements", "Desconocido"),
                "effective_permissions": entry.get("effective permissions", "Desconocido")
            }
    return techniques

def load_mitigations_json(json_file):
    mitigations = {}
    with open(json_file, "r") as file:
        data = json.load(file)
        for item in data:
            source_name = item["source name"]
            target_ids = item["target ID"]
            for target_id in target_ids:
                mitigations[target_id] = source_name
    return mitigations

def create_attack_graph(driver, chain, techniques, cves, cwes):
    try:
        with driver.session() as session:
            for i in range(len(chain) - 1):
                origin_state = chain[i]
                destination_state = chain[i + 1]
                
                # Obtener la información de la técnica para los atributos necesarios
                origin_technique_info = techniques.get(origin_state, {})
                dest_technique_info = techniques.get(destination_state, {})

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
                
                origin_requirements = origin_technique_info.get("system_requirements")
                if isinstance(origin_requirements, str):
                    origin_requirements = [origin_requirements]
                elif origin_requirements is None:
                    origin_requirements = []

                origin_name = origin_technique_info.get("name")

                # Extraer CWEs y CVEs para esa TTP
                origin_cwes = cwes.get(origin_state, [])  # Si no hay datos, devuelve una lista vacía
                origin_cves = cves.get(origin_state, [])

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

                dest_requirements = dest_technique_info.get("system_requirements")
                if isinstance(dest_requirements, str):
                    dest_requirements = [dest_requirements]
                elif dest_requirements is None:
                    dest_requirements = []

                dest_name = dest_technique_info.get("name")

                # Extraer CWEs y CVEs para esa TTP
                dest_cwes = cwes.get(destination_state, [])  # Si no hay datos, devuelve una lista vacía
                dest_cves = cves.get(destination_state, [])

                # Crear nodos de estado con atributos completos
                session.run("""
                    MERGE (t1:Técnica {
                        id: $estado_origen,
                        name: $name_origen,
                        platforms: $platforms_origen,
                        permissions_required: $permissions_origen,
                        system_requirements: $requirements_origen,
                        CWEs: $cwes_origen,
                        CVEs: $cves_origen
                    })
                    MERGE (t2:Técnica {
                        id: $estado_destino,
                        name: $name_destino,
                        platforms: $platforms_destino,
                        permissions_required: $permissions_destino,
                        system_requirements: $requirements_destino,
                        CWEs: $cwes_destino,
                        CVEs: $cves_destino
                    })
                    MERGE (t1)-[:TRANSICIÓN]->(t2)
                """, 
                estado_origen=origin_state, name_origen=origin_name, platforms_origen=origin_platforms,
                permissions_origen=origin_permissions, requirements_origen=origin_requirements,
                estado_destino=destination_state, name_destino=dest_name, platforms_destino=dest_platforms,
                permissions_destino=dest_permissions, requirements_destino=dest_requirements,
                cwes_origen=origin_cwes, cves_origen=origin_cves, cwes_destino=dest_cwes, cves_destino=dest_cves)

            print("[green][+][reset] Secuencia de ataque insertada en Neo4j.\n")

    except Neo4jError as e:
        print("\n[red][+][reset] Error connecting to Neo4j: " + f"{e}")
        exit(1)

def link_attack_to_scenario(driver, chain, techniques, cves, cwes):
    
    affected_assets = []
    affecting_techniques_ids = []
    affecting_techniques_names = []
    total_assets = []

    try:
        with driver.session() as session:
            for state in chain:
                # Obtener la información de la técnica actual
                technique_info = techniques.get(state, {})
                
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
                
                requirements = technique_info.get("system_requirements", [])
                if requirements is None:
                    requirements = []
                elif isinstance(requirements, str):
                    requirements = [requirements]
                requirements = [req.strip() for r in requirements for req in r.split(",")]

                state_cwes = cwes.get(state, [])
                state_cves = cves.get(state, [])
                
                # Realizar el MATCH en Neo4j con los filtros de plataforma, permisos y defensas
                result = session.run("""
                    MATCH (a:Activo)
                    WHERE (a.platform IN $platforms AND (ANY(permiso IN a.permissions WHERE permiso IN $permissions)
                      OR ANY(capacidad IN a.capabilities WHERE capacidad IN $requirements)))
                      OR a.cve IN $CVEs
                    MATCH (t:Técnica {id: $estado})
                    MATCH (n:Activo) 
                    MERGE (t)-[:EXPLOTACIÓN]->(a)
                    RETURN a.name, t.id, t.name, count(n) AS total_activos
                """, platforms=platforms, requirements=requirements, permissions=permissions,
                     CVEs=state_cves, estado=state)
                
                # Iterar sobre los registros en el resultado
                for record in result:
                    asset = record["a.name"]
                    technique_id = record["t.id"]
                    technique_name = record["t.name"]
                    total_assets = record["total_activos"]
                    affected_assets.append(asset)
                    affecting_techniques_ids.append(technique_id)
                    affecting_techniques_names.append(technique_name)
    
        #Crear dashboard del ataque
        create_dashboard(affected_assets, affecting_techniques_ids, affecting_techniques_names, total_assets, chain)

    except Neo4jError as e:
        print("\n[red][+][reset] Error connecting to Neo4j: " + f"{e}")
        exit(1)

def create_dashboard(affected_assets, affecting_techniques_ids, affecting_techniques_names, total_assets, chain):
    
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
    
    secuencia_content = "\n"
    for state in chain:
        # Generar la cadena de texto con formato
        secuencia_content += f"[b]{state}[reset] -> "
        
    secuencia_content = secuencia_content[:-4] # Eliminar flecha del último estado
    secuencia_panel = Panel(secuencia_content, title="[b magenta]:link: ATAQUE", padding=(0, 1), border_style="magenta")  

    # Crear el contenido dinámico para el panel "Overview"
    defense_content = "\n"
    for asset, technique_id, technique_name in zip(affected_assets, affecting_techniques_ids, affecting_techniques_names):
        # Generar la cadena de texto con formato
        defense_content += f"[b]·[reset] Activo [u]{asset}[reset] comprometido por [u]{technique_id} - {technique_name}[reset]\n"

    # Crear un Panel con el contenido generado
    defense_panel = Panel(defense_content, title="[b blue]:shield: DEFENSA", padding=(0, 1), border_style="blue")
   
    # Calcular activos más afectados   
    counter = Counter(affected_assets)
    max_freq = max(counter.values())
    most_affected_assets = [activo for activo, frecuencia in counter.items() if frecuencia == max_freq]
    maa_str = ", ".join(most_affected_assets)

    # Calcular técnicas más exitosas   
    counter = Counter(affecting_techniques_ids)
    max_freq = max(counter.values())
    most_affecting_techniques = [tech for tech, frecuencia in counter.items() if frecuencia == max_freq]
    mat_str = ", ".join(most_affecting_techniques)
    
    # Obtener mitigaciones asociadas a las técnicas más exitosas
    mitigations = load_mitigations_json('ttp_mitigations.json')
    unique_mitigations = list({mitigations[tech] for tech in most_affecting_techniques if tech in mitigations})
    mit_str = ", ".join(unique_mitigations)

    activos_panel = Panel(
        f"\n[b]Total de activos:[reset]\t{total_assets}\n"
        f"\n[b]Activos afectados:[reset]\t{affected_assets_count} ({round(100*affected_assets_count/total_assets, 1)}%)\n"
        f"\n[b]Activos seguros:[reset]\t{secure_assets} ({round(100*secure_assets/total_assets, 1)}%)\n"
        f"\n[b]Activo(s) más afectado(s):[reset] {maa_str} ({max_freq} veces)\n",
        title="[b green]:laptop_computer: ACTIVOS",
        padding=(0, 1),
        border_style="green"
    )

    tecnicas_panel = Panel(
        f"\n[b]Técnicas en la secuencia:[reset]\t{len(chain)}\n"
        f"\n[b]Técnicas distintas empleadas:[reset]\t{len(set(chain))}\n"
        f"\n[b]Total técnicas exitosas:[reset]\t{successful_techniques_count}\n"
        f"\n[b]Técnica más exitosa:[reset] {mat_str} ({max_freq} veces)\n"
        f"\n[b]Mitigación recomendada:[reset] {mit_str}\n",
        title="[b red]:old_key: TÉCNICAS",
        padding=(0, 1),
        border_style="red"
    )

    # Selección de color de barra en función de la gravedad
    if attack_severity <= 33:
        bar_color = "green"
        criticity = "Baja"
    elif attack_severity <= 66:
        bar_color = "yellow"
        criticity = "Media"
    else:
        bar_color = "red"
        criticity = "Alta"

    # Crear y mostrar la barra de gravedad del ataque con color condicional y centrada
    bar = Bar(size=100, begin=0, end=attack_severity, color=bar_color, bgcolor="black", width=40)
    criticity_text = Text(f"{attack_severity} - {criticity}")

    bar_panel = Panel(
        Align.center(
            Group(Align.center(criticity_text), "", Align.center(bar)),
            vertical="middle",
        ),
        padding=(1, 2),
        title="[b yellow]:warning: CRITICIDAD",
        border_style="yellow"
    )

    # Crear el layout
    layout = Layout()

    # Divide la pantalla en dos partes, con "secuencia_panel" en la parte superior y "main" en la parte inferior
    layout.split(
        Layout(secuencia_panel, size=5),  # Ajusta el tamaño para reducir el espacio
        Layout(name="main", ratio=1),    # Usa el resto del espacio para "main"
    )

    layout["main"].split_row(
        Layout(name="Statistics", ratio=1), 
        Layout(name="Defense", ratio=2)
    )
    
    # Divide el layout "Statistics" en dos partes verticales: "activos_panel" y "tecnicas_panel"
    layout["Defense"].split_column(
        Layout(defense_panel, ratio=3),
        Layout(bar_panel, ratio=1)
    )

    # Divide el layout "Statistics" en dos partes verticales: "activos_panel" y "tecnicas_panel"
    layout["Statistics"].split_column(
        Layout(activos_panel, ratio=1),
        Layout(tecnicas_panel, ratio=1)
    )

    # Generar un ID único para el ataque y almacenarlo en el histórico
    attack_id = f"Ataque-{random.randint(1000, 9999)}"
    scenario=cargar_escenario()
    save_attack_stats_csv(attack_id, scenario, maa_str, mat_str)

    from rich.live import Live
    # Mantener el layout visible usando Live
    with Live(layout, screen=True):
        input("Presiona Enter para salir...")

def save_attack_stats_csv(attack_id, scenario, most_affected_asset, most_recurrent_asset):
    # Verifica si el archivo ya existe para añadir encabezados solo en caso necesario
    file_exists = os.path.isfile('attack_history.csv')

    with open('attack_history.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            # Escribe los encabezados si el archivo se está creando
            writer.writerow(["ID Ataque", "Escenario", "Activo Más Afectado", "Técnica más exitosa", "Fecha de ejecución"])

        # Registra los datos del ataque
        writer.writerow([attack_id, scenario, most_affected_asset, most_recurrent_asset, str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))])
    
    print(f"[green][+][reset] Estadísticas del ataque {attack_id} guardadas en attack_history.csv.\n")

def display_attack_history_csv():
    try:
        df = pd.read_csv('attack_history.csv', skipinitialspace = True,quotechar='"')

        table = Table(title="Historial de ataques")
        rows = df.values.tolist()
        rows = [[str(el) for el in row] for row in rows]
        columns = df.columns.tolist()

        for column in columns:
            table.add_column(column)

        for row in rows:
            table.add_row(*row, style='cyan')

        print(Align.center(table))

    except FileNotFoundError:
        print("\n[red][+][reset] No se ha encontrado el archivo attack_history.csv. Ejecuta al menos un ataque para generar el historial.\n")

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

def guardar_escenario(escenario):
    with open('current_scenario.txt', "w") as file:
        file.write(str(escenario))

def cargar_escenario():
    try:
        with open('current_scenario.txt', "r") as file:
            return file.read()
    except FileNotFoundError:
        return 0

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
    password = "argos123"
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
    print("[yellow]\thistory:" + "[reset]\tMostrar historial de ataques.")
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
        techniques = load_techniques_json('tecnicas_completo.json')
        cves = load_cves_json('ttp_cwe_cve.json')
        cwes = load_cwes_json('ttp_cwe_cve.json')
        driver = start_neo4j()
        create_attack_graph(driver, chain, techniques, cves, cwes)
        link_attack_to_scenario(driver, chain, techniques, cves, cwes)
        close_neo4j(driver)
        exit(0)

    elif str(sys.argv[1]) == "clean":
        driver = start_neo4j()
        clean_database(driver)
        close_neo4j(driver)
        exit(0)
    
    elif str(sys.argv[1]) == "history":
        display_attack_history_csv()
        exit(0)

    else:
        print("[reset]No valid arguments were introduced")
        help()
        exit(0)

if __name__ == "__main__":
    main()
