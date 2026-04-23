# MTG Simulator — Mejoras v2.0

## 🎨 Mejoras Gráficas

### Menú Principal
- **Fondo dinámico**: Gradiente oscuro con campo de estrellas parpadeantes
- **Partículas de maná**: 80 partículas flotantes de colores W/U/B/R/G animadas
- **Halo de luz pulsante** detrás del logo
- **Iconos de maná orbitales** con 5 símbolos animados
- **Título con efecto de pulso dorado** y líneas decorativas laterales
- **Panel de botones con fondo semi-transparente** y bordes dorados
- **Panel de controles** rediseñado con columnas y tipografía mejorada

### Campo de Batalla (Playmat)
- **Gradiente temático**: verde oscuro para el jugador, azul/rojo para el oponente
- **Hexágono de vida dinámico**: cambia de color según % de vida restante
  - Verde (>50%), Naranja (25–50%), Rojo (<25%) con pulso de advertencia
- **Borde activo luminoso** (dorado brillante) indica de quién es el turno
- **Zonas con degradados** y etiquetas de texto actualizadas
- **Indicadores de biblioteca** con alerta roja cuando quedan <10 cartas

### Cartas
- **Botones con degradado** vertical y sombra proyectada
- **Efecto glow (halo)** al seleccionar una carta (dorado) u hover (azul)
- **Frames por color** de la carta: blanco, azul, negro, rojo, verde, multi
- **Área de arte** con gradiente interior en cartas sin imagen PNG
- **Barra de nombre** con fondo semiopaco del color del frame

### Indicador de Fases
- **Colores por fase** (azul=robo, rojo=combate, verde=principal, etc.)
- **Animación de pulso** en la fase activa con halo dorado exterior
- **Indicador de turno compacto** a la derecha con colores verde/rojo
- **Degradados** en todos los segmentos

### Pantalla de Fin de Juego
- **Victoria**: lluvia de confeti colorido animado
- **Derrota**: halo rojo pulsante
- **Fondo con degradado oscuro** y texto jerarquizado
- **Botones mejorados** con iconos

### Registro de Combate
- **Panel premium** con bordes y encabezado degradado
- **Mensajes coloreados** por tipo: rojo=daño/combate, azul=bloqueo, verde=maná
- **Scrollbar estilizada** con track y thumb diferenciados

## ⚡ Mejoras Funcionales

### HUD de Estadísticas (`StatsHUD`)
- Panel in-game con **cronómetro de partida** en tiempo real
- Contador de **turno actual**
- Registro de **daño total** infligido a cada jugador
- Contador de **criaturas caídas** en combate

### Barra de Estado Animada (`StatusBar`)
- Mensajes centrados con **fade-in / fade-out** suave
- **Tipos de mensaje**: info (azul), warning (naranja), combat (rojo), success (verde)
- **Pulso luminoso** en el borde del mensaje activo

### Sistema de Fuentes Mejorado
- Prioridad a fuentes serif (Palatino, Georgia) para estética MTG auténtica
- Nuevo tamaño `'title'` (72px) para pantallas especiales
- Fallbacks robustos por si no hay fuentes del sistema

### Arquitectura
- `draw_panel()`: función de panel semi-transparente reutilizable
- `draw_glow()`: halos de luz difusos con múltiples pasos
- `draw_rounded_rect_gradient()`: degradados verticales en cualquier rect
- `lerp_color()` / `alpha_color()` en colors.py
- Nueva paleta `MTG_*` centralizada con 10+ tokens de color temáticos
