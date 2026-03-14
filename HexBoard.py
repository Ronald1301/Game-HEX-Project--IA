class HexBoard:

    def __init__(self, size: int):
        self.size = size  # Tamaño N del tablero (NxN)
        self.board = [[0 for _ in range(size)] for _ in range(size)]
        # Matriz NxN (0=vacío, 1=Jugador1, 2=Jugador2)

    # CLONE
    def clone(self) -> "HexBoard":
        """Devuelve una copia profunda del tablero actual"""
        new_board = HexBoard(self.size)
        new_board.board = [row[:] for row in self.board]
        return new_board

    # PLACE PIECE
    def place_piece(self, row: int, col: int, player_id: int) -> bool:
        """Coloca una ficha si la casilla está vacía."""
        if 0 <= row < self.size and 0 <= col < self.size:
            if self.board[row][col] == 0:
                self.board[row][col] = player_id
                return True
        return False

    # CHECK CONNECTION (DFS)
    def check_connection(self, player_id: int) -> bool:
        """
        Jugador 1 conecta izquierda → derecha
        Jugador 2 conecta arriba → abajo
        """
        visited = set()
        stack = []

        # JUGADOR 1: izquierda a derecha
        if player_id == 1:
            for r in range(self.size):
                if self.board[r][0] == 1:
                    stack.append((r, 0))
                    visited.add((r, 0))

            target_col = self.size - 1

            while stack:
                r, c = stack.pop()

                if c == target_col:
                    return True

                for nr, nc in self.get_neighbors(r, c):
                    if (nr, nc) not in visited and self.board[nr][nc] == 1:
                        visited.add((nr, nc))
                        stack.append((nr, nc))

        # JUGADOR 2: arriba hacia abajo
        else:
            for c in range(self.size):
                if self.board[0][c] == 2:
                    stack.append((0, c))
                    visited.add((0, c))

            target_row = self.size - 1

            while stack:
                r, c = stack.pop()

                if r == target_row:
                    return True

                for nr, nc in self.get_neighbors(r, c):
                    if (nr, nc) not in visited and self.board[nr][nc] == 2:
                        visited.add((nr, nc))
                        stack.append((nr, nc))

        return False

    # Vecinos en even-r layout
    def get_neighbors(self, r, c):
        if r % 2 == 0:
            directions = [(-1, 0), (-1, -1), (0, -1),
                          (0, 1), (1, 0), (1, -1)]
        else:
            directions = [(-1, 0), (-1, 1), (0, -1),
                          (0, 1), (1, 0), (1, 1)]

        neighbors = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbors.append((nr, nc))

        return neighbors