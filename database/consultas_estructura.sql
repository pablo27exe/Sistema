----------------------------CONSULTAS DE ESTRUCTURA
SELECT *
FROM information_schema.columns
WHERE table_name = 'usuarios'
ORDER BY ordinal_position;

SELECT * 
FROM information_schema.columns
WHERE table_name = 'credenciales'
ORDER BY ordinal_position;

SELECT * 
FROM information_schema.columns
WHERE table_name = 'metodos_segundo_factor'
ORDER BY ordinal_position;