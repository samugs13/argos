CREATE 
    (s:Activo:DispositivoRed {
      name: 'Sensor', 
      ip: '10.0.1.10', 
      platform: 'PRE', 
      permissions: ['User'], 
      capabilities: ['Presence of physical medium or device', 'Privileges to access certain files and directories']
    }),

    (a:Activo:DispositivoRed {
      name: 'Actuator', 
      ip: '10.0.1.20', 
      platform: 'PRE', 
      permissions: ['User'], 
      capabilities: ['Presence of physical medium or device', 'Privileges to access certain files and directories']
    }),

    (hmi:Activo:DispositivoRed {
      name: 'HMI', 
      ip: '10.0.1.30', 
      platform: 'Windows', 
      permissions: ['Administrator'], 
      capabilities: ['Access to shared folders and content with write permissions', 'Microsoft Core XML Services (MSXML) or access to wmic.exe']
    }),

    (plc:Activo:DispositivoRed {
      name: 'PLC', 
      ip: '10.0.1.40', 
      platform: 'PRE', 
      permissions: ['Administrator'], 
      capabilities: ['Access to shared folders and content with write permissions', 'Autorun enabled or vulnerability present that allows for code execution', 'Unpatched software or otherwise vulnerable target. Depending on the target and goal, the system and exploitable service may need to be remotely accessible from the internal network.'],
      cve: 'CVE-2022-29519'
    }),

    (cdb:Activo:DispositivoRed {
      name: 'CloudDB', 
      ip: '10.0.1.50', 
      platform: 'SaaS', 
      permissions: ['Administrator'], 
      capabilities: ['API endpoints that store information of interest', 'Permissions to access directories, files, and API endpoints that store information of interest']
    }),

    (fw:Activo:DispositivoSeguridad {
      name: 'Firewall', 
      ip: '10.0.1.1', 
      platform: 'Network', 
      permissions: ['Administrator'], 
      capabilities: ['Network interface access and packet capture driver']
    })

CREATE 
    (plc)-[:CONEXION {protocolo: 'Modbus'}]->(a),
    (s)-[:CONEXION {protocolo: 'Modbus'}]->(plc),
    (hmi)-[:CONEXION {protocolo: 'Modbus'}]->(plc),
    (plc)-[:CONEXION {puerto: '1883', protocolo: 'MQTT'}]->(cdb),
    (fw)-[:PROTECCION {tipo: 'Firewall'}]->(plc),
    (fw)-[:PROTECCION {tipo: 'Firewall'}]->(cdb);
