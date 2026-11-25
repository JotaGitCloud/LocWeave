# ADR 006 — Comunicación en la versión de escritorio

**Estado:** aceptada · **Relación con el ADR 003:** acota su alcance para la primera versión.

## Contexto
El ADR 003 define una estrategia híbrida (REST síncrono, eventos asíncronos y webhooks) pensada para componentes
distribuidos y herramientas externas. La versión entregable de LocWeave es una **aplicación de escritorio de un solo
proceso**: no hay servidor, red ni infraestructura que operar, algo coherente con un equipo de tres personas y usuarios
indie sin recursos.

## Decisión
- **Comunicación síncrona dentro del proceso:** la interfaz (y la CLI) llaman a la fachada `LocWeaveService`; no hay
  llamadas de red entre componentes.
- **Tareas largas en segundo plano:** importar, traducir por lote y exportar se ejecutan en un hilo de trabajo
  (`QThread`) y notifican **progreso, éxito, error y cancelación mediante señales**. Es el equivalente local de la
  cola de eventos y de consultar el estado de una tarea del ADR 003.
- **Contrato estable:** los métodos públicos de `LocWeaveService` (importar, traducir, validar, exportar, glosario)
  son el contrato interno; la CLI demuestra que cualquier otro cliente puede usarlo.
- **REST, webhooks y cola de mensajes:** quedan diferidos. Cuando se necesiten (plugin para motores de juego, CI del
  desarrollador), se expondrá la misma fachada con una API REST sin cambiar el núcleo.

## Consecuencias
- **Positivas:** cero infraestructura, pruebas sencillas, funcionamiento sin conexión.
- **Negativas:** no hay integración remota ni uso multiusuario hasta implementar la API prevista en el ADR 003.
- **Alineación:** se mantiene el principio del ADR 003 (trabajo largo sin bloquear al usuario, estados de tarea
  explícitos, contratos claros); solo cambia el mecanismo, de red a señales dentro del proceso.
