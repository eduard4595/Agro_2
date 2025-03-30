# Agro-CIDATMEX Flask Project

Este proyecto Flask incluye módulos para análisis financiero, análisis 
climático, un chat basado en IA y gestión de usuarios.

## Instrucciones para ejecutar

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt

2. Ejecutar la aplicación:
``` python run.py ```
3. Acceder a la aplicación en http://127.0.0.1:5000.



## Para migrar la base de datos cuando cambia el modelo de datos
```python manage.py db init```
```python manage.py db migrate -m "Create GeneralDataCafe table"```
```python manage.py db upgrade```
