
# 🃏 MTG Simulator

<div align="center">



!\[Python](https://img.shields.io/badge/Python-3.8+-blue.svg)

!\[Pygame](https://img.shields.io/badge/Pygame-2.5.0-green.svg)

!\[License](https://img.shields.io/badge/License-MIT-yellow.svg)

!\[Status](https://img.shields.io/badge/Status-En%20Desarrollo-orange.svg)



\*\*Un simulador de duelo de Magic: The Gathering desarrollado en Python con Pygame\*\*



\[Características](#-características) • \[Instalación](#-instalación) • \[Cómo Jugar](#-cómo-jugar) • \[Estructura](#-estructura-del-proyecto) • \[Capturas](#-capturas-de-pantalla)



</div>



\---



\## 🎮 Características



\### Jugabilidad

\- ✅ \*\*Sistema de turnos completo\*\* con todas las fases (mantenimiento, robo, principal, combate, final)

\- ✅ \*\*Combate completo\*\*: declarar atacantes, asignar bloqueadores, resolución de daño

\- ✅ \*\*Sistema de maná\*\*: gira tierras para obtener maná de diferentes colores

\- ✅ \*\*Mazos personalizables\*\*: crea y guarda tus propios mazos de 60 cartas

\- ✅ \*\*IA oponente\*\*: juega contra una inteligencia artificial básica

\- ✅ \*\*Habilidades de cartas\*\*: Vuela, Prisa, habilidades activadas y disparadas



\### Interfaz

\- ✅ \*\*Playmat estilo MTG Arena\*\* con zonas diferenciadas

\- ✅ \*\*Cartas en alta resolución\*\* con imágenes PNG

\- ✅ \*\*Animaciones suaves\*\*: rotación de cartas, maná flotante, despliegue de manos

\- ✅ \*\*Manos semiescondidas\*\* que se despliegan al hacer hover

\- ✅ \*\*Tooltips\*\* con imagen ampliada de la carta al pasar el cursor

\- ✅ \*\*Registro de partida\*\* con todo el historial de acciones



\### Técnico

\- ✅ \*\*Arquitectura modular\*\* fácil de extender

\- ✅ \*\*Sistema de logging\*\* completo para depuración

\- ✅ \*\*Gestión de imágenes\*\* con caché para rendimiento

\- ✅ \*\*Sistema de animaciones\*\* basado en tiempo real



\---



\## 🚀 Instalación



\### Requisitos previos

\- Python 3.8 o superior

\- pip (gestor de paquetes de Python)



\### Pasos de instalación



1\. \*\*Clonar el repositorio\*\*

```bash

git clone https://github.com/Robmoru23/MTG\_Simulator.git

cd MTG\_Simulator

```



2\. \*\*Instalar dependencias\*\*

```bash

pip install -r requirements.txt

```



3\. \*\*Ejecutar el juego\*\*

```bash

python main.py

```



\### Crear un ejecutable (opcional)

```bash

pip install pyinstaller

pyinstaller --onefile --windowed --name "MTG\_Simulator" main.py

```



\---



\## 🎯 Cómo Jugar



\### Controles básicos



| Acción | Control |

|--------|---------|

| Jugar tierra/criatura/hechizo | Clic izquierdo en la carta de la mano |

| Girar tierra para maná | Clic izquierdo en la tierra en el campo |

| Seleccionar atacante | Clic izquierdo en tu criatura (en fase de ataque) |

| Seleccionar bloqueador | Clic en atacante rival → clic en tu criatura |

| Activar habilidad de criatura | Clic izquierdo en la criatura (ej: Llanowar Elves) |

| Avanzar fase | `ESPACIO` |

| Volver al menú | `ESC` |

| Pantalla completa | `F11` |



\### Flujo del juego



1\. \*\*Fase de mantenimiento\*\*: se enderezan todas tus cartas

2\. \*\*Fase de robo\*\*: robas una carta

3\. \*\*Fase principal\*\*: juegas tierras, criaturas y hechizos

4\. \*\*Fase de combate\*\*:

&#x20;  - Declarar atacantes: selecciona tus criaturas (clic en ellas)

&#x20;  - Presiona `ESPACIO` para confirmar atacantes

&#x20;  - Declarar bloqueadores: clic en atacante rival → clic en tu criatura

&#x20;  - Presiona `ESPACIO` para confirmar bloqueos y resolver daño

5\. \*\*Segunda fase principal\*\*: juegas más cartas si deseas

6\. \*\*Fase final\*\*: descartas si tienes más de 7 cartas



\---



\## 📁 Estructura del Proyecto



```

MTG\_Simulator/

├── main.py                 # Punto de entrada

├── core/                   # Lógica central del juego

│   ├── card.py            # Clase Card y definición de cartas

│   ├── game\_core.py       # Clases Player y Game

│   └── config.py          # Configuración global

├── ui/                     # Interfaz de usuario

│   ├── screens/           # Pantallas del juego

│   │   ├── menu\_screen.py

│   │   ├── game\_screen.py

│   │   ├── deck\_list\_screen.py

│   │   └── deck\_builder\_screen.py

│   ├── widgets/           # Componentes reutilizables

│   └── draw\_utils.py      # Funciones de dibujo

├── managers/              # Gestores de recursos

│   ├── deck\_manager.py    # Guardado/carga de mazos

│   └── image\_manager.py   # Caché de imágenes

├── assets/                # Recursos del juego

│   └── cards\_imgs/        # Imágenes de cartas (PNG)

├── decks/                 # Mazos guardados (JSON)

└── utils/                 # Utilidades varias

```



\---



\## 🛠️ Próximas Mejoras



\- \[ ] Más cartas y expansiones

\- \[ ] Efectos de sonido y música

\- \[ ] IA más avanzada

\- \[ ] Modo multijugador local

\- \[ ] Guardado y carga de partidas

\- \[ ] Sistema de logros

\- \[ ] Editor de cartas



\---



\## 🤝 Contribuciones



Las contribuciones son bienvenidas. Para cambios importantes:



1\. Fork el proyecto

2\. Crea tu rama de características (`git checkout -b feature/AmazingFeature`)

3\. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)

4\. Push a la rama (`git push origin feature/AmazingFeature`)

5\. Abre un Pull Request



\---



\## 📝 Licencia



Distribuido bajo la licencia MIT. Ver `LICENSE` para más información.



\---



\## 📧 Contacto



\*\*Autor\*\*: Robmoru23

\*\*GitHub\*\*: \[https://github.com/Robmoru23](https://github.com/Robmoru23)

\*\*Proyecto\*\*: \[https://github.com/Robmoru23/MTG\_Simulator](https://github.com/Robmoru23/MTG\_Simulator)



\---



\## 🙏 Agradecimientos



\- Wizards of the Coast por el juego Magic: The Gathering

\- La comunidad de Pygame por la excelente documentación

\- Todos los contribuyentes y testers del proyecto



\---



<div align="center">

&#x20; <sub>Built with ❤️ using Python and Pygame</sub>

</div>

```

