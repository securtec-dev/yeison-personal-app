# Casa Yeison

Asistente financiero familiar móvil primero para registrar ingresos, gastos, facturas, inversiones en animales y producción diaria de huevos.

## Ejecutar localmente

```powershell
docker compose up -d --build
```

- Aplicación: http://localhost:5186
- API: http://localhost:8016/api/v1/
- Salud de la API: http://localhost:8016/health/
- PIN local inicial: `2580`

Para cambiar el PIN o configurar Claude, copia `.env.example` como `.env` y ajusta:

```env
APP_PIN=2580
CLAUDE_API_KEY=
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

La clave de Claude solo se consume en el backend. Si no está configurada, el sistema genera recomendaciones locales basadas en los movimientos registrados.

## Servicios Docker

- `frontend`: React + Nginx, puerto 5186.
- `backend`: Django REST + Gunicorn, puerto 8016.
- `db`: PostgreSQL.
- `redis`: cola y planificación.
- `worker`: tareas de salarios y recomendaciones.
- `scheduler`: ingresos automáticos y resumen diario de las 12:00 m.

Los salarios de Yeison y Camila son ₡180.000 cada uno y se agregan automáticamente los días 15 y 28. Todas las fechas y tareas usan `America/Costa_Rica`.

## Seguridad y consistencia

- PIN almacenado mediante hash, no como texto legible.
- Límite de intentos de acceso y escaneos.
- Token privado para consumir la API.
- Idempotencia mediante `Idempotency-Key`.
- Transacciones atómicas y estados pendiente/completado/cancelado.
- Auditoría de operaciones financieras.
- Consultas con `select_related` y agregaciones para evitar N+1.
- Validación de tamaño y tipo de imágenes.

## Railway

El `Dockerfile` de la raíz construye React y Django en una sola aplicación web para producción. Railway usa además servicios separados del mismo repositorio para Celery worker y scheduler.

Variables requeridas en producción:

- `DATABASE_URL`: referencia privada al PostgreSQL de Railway.
- `REDIS_URL`: referencia privada al Redis de Railway.
- `DJANGO_SECRET_KEY`: valor aleatorio y exclusivo de producción.
- `APP_PIN`: PIN privado de 4 dígitos.
- `DJANGO_ALLOWED_HOSTS`: dominio público de Railway.
- `CSRF_TRUSTED_ORIGINS`: URL pública HTTPS.
- `CLAUDE_API_KEY`: opcional; nunca debe guardarse en Git.

El repositorio no contiene claves privadas. Los pushes a la rama `main` pueden activar despliegues automáticos en los servicios conectados.
