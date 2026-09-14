INSERT INTO roles (code, name)
SELECT 'public', '普通员工'
WHERE NOT EXISTS (SELECT 1 FROM roles WHERE code = 'public');

SELECT code, name FROM roles WHERE code = 'public';
SELECT COUNT(*) AS permission_count FROM permissions;