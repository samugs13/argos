CREATE 
    (s:Activo:DispositivoRed {
      name: 'Smartphone', 
      ip: '192.168.0.100', 
      platform: 'Windows', 
      permissions: ['User'], 
      capabilities: ['Permissions to access directories'] 
    }),

    (t:Activo:DispositivoRed {
      name: 'Tablet', 
      ip: '192.168.0.200', 
      platform: 'Windows', 
      permissions: ['User'], 
      capabilities: ['Permissions to access directories'] 
    }),

    (r:Activo:DispositivoSeguridad {
      name: 'Router', 
      ip: '192.168.0.1', 
      platform: 'Network', 
      permissions: ['Administrator'], 
      capabilities: [''] 
    }),

    (c:Activo:DispositivoRed {
      name: 'SmartCamera', 
      ip: '192.168.0.30', 
      platform: 'SaaS', 
      permissions: ['Administrator'], 
      capabilities: [''], 
      cwe: ['CWE-284']
    }),

    (p:Activo:DispositivoRed {
      name: 'Printer', 
      ip: '192.168.0.30', 
      platform: 'SaaS', 
      permissions: ['Administrator'], 
      capabilities: [''], 
      cwe: ['CWE-284']
    }),

    (h:Activo:Aplicacion {
      name: 'SmartHub', 
      ip: '192.168.0.40', 
      platform: 'SaaS', 
      permissions: ['Administrator'], 
      capabilities: ['API endpoints that store information of interest'] 
    })

CREATE 
    (s)-[:CONEXION {protocolo: 'WPA2'}]->(r),
    (t)-[:CONEXION {protocolo: 'WPA2'}]->(r),
    (h)-[:CONEXION {puerto: 8883, protocolo: 'MQTT'}]->(p),
    (h)-[:CONEXION {puerto: 554, protocolo: 'RTSP'}]->(c),
    (r)-[:PROTECCION {tipo: 'Filtrado'}]->(h),
    (r)-[:PROTECCION {tipo: 'Filtrado'}]->(c);
