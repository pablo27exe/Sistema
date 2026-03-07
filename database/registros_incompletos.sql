-- Usuarios sin credencial
SELECT u.nombre_usuario 
FROM usuarios u
LEFT JOIN credenciales c ON c.usuario_id = u.id
WHERE c.id IS NULL;

-- Usuarios sin método de segundo factor
SELECT u.nombre_usuario 
FROM usuarios u
LEFT JOIN metodos_segundo_factor m ON m.usuario_id = u.id
WHERE m.id IS NULL;