CREATE 
    (eng1:Activo:Usuario {
      name: 'Ingeniero1', 
      ip: '10.0.1.10', 
      platform: 'Windows', 
      permissions: ['Administrator'], 
      capabilities: ['Active remote service accepting connections and valid credentials']
    }),

    (scada:Activo:Servidor {
      name: 'SCADA', 
      ip: '10.0.1.20', 
      platform: 'Windows', 
      permissions: ['Administrator'], 
      capabilities: ['Kerberos authentication enabled']
    }),

    (plc:Activo:Aplicacion {
      name: 'PLC_Control', 
      ip: '10.0.1.30', 
      platform: 'PRE', 
      permissions: ['Administrator'], 
      capabilities: ['Access to shared folders and content with write permissions']
    }),

    (hist:Activo:Aplicacion {
      name: 'HistorianDB', 
      ip: '10.0.1.40', 
      platform: 'Windows', 
      permissions: ['Administrator'], 
      capabilities: ['API endpoints that store information of interest']
    }),

    (fw:Activo:DispositivoSeguridad {
      name: 'IndustrialFirewall', 
      ip: '10.0.1.1', 
      platform: 'Network', 
      permissions: ['Administrator'], 
      capabilities: ['']
    })

CREATE 
    (eng1)-[:AUTENTICACION {protocolo: 'Kerberos'}]->(scada),
    (scada)-[:CONEXION {puerto: 4840, protocolo: 'OPC-UA'}]->(plc),
    (scada)-[:CONEXION {puerto: 1433, protocolo: 'SQL'}]->(hist),
    (fw)-[:PROTECCION {tipo: 'Firewall'}]->(scada),
    (fw)-[:PROTECCION {tipo: 'Firewall'}]->(plc);
