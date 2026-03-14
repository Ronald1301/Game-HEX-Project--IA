# Jugador Autónomo para HEX (MCTS)

Proyecto universitario de IA: implementación de un jugador autónomo para HEX usando **Monte Carlo Tree Search (MCTS)**

## Descripción del proyecto
El agente decide una jugada en `solution.py` y devuelve una tupla `(row, col)` sobre un tablero NxN:
- `0` = casilla vacía
- `1` = mi jugador
- `2` = oponente

El ganador es quien conecta sus lados:
- Jugador 1: izquierda → derecha
- Jugador 2: arriba → abajo  
Conexiones válidas en las 6 direcciones (even‑r layout).

## Estructura y requisitos
- **Archivo principal**: `solution.py` (todo el agente está ahí)
- Importaciones requeridas:
  - `from player import Player`
  - `from board import HexBoard`
- Firma obligatoria:
  - `class SmartPlayer(Player):`
  - `def play(self, board: HexBoard) -> tuple:`
- Restricciones:
  - Sin lectura/escritura de archivos en `play()`
  - Sin uso de internet
  - Sin estado global persistente entre partidas
  - Tiempo máximo por jugada: **5s** (límite interno seguro 4.5s)

## Estrategia: MCTS + metaheurísticas ligeras
El agente usa MCTS con:
- **Selection** (UCT)
- **Expansion**
- **Simulation** (rollout)
- **Backpropagation**
- **Control de tiempo** (búsqueda limitada por tiempo)

### ¿Qué significa UCT?
UCT significa **Upper Confidence bound applied to Trees**.(Límite superior de confianza aplicado a los árboles.)  
Es la función que balancea **explotación** (elegir lo que más gana) y **exploración** (probar movimientos poco visitados).

**Fórmula UCT:**
```
UCT = (wins / visits) + C * sqrt( ln(parent_visits) / visits )
```
- `wins/visits`: tasa de victoria del nodo (explotación)
- `C * sqrt(...)`: término de exploración
- `C` suele ser √2

## Arquitectura del algoritmo
1. **Selection**: mientras el nodo esté totalmente expandido y tenga hijos, se elige el hijo con mayor UCT.
2. **Expansion**: si hay movimientos no explorados, se expande uno.
3. **Simulation**: se simula una partida hasta que termine.
4. **Backpropagation**: se actualizan visitas y victorias hacia la raíz.


## Heurísticas implementadas
- **Move Ordering**: antes de expandir, se priorizan las casillas con mejor puntaje heurístico (centro + proximidad a fichas).
- **Heurística de centro**: prioriza casillas cercanas al centro del tablero (distancia menor → mejor score).
- **Rollouts sesgados**: 70% elige movimiento heurístico y 30% aleatorio.
- **Proximidad local**: favorece movimientos adyacentes a fichas propias u oponentes.

## Complejidad (estimada)
Sea `N` el tamaño del tablero (NxN) y `M = N²`.
- **Selección**: proporcional a la profundidad y número de hijos (≈ `O(d · b)`).
- **Expansión**: ordenar movimientos `O(M log M)` y extraer el siguiente.
- **Simulación**: en cada rollout se pueden jugar hasta `M` jugadas; cada verificación de ganador es `O(N²)` → **`O(N⁴)` por rollout**.
- **Backpropagation**: `O(d)`.

En la práctica, el tiempo total está acotado por el límite de tiempo (≈ 4.5s), por lo que el número de iteraciones se ajusta automáticamente.

**Complejidad final incluyendo heurísticas**  
Las heurísticas agregan sobrecosto en:
- **Move Ordering**: `O(M log M)` al ordenar movimientos.
- **Rollouts sesgados**: evaluación heurística local `O(1)` por movimiento (vecinos constantes).

Por tanto, la complejidad dominante sigue siendo la simulación: **`O(N⁴)` por rollout**, y el tiempo total queda acotado por el límite de tiempo.

## Posibles mejoras futuras
- Progressive Bias en UCT
- Heurística de conexión (distancia entre grupos)
- Evaluación rápida de caminos para HEX
