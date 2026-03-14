"""
Solución MCTS para jugar HEX - Ronald Provance Valladares

Este módulo implementa un jugador inteligente basado en Monte Carlo Tree Search (MCTS)
que hereda de la clase Player y utiliza la clase HexBoard proporcionada(SmartPlayer)
"""

import math
import random
import time
from typing import Optional, List, Tuple
from collections import deque
from player import Player
from board import HexBoard


CENTER_WEIGHT = 1.2
ADJ_OWN_WEIGHT = 1.0
ADJ_OPP_WEIGHT = 0.7
ROLLOUT_BIAS_PROB = 0.7


def get_valid_moves(board: HexBoard) -> List[Tuple[int, int]]:
    """Lista de celdas vacías como tuplas (row, col)."""
    moves = []
    for r in range(board.size):
        for c in range(board.size):
            if board.board[r][c] == 0:
                moves.append((r, c))
    return moves


def apply_move(board: HexBoard, move: Tuple[int, int], player_id: int) -> None:
    """Aplica un movimiento o lanza ValueError si no es válido."""
    row, col = move
    if not board.place_piece(row, col, player_id):
        raise ValueError(f"Movimiento inválido: {move}")


def move_heuristic(board: HexBoard, move: Tuple[int, int], player_id: int) -> float:
    """
    Heurística ligera para priorizar movimientos:
    - Cercanía al centro
    - Proximidad a fichas propias
    - Proximidad a fichas del oponente
    """
    r, c = move
    size = board.size
    center = (size - 1) / 2.0
    dist_center = abs(r - center) + abs(c - center)
    score = -CENTER_WEIGHT * dist_center

    opponent = 2 if player_id == 1 else 1
    for nr, nc in MCTSSimulator._get_hex_neighbors(r, c, size):
        if board.board[nr][nc] == player_id:
            score += ADJ_OWN_WEIGHT
        elif board.board[nr][nc] == opponent:
            score += ADJ_OPP_WEIGHT

    return score


def order_moves(board: HexBoard, moves: List[Tuple[int, int]], player_id: int) -> List[Tuple[int, int]]:
    """Ordena movimientos por heurística (mayor puntaje primero)."""
    return sorted(moves, key=lambda m: move_heuristic(board, m, player_id), reverse=True)


def select_rollout_move(board: HexBoard, moves: List[Tuple[int, int]], player_id: int) -> Tuple[int, int]:
    """Rollout sesgado: 70% heurístico, 30% aleatorio."""
    if not moves:
        return (0, 0)
    if random.random() < ROLLOUT_BIAS_PROB:
        return max(moves, key=lambda m: move_heuristic(board, m, player_id))
    return random.choice(moves)

class MCTSNode:
    """
    Nodo del árbol MCTS.
    
    Almacena:
    - board: estado del tablero
    - parent: nodo padre
    - children: diccionario de nodos hijos {movimiento -> nodo}
    - move: movimiento que llevó a este nodo
    - player: jugador que debe jugar en este nodo
    - visits: número de veces visitado
    - wins: número de victorias acumuladas
    - untried_moves: movimientos no expandidos aún
    """
    
    def __init__(
        self,
        board: HexBoard,
        move: Optional[Tuple[int, int]] = None,
        parent: Optional["MCTSNode"] = None,
        player: int = 1
    ):
        self.board = board.clone()
        self.move = move
        self.parent = parent
        self.children = {}
        self.visits = 0
        self.wins = 0
        self.player = player  # Jugador que debe jugar desde este nodo
        self.untried_moves = order_moves(
            board,
            get_valid_moves(board),
            player
        )
    
    def uct_value(self, exploration: float = math.sqrt(2)) -> float:
        """
        Calcula el valor UCT (Upper Confidence bound for Trees).
        
        Fórmula: wins/visits + C * sqrt(ln(parent_visits) / visits)
        
        Esto balancea explotación (ganar) y exploración (incertidumbre).
        """
        if self.visits == 0:
            return float('inf')
        
        exploitation = self.wins / self.visits
        exploration_term = exploration * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )
        return exploitation + exploration_term
    
    def is_fully_expanded(self) -> bool:
        """Retorna True si todos los movimientos han sido intentados."""
        return len(self.untried_moves) == 0
    
    def select_child(self, exploration: float) -> "MCTSNode":
        """Selecciona el hijo con mayor valor UCT."""
        return max(self.children.values(), key=lambda c: c.uct_value(exploration))


class MCTSSimulator:
    """
    Manejador de simulaciones y detección de ganador para MCTS.
    """
    
    @staticmethod
    def check_winner(board: HexBoard) -> int:
        """
        Verifica si hay un ganador en el tablero actual.
        """
        size = len(board.board)
        
        # Verificar si Jugador 1 conecta izquierda-derecha
        if MCTSSimulator._connects_horizontally(board, 1):
            return 1
        
        # Verificar si Jugador 2 conecta arriba-abajo
        if MCTSSimulator._connects_vertically(board, 2):
            return 2
        
        return 0
    
    @staticmethod
    def _connects_horizontally(board: HexBoard, player: int) -> bool:
        """Verifica si el jugador conecta de izquierda a derecha."""
        size = len(board.board)
        visited = [[False] * size for _ in range(size)]
        queue = deque()
        
        # Inicializar: buscar celdas del jugador en la columna 0
        for r in range(size):
            if board.board[r][0] == player:
                queue.append((r, 0))
                visited[r][0] = True
        
        # BFS hasta alcanzar la columna size-1
        while queue:
            r, c = queue.popleft()
            if c == size - 1:
                return True
            
            # Explorar vecinos en HEX
            for nr, nc in MCTSSimulator._get_hex_neighbors(r, c, size):
                if not visited[nr][nc] and board.board[nr][nc] == player:
                    visited[nr][nc] = True
                    queue.append((nr, nc))
        
        return False
    
    @staticmethod
    def _connects_vertically(board: HexBoard, player: int) -> bool:
        """Verifica si el jugador conecta de arriba hacia abajo."""
        size = len(board.board)
        visited = [[False] * size for _ in range(size)]
        queue = deque()
        
        # Inicializar: buscar celdas del jugador en la fila 0
        for c in range(size):
            if board.board[0][c] == player:
                queue.append((0, c))
                visited[0][c] = True
        
        # BFS hasta alcanzar la fila size-1
        while queue:
            r, c = queue.popleft()
            if r == size - 1:
                return True
            
            # Explorar vecinos en HEX
            for nr, nc in MCTSSimulator._get_hex_neighbors(r, c, size):
                if not visited[nr][nc] and board.board[nr][nc] == player:
                    visited[nr][nc] = True
                    queue.append((nr, nc))
        
        return False
    
    @staticmethod
    def _get_hex_neighbors(row: int, col: int, size: int) -> List[Tuple[int, int]]:
        """
        Retorna los 6 vecinos de una celda en el tablero HEX usando even-r layout.
        
        En el esquema even-r:
        - Filas pares están desplazadas a la derecha
        - Los desplazamientos de vecinos varían según la paridad de la fila
        """
        neighbors = []
        
        # Desplazamientos según la paridad de la fila
        if row % 2 == 0:  # Fila par
            deltas = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)]
        else:  # Fila impar
            deltas = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1)]
        
        for dr, dc in deltas:
            nr, nc = row + dr, col + dc
            if 0 <= nr < size and 0 <= nc < size:
                neighbors.append((nr, nc))
        
        return neighbors
    
    @staticmethod
    def simulate_random_game(board: HexBoard, current_player: int) -> int:
        """
        Ejecuta una simulación aleatoria desde el estado actual del tablero
        hasta encontrar un ganador.
        """
        # Clonar el tablero para no modificar el original
        sim_board = board.clone()
        player = current_player
        
        # Simular hasta encontrar ganador o llenar el tablero
        max_iterations = len(sim_board.board) * len(sim_board.board)
        for _ in range(max_iterations):
            # Obtener movimientos válidos
            valid_moves = get_valid_moves(sim_board)
            if not valid_moves:
                break
            
            # Rollout sesgado: heurístico con probabilidad 70%
            move = select_rollout_move(sim_board, valid_moves, player)
            apply_move(sim_board, move, player)
            
            # Verificar si hay ganador
            winner = MCTSSimulator.check_winner(sim_board)
            if winner != 0:
                return winner
            
            # Cambiar de jugador
            player = 2 if player == 1 else 1
        
        # Si no hay ganador después de llenar el tablero
        # retorna el ganador conocido (0 en caso de empate)
        return MCTSSimulator.check_winner(sim_board)


class MCTSTree:
    """
    Árbol de búsqueda MCTS.
    
    Gestiona el árbol completo y ejecuta los 4 pasos de MCTS:
    1. Selection: Recorre el árbol
    2. Expansion: Expande un nodo
    3. Simulation: Juega un juego aleatorio
    4. Backpropagation: Actualiza estadísticas
    """
    
    def __init__(
        self,
        board: HexBoard,
        player: int,
        exploration: float = math.sqrt(2)
    ):
        self.root = MCTSNode(board, player=player)
        self.exploration = exploration
        self.simulator = MCTSSimulator()
    
    def search(self, time_limit: float) -> None:
        """
        Ejecuta búsqueda MCTS durante el tiempo especificado.
        """
        start_time = time.time()
        iterations = 0
        
        while time.time() - start_time < time_limit:
            # Fase 1: Selection
            node = self._select_node(self.root)

            # Fase 2: Expansion
            if not node.is_fully_expanded():
                node = self._expand_node(node)
                if __debug__ and self.root.untried_moves:
                    # Verificación interna: la raíz debe empezar a tener hijos
                    assert self.root.children

            # Fase 3: Simulation
            winner = self.simulator.simulate_random_game(
                node.board,
                2 if node.player == 1 else 1
            )

            # Fase 4: Backpropagation
            self._backpropagate(node, winner)

            iterations += 1
        
        # Debug: mostrar información de búsqueda (opcional)
        # print(f"Iteraciones MCTS: {iterations}")
    
    def _select_node(self, node: MCTSNode) -> MCTSNode:
        """
        Fase 1: Selection.
        Recorre el árbol usando UCT hasta llegar a una hoja no totalmente expandida.
        """
        while node.is_fully_expanded() and node.children:
            node = node.select_child(self.exploration)
        return node
    
    def _expand_node(self, node: MCTSNode) -> MCTSNode:
        """
        Fase 2: Expansion.
        Expande un movimiento no intentado y retorna el nuevo nodo hijo.
        """
        # Seleccionar el mejor movimiento no intentado (ordenado por heurística)
        move = node.untried_moves.pop(0)
        
        # Crear nuevo nodo hijo
        child_board = node.board.clone()
        apply_move(child_board, move, node.player)
        
        # Siguiente jugador
        next_player = 2 if node.player == 1 else 1
        
        child_node = MCTSNode(
            child_board,
            move=move,
            parent=node,
            player=next_player
        )
        
        node.children[move] = child_node
        if __debug__:
            # Verificación interna: el hijo debe quedar registrado
            assert move in node.children
        return child_node
    
    def _backpropagate(self, node: MCTSNode, winner: int) -> None:
        """
        Fase 4: Backpropagation.
        Actualiza los contadores de visitas y victorias subiendo el árbol.
        """
        while node is not None:
            node.visits += 1
            
            # Contar como victoria si el jugador que jugó en este nodo ganó
            # Recordar que en node.player está el jugador que juega DESDE ese nodo
            # pero la victoria es del que jugó PARA LLEGAR a ese nodo
            parent_player = 2 if node.player == 1 else 1
            
            if winner == parent_player:
                node.wins += 1
            
            node = node.parent
    
    def get_best_move(self) -> Tuple[int, int]:
        """
        Retorna el movimiento con más visitas (mejor explorado).
        
        Este es generalmente mejor que elegir por valor UCT en el root,
        porque se basa en la exploración real del árbol.
        """
        if not self.root.children:
            # Si no hay hijos, retornar un movimiento aleatorio
            moves = get_valid_moves(self.root.board)
            return random.choice(moves) if moves else (0, 0)
        
        # Elegir el hijo con más visitas
        best_child = max(
            self.root.children.values(),
            key=lambda c: c.visits
        )
        return best_child.move
    
    def best_move(self) -> Tuple[int, int]:
        """
        Alias para get_best_move para compatibilidad.
        """
        return self.get_best_move()


class SmartPlayer(Player):
    """
    Jugador inteligente basado en MCTS
    """
    
    def __init__(self, time_limit: float = 4.0):
        
        # Asegurar que el tiempo no exceda 5 segundos (requisito)
        self.time_limit = min(time_limit, 4.5)
        self.exploration_constant = math.sqrt(2)
    
    def play(self, board: HexBoard) -> Tuple[int, int]:
        """
        Ejecuta MCTS para encontrar el mejor movimiento.
        """
        # Identificar nuestro jugador
        # Contamos las piedras para determinar si somos el jugador 1 o 2
        player_1_count = sum(
            1 for row in board.board for cell in row if cell == 1
        )
        player_2_count = sum(
            1 for row in board.board for cell in row if cell == 2
        )
        
        # Si hay igual cantidad de piedras o ambas son 0, comenzó el jugador 1
        # Si player 1 tiene más, es turno del jugador 2
        our_player = 2 if player_1_count > player_2_count else 1
        
        # Crear árbol MCTS y ejecutar búsqueda
        tree = MCTSTree(
            board,
            player=our_player,
            exploration=self.exploration_constant
        )
        
        # Ejecutar búsqueda por tiempo limitado
        tree.search(self.time_limit)
        
        # Retornar el mejor movimiento encontrado
        move = tree.get_best_move()
        print(f"SmartPlayer elige movimiento: {move} (Jugador {our_player})")
        return move
