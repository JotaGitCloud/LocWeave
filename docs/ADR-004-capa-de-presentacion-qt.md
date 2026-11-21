# ADR 004 — Capa de presentación con Qt (PySide6)

**Estado:** aceptada

## Contexto
La primera versión de la interfaz usaba CustomTkinter. Tkinter no ofrece animaciones, sombras ni hojas de
estilo, y su tabla estándar es difícil de personalizar, lo que limitaba el acabado visual definido en la
maqueta (tema claro/oscuro, pastillas de estado, variables resaltadas, avisos animados).

## Decisión
Reemplazar únicamente la capa de presentación por **PySide6 (Qt for Python)**: hojas de estilo QSS, tabla
basada en modelo/vista con delegados de dibujo, animaciones de propiedades y soporte de pantallas de alta
densidad. Se elige PySide6 y no PyQt6 por su licencia LGPL, que permite distribuir el ejecutable sin
obligaciones adicionales.

## Consecuencias
- **Sin cambios en el núcleo:** el Pipeline, los manejadores de formato, los proveedores, la validación y la
  persistencia no se tocaron. La interfaz solo depende de `LocWeaveService`, por lo que la presentación es una
  capa reemplazable (la CLI es la prueba: usa la misma fachada).
- Las tareas largas se ejecutan en hilos (`QThread`) y se comunican con la interfaz mediante señales.
- El ejecutable de Windows pesa más (Qt + Argos); se mitiga excluyendo los módulos de Qt que no se usan.
- Dependencia nueva: `PySide6`; se retira `customtkinter`.

## Alternativas consideradas
- Mantener CustomTkinter: más ligero, pero sin animaciones y con una tabla poco flexible.
- Interfaz web local (Electron/Tauri): mejor acabado, pero obliga a otra pila tecnológica y complica el motor
  de traducción local en Python.
