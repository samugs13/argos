CREATE 
    (r:Activo:DispositivoSeguridad {
      name: 'Router', 
      ip: '192.168.0.1', 
      platform: 'Network', 
      permissions: ['Administrator'], 
      capabilities: ['Remote exploitation for execution requires a remotely accessible service reachable over the network or other vector of access such as spearphishing or drive-by compromise.', 'Network interface access and packet capture driver'] 
    }),

    (p:Activo:DispositivoRed {
      name: 'Printer', 
      ip: '192.168.0.100', 
      platform: 'Network', 
      permissions: ['User'], 
      capabilities: ['Active remote service accepting connections and valid credentials', 'Privileges to access network shared drive', 'Presence of physical medium or device'] 
    }),

    (st:Activo:DispositivoRed {
      name: 'SmartTV', 
      ip: '192.168.0.200', 
      platform: 'SaaS', 
      permissions: ['User'], 
      capabilities: ['Active remote service accepting connections and valid credentials', 'Privileges to access certain files and directories', 'Unpatched software or otherwise vulnerable target. Depending on the target and goal, the system and exploitable service may need to be remotely accessible from the internal network.' ] 
    }),

    (c:Activo:DispositivoRed {
      name: 'CCTV', 
      ip: '192.168.0.300', 
      platform: 'Network', 
      permissions: ['Administrator'], 
      capabilities: ['Remote exploitation for execution requires a remotely accessible service reachable over the network or other vector of access such as spearphishing or drive-by compromise.', 'Active remote service accepting connections and valid credentials', 'Network interface access and packet capture driver'] 
    }),

    (h:Activo:DispositivoRed {
      name: 'Hub', 
      ip: '192.168.0.400', 
      platform: 'IaaS', 
      permissions: ['Administrator'], 
      capabilities: ['Active remote service accepting connections and valid credentials', 'Network interface access and packet capture driver', 'Privileges to access directories, files, and API endpoints that store information of interest'] 
    }),

    (s:Activo:DispositivoRed {
      name: 'Smartphone', 
      ip: '192.168.0.500', 
      platform: 'macOS', 
      permissions: ['User'], 
      capabilities: ['Removable media allowed', 'Privileges to access removable media drive and files', 'Unpatched software or otherwise vulnerable target.']
    }),

    (t:Activo:DispositivoRed {
      name: 'Thermostat', 
      ip: '192.168.0.600', 
      platform: 'IaaS', 
      permissions: ['SYSTEM'], 
      capabilities: ['Active remote service accepting connections and valid credentials', 'Privileges to access directories, files, and API endpoints that store information of interest', 'Remote exploitation for execution requires a remotely accessible service reachable over the network or other vector of access such as spearphishing or drive-by compromise.']
    })

CREATE 
    (h)-[:CONEXION {protocolo: 'WPA2'}]->(r),
    (t)-[:CONEXION {protocolo: 'WPA2'}]->(r),
    (c)-[:CONEXION {protocolo: 'WPA2'}]->(r),
    (p)-[:CONEXION {protocolo: 'WPA2'}]->(r),
    (s)-[:CONEXION {protocolo: 'WPA2'}]->(r),
    (st)-[:CONEXION {protocolo: 'WPA2'}]->(r),
    (h)-[:CONEXION {puerto: 1883, protocolo: 'MQTT'}]->(t),
    (s)-[:CONEXION {puerto: 5000, protocolo: 'DLNA'}]->(st),
    (s)-[:CONEXION {puerto: 631, protocolo: 'IPP'}]->(p);
