# Jugador Autónomo para HEX (MCTS)

Proyecto universitario de Inteligencia Artificial: implementación de un jugador autónomo para el juego HEX usando **Monte Carlo Tree Search (MCTS)**.

## 1. Descripción del proyecto
El agente decide su jugada en `solution.py` mediante MCTS y devuelve una tupla `(row, col)` sobre un tablero NxN:
- `0` = casilla vacía
- `1` = mi jugador
- `2` = oponente

## 2. Estrategia utilizada
El agente aplica MCTS con:
- Selección UCT
- Simulaciones (rollouts)
- Retropropagación
- Control de tiempo (límite interno seguro de 4.5s)

Heurísticas ligeras añadidas:
- **Move Ordering** basado en centro y proximidad a fichas
- **Heurística de centro** (prioriza casillas más cercanas al centro)
- **Rollouts sesgados** (70% heurístico, 30% aleatorio)

## 3. Arquitectura del algoritmo
Fases MCTS implementadas:
1. **Selection**: mientras el nodo esté totalmente expandido y tenga hijos, se selecciona el hijo con mayor UCT.
2. **Expansion**: si hay movimientos no explorados, se expande uno.
3. **Simulation**: rollout hasta finalizar partida.
4. **Backpropagation**: se actualizan visitas y victorias hacia la raíz.

## 4. Restricciones del proyecto
- Todo el código del agente está en `solution.py`.
- Límite de tiempo por jugada: **5 segundos**.
- Prohibido leer/escribir archivos o usar internet durante `play()`.
- No se mantienen estados globales persistentes entre partidas.

## 5. Posibles mejoras futuras
- **Progressive Bias** en la fórmula UCT
- **Heurísticas de conexión** (distancia entre grupos)
- **Análisis de caminos** específico para HEX

## Uso básico
```python
from solution import SmartPlayer
from board import HexBoard

player = SmartPlayer(time_limit=4.0)
board = HexBoard(size=5)
move = player.play(board)
```

## Estructura requerida
```
solution.py
player.py
board.py
README.md
```
