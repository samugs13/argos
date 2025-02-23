CREATE
    (u1:Activo:Usuario {
      name: 'Alice', 
      ip: '192.168.1.10', 
      platform: 'Windows', 
      permissions: ['User'], 
      capabilities: ['Permissions to access directories', 'Access to shared folders and content with write permissions', 'Presence of physical medium or device', 'Privileges to access certain files and directories', 'Privileges to access network shared drive', 'Privileges to access removable media drive and files'], 
      cve: ['CVE-2004-2227']
    }),

    (u2:Activo:Usuario {
      name: 'Bob', 
      ip: '192.168.1.11', 
      platform: 'Linux', 
      permissions: ['Administrator'], 
      capabilities: ['Permissions to access directories', 'Privileges to access network shared drive', 'Privileges to access removable media drive and files']
    }),

    (s1:Activo:Servidor {
      name: 'WebServer', 
      ip: '192.168.1.20', 
      platform: 'Windows', 
      permissions: ['Administrator'], 
      capabilities: ['Remote exploitation for execution requires a remotely accessible service', 'Active remote service accepting connections and valid credentials']
    }),

    (s2:Activo:Servidor {
      name: 'MailServer', 
      ip: '192.168.1.21', 
      platform: 'Linux', 
      permissions: ['Administrator'], 
      capabilities: ['Remote exploitation for execution requires a remotely accessible service', 'Active remote service accepting connections and valid credentials']
    }),

    (fw:Activo:DispositivoSeguridad {
      name: 'Firewall', 
      ip: '192.168.1.1', 
      platform: 'Network', 
      permissions: ['Administrator'], 
      capabilities: ['Network interface access and packet capture driver'] 
    }),

    (app1:Activo:Aplicacion {
      name: 'Apache', 
      ip: '192.168.1.30', 
      platform: 'Linux', 
      permissions: ['Administrator'], 
      capabilities: ['Privileges to access certain files and directories'] 
    })

CREATE 
    (u1)-[:CONEXION {protocolo: 'LDAP'}]->(s1),
    (u2)-[:CONEXION {protocolo: 'SMTP'}]->(s2),
    (s1)-[:CONEXION {puerto: 25, protocolo: 'SMTP'}]->(s2),
    (fw)-[:PROTECCION {tipo: 'Firewall'}]->(s1),
    (fw)-[:PROTECCION {tipo: 'Firewall'}]->(s2),
    (app1)-[:ALOJAMIENTO {entorno: 'WebServer'}]->(s1);
