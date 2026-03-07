SELECT 
    u.id              AS usuario_id,
    u.nombre,
    u.nombre_usuario,
    u.fecha_creacion,
    c.hash_contrasena,
    c.creado_en       AS credencial_creada,
    m.tipo            AS metodo,
    m.dato_factor,
    m.activo,
    m.registrado_en   AS metodo_registrado
FROM usuarios u
LEFT JOIN credenciales c         ON c.usuario_id = u.id
LEFT JOIN metodos_segundo_factor m ON m.usuario_id = u.id
ORDER BY u.fecha_creacion DESC;