# anti_sleep

Script simple para evitar el reposo moviendo el mouse si no hay actividad.

## Uso rápido

```bash
pip install -r requirements.txt

# Normal (requiere permisos del SO)
python scripts/anti_sleep.py --idle 120 --interval 30 --pixels 1 --verbose

# Pruebas / Codespaces (no mueve mouse real)
python scripts/anti_sleep.py --idle 10 --interval 5 --dry-run --verbose
