# LocWeave

Para LocWeave se eligió Trunk-Based Development por las siguientes razones:

Frecuencia de despliegue esperada: el sistema requiere integraciones y despliegues frecuentes (nuevos extractores, mejoras en validaciones, soporte de formatos y ajustes de workflow). Trunk-Based permite mantener la rama principal siempre en estado desplegable e integrar cambios de forma continua, evitando la acumulación de trabajo que generan estrategias con ramas de larga duración.

Tamaño del equipo: Tres integrantes

Esta combinación de alta frecuencia de cambios, equipo reducido de tres personas y necesidad de un proceso de release liviano hace que Trunk-Based Development sea la estrategia más adecuada para LocWeave frente a alternativas más pesadas como GitFlow.

//MENSAJE DE GRUPO: Deben crearse su entorno propio para la mayoria de librerias usadas en el código, aquí la guia:
1. python -m venv venv

2. Si es en Git Bash o terminal normal: venv\Scripts\activate
   Si es en terminal de PowerShell: .\venv\Scripts\Activate.ps1
    
3. pip install -r requirements.txt