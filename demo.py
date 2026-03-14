"""
DEMO - Interfaz gráfica (Flet) para el juego HEX con MCTS
"""

import asyncio
import time
from typing import Dict, Tuple

import flet as ft

from solution import SmartPlayer, MCTSSimulator
from HexBoard import HexBoard


CellKey = Tuple[int, int]


class HexApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.size = 5
        self.time_limit = 4.0
        self.mode = "human_vs_ai"  # human_vs_ai | ai_vs_ai
        self.current_player = 1
        self.board = HexBoard(self.size)
        self.players = {
            1: SmartPlayer(time_limit=self.time_limit),
            2: SmartPlayer(time_limit=self.time_limit),
        }
        self.game_started = False
        self.ai_delay_s = self._calc_ai_delay_s()
        self.ai_loop_task: asyncio.Task | None = None
        self.ai_loop_running = False

        self.cell_size = 48
        self.col_spacing = 6
        self.row_spacing = 6
        self.cells: Dict[CellKey, ft.Container] = {}
        self.cell_texts: Dict[CellKey, ft.Text] = {}

        self.status_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color="#2d7dd2")
        self.turn_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color="#1f2a44")

        self._build_ui()
        self._reset_game()

    def _is_ai_vs_ai_mode(self) -> bool:
        value = str(self.mode).lower()
        return value == "ai_vs_ai" or "ia vs ia" in value

    def _is_human_vs_ai_mode(self) -> bool:
        return not self._is_ai_vs_ai_mode()

    # -----------------------------
    # UI
    # -----------------------------
    def _build_ui(self) -> None:
        self.page.title = "HEX - MCTS"
        self.page.window_width = 1100
        self.page.window_height = 760
        self.page.padding = 24
        self.page.bgcolor = "#f5f2eb"
        self.page.theme = ft.Theme(font_family="Trebuchet MS")

        title = ft.Text(
            "HEX · MCTS",
            size=28,
            weight=ft.FontWeight.BOLD,
            color="#1f2a44",
        )
        subtitle = ft.Text(
            "Interfaz gráfica para jugar y ver el algoritmo en acción",
            size=13,
            color="#4c5c7a",
        )

        self.mode_dropdown = ft.Dropdown(
            label="Modo",
            width=220,
            value="human_vs_ai",
            options=[
                ft.dropdown.Option("human_vs_ai", "Humano vs IA"),
                ft.dropdown.Option("ai_vs_ai", "IA vs IA (paso a paso)"),
            ],
            text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_600, color="#1f2a44"),
            label_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_600, color="#3f4b62"),
        )
        self.mode_dropdown.on_change = self._on_mode_change

        self.size_input = ft.TextField(
            label="Tamaño del tablero (N)",
            value=str(self.size),
            width=220,
            on_submit=self._on_size_submit,
            input_filter=ft.NumbersOnlyInputFilter(),
            text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_600, color="#1f2a44"),
            label_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_600, color="#3f4b62"),
        )

        self.time_slider = ft.Slider(
            min=0.5,
            max=4.5,
            divisions=8,
            label="{value}",
            width=220,
            value=self.time_limit,
        )
        self.time_slider.on_change = self._on_time_change

        self.start_btn = ft.Button(
            "Iniciar juego",
            on_click=self._on_start_or_new,
            bgcolor="#2d7dd2",
            color="#f5f2eb",
        )

        self.hint_text = ft.Text(
            "Tip: en Humano vs IA, haces clic en una celda vacía.",
            size=13,
            weight=ft.FontWeight.W_500,
            color="#3f4b62",
        )
        self.legend_row = ft.Row(
            spacing=10,
            controls=[
                ft.Container(width=12, height=12, bgcolor="#2d7dd2", border_radius=6),
                ft.Text("Jugador 1 (X) - Azul", size=12, color="#3f4b62"),
                ft.Container(width=12, height=12, bgcolor="#f45d01", border_radius=6),
                ft.Text("Jugador 2 (O) - Naranja", size=12, color="#3f4b62"),
            ],
        )
        self.scroll_hint = ft.Text(
            "Scroll: rueda = vertical, Shift + rueda = horizontal",
            size=11,
            color="#6b7a90",
        )

        controls = ft.Container(
            padding=20,
            border_radius=16,
            bgcolor="#ffffff",
            shadow=ft.BoxShadow(blur_radius=16, color="#e3dccf"),
            content=ft.Column(
                spacing=14,
                controls=[
                    ft.Text("Panel de control", size=18, weight=ft.FontWeight.BOLD, color="#1f2a44"),
                    self.mode_dropdown,
                    ft.Text("Tamaño del tablero", size=13, weight=ft.FontWeight.W_500, color="#3f4b62"),
                    self.size_input,
                    ft.Text("Dificultad (tiempo IA)", size=13, weight=ft.FontWeight.W_500, color="#3f4b62"),
                    self.time_slider,
                    self.start_btn,
                    self.hint_text,
                    self.legend_row,
                    self.scroll_hint,
                ],
            ),
        )

        self.board_container = ft.Container(
            content=ft.Column(spacing=8),
        )
        self.board_scroll_x = ft.Row(
            controls=[self.board_container],
            scroll=ft.ScrollMode.ALWAYS,
            expand=True,
        )
        self.board_scroll_y = ft.Column(
            controls=[self.board_scroll_x],
            scroll=ft.ScrollMode.ALWAYS,
            expand=True,
        )
        self.board_viewport = ft.Container(
            padding=16,
            border_radius=16,
            bgcolor="#ffffff",
            shadow=ft.BoxShadow(blur_radius=16, color="#e3dccf"),
            content=self.board_scroll_y,
            expand=True,
            height=620,
        )

        info_bar = ft.Row(
            controls=[
                ft.Column(
                    spacing=6,
                    controls=[
                        self.turn_text,
                        self.status_text,
                    ]
                )
            ]
        )

        layout = ft.Column(
            spacing=20,
            controls=[
                ft.Column(controls=[title, subtitle], spacing=2),
                info_bar,
                ft.ResponsiveRow(
                    spacing=16,
                    controls=[
                        ft.Container(col={"sm": 12, "md": 4}, content=controls),
                        ft.Container(col={"sm": 12, "md": 8}, content=self.board_viewport),
                    ],
                ),
            ],
        )

        self.page.add(layout)

    # -----------------------------
    # Game logic
    # -----------------------------
    def _reset_game(self) -> None:
        self.board = HexBoard(self.size)
        self.current_player = 1
        self.players = {
            1: SmartPlayer(time_limit=self.time_limit),
            2: SmartPlayer(time_limit=self.time_limit),
        }
        self.cell_size = self._compute_cell_size()
        self.ai_delay_s = self._calc_ai_delay_s()
        self.game_started = False
        self._stop_ai_loop()
        self._sync_start_button()
        self._build_board()
        self._update_status("Presiona 'Iniciar juego' para comenzar.")
        self._update_turn("Turno: -")
        self.page.update()

    def _build_board(self) -> None:
        self.cells.clear()
        self.cell_texts.clear()

        rows = []
        indent_step = self.cell_size * 0.45
        margin = self.row_spacing

        # Columnas para segmentos laterales
        left_segments = []
        right_segments = []

        for r in range(self.size):
            row_controls = []
            
            # Añadir línea naranja ARRIBA si es la primera fila
            if r == 0:
                top_row = []
                if r % 2 == 1:
                    top_row.append(ft.Container(width=indent_step))
                for c in range(self.size):
                    top_row.append(ft.Container(
                        width=self.cell_size,
                        height=4,
                        bgcolor="#f45d01",
                        border_radius=2,
                        margin=ft.Margin.only(bottom=margin),
                    ))
                rows.append(ft.Row(top_row, spacing=self.col_spacing))
                
                # Segmento lateral para la línea naranja superior
                left_segments.append(ft.Container(width=4, height=4 + margin, bgcolor="transparent"))
                right_segments.append(ft.Container(width=4, height=4 + margin, bgcolor="transparent"))
            
            # Fila de celdas con segmentos azules laterales
            row_controls = []
            
            if r % 2 == 1:
                row_controls.append(ft.Container(width=indent_step))

            for c in range(self.size):
                label = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color="#1f2a44")
                
                cell_content = ft.Container(
                    width=self.cell_size,
                    height=self.cell_size,
                    border_radius=12,
                    alignment=ft.Alignment.CENTER,
                    bgcolor="#f1ede5",
                    border=ft.Border.all(1, "#cfc7ba"),
                    animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
                    content=label,
                    on_click=lambda e, r=r, c=c: self._on_cell_click(r, c),
                )
                
                row_controls.append(cell_content)
                self.cells[(r, c)] = cell_content
                self.cell_texts[(r, c)] = label

            rows.append(ft.Row(row_controls, spacing=self.col_spacing))
            
            # Segmento azul lateral para fila de celdas
            left_segments.append(ft.Container(
                width=4,
                height=self.cell_size,
                bgcolor="#0d47a1",
                border_radius=2,
                margin=ft.Margin.only(right=margin),
            ))
            
            right_segments.append(ft.Container(
                width=4,
                height=self.cell_size,
                bgcolor="#0d47a1",
                border_radius=2,
                margin=ft.Margin.only(left=margin),
            ))
            
            # Añadir línea naranja ABAJO si es la última fila
            if r == self.size - 1:
                bottom_row = []
                if r % 2 == 1:
                    bottom_row.append(ft.Container(width=indent_step))
                for c in range(self.size):
                    bottom_row.append(ft.Container(
                        width=self.cell_size,
                        height=4,
                        bgcolor="#f45d01",
                        border_radius=2,
                        margin=ft.Margin.only(top=margin),
                    ))
                rows.append(ft.Row(bottom_row, spacing=self.col_spacing))
                
                # Segmento lateral para la línea naranja inferior
                left_segments.append(ft.Container(width=4, height=4 + margin, bgcolor="transparent"))
                right_segments.append(ft.Container(width=4, height=4 + margin, bgcolor="transparent"))

        # Board central sin indentación lateral
        board_column = ft.Column(rows, spacing=self.row_spacing)
        
        # Columnas laterales alineadas con espaciado
        left_column = ft.Column(left_segments, spacing=self.row_spacing)
        right_column = ft.Column(right_segments, spacing=self.row_spacing)

        # Layout final: segmentos laterales + board + segmentos laterales
        board_with_sides = ft.Row(
            [left_column, board_column, right_column],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        self.board_container.content = board_with_sides
        self.board_container.width = self._board_total_width(indent_step, margin)
        self.board_container.height = self._board_total_height(margin)

    def _update_board_view(self) -> None:
        for (r, c), cell in self.cells.items():
            value = self.board.board[r][c]
            label = self.cell_texts[(r, c)]
            if value == 0:
                cell.bgcolor = "#f1ede5"
                label.value = ""
                label.color = "#1f2a44"
            elif value == 1:
                cell.bgcolor = "#2d7dd2"
                label.value = "X"
                label.color = "#f7f3ea"
            else:
                cell.bgcolor = "#f45d01"
                label.value = "O"
                label.color = "#f7f3ea"

    def _make_move(self, move: CellKey, player_id: int) -> bool:
        row, col = move
        if self.board.place_piece(row, col, player_id):
            self.current_player = 2 if player_id == 1 else 1
            return True
        return False

    def _check_end(self) -> bool:
        winner = MCTSSimulator.check_winner(self.board)
        if winner != 0:
            self._update_status(f"Ganador: Jugador {winner}")
            self._update_turn(f"Partida finalizada.")
            return True
        if not self._has_moves():
            self._update_status("Tablero lleno. Sin ganador.")
            self._update_turn("Partida finalizada.")
            return True
        return False

    def _has_moves(self) -> bool:
        for r in range(self.size):
            for c in range(self.size):
                if self.board.board[r][c] == 0:
                    return True
        return False

    def _ai_move_with_delay(self) -> None:
        """Ejecuta el movimiento de la IA de forma asincrónica"""
        if not self.game_started or not self._is_human_vs_ai_mode():
            return
        asyncio.create_task(self._ai_move_async_for_human())

    async def _ai_move_async(self) -> bool:
        """Ejecuta un turno de IA sin bloquear la UI. Retorna False si termina la partida."""
        if not self.game_started or self._check_end():
            return False

        player_id = self.current_player
        player_obj = self.players[player_id]
        self._update_status("IA pensando...")
        self.page.update()

        loop = asyncio.get_running_loop()
        start = time.time()
        move = await loop.run_in_executor(None, player_obj.play, self.board)
        elapsed = time.time() - start

        if not self._make_move(move, player_id):
            self._update_status("IA intentó movimiento inválido.")
            self.page.update()
            return False

        self._update_board_view()
        self._update_status(f"IA movió en {move} ({elapsed:.2f}s)")
        self._update_turn()
        self.page.update()

        if self._check_end():
            self.page.update()
            return False

        return True

    async def _ai_move_async_for_human(self) -> None:
        """Turno IA en modo humano vs IA."""
        ok = await self._ai_move_async()
        if not ok:
            return
        if self.game_started and self._is_human_vs_ai_mode():
            self._update_turn("Turno: Jugador 1 (X)")
            self._update_status("Tu turno. Haz clic en una celda.")
            self.page.update()

    # IA vs IA loop (async)
    def _start_ai_loop(self) -> None:
        if self.ai_loop_task and not self.ai_loop_task.done():
            return
        self.ai_loop_running = True
        self.ai_loop_task = asyncio.create_task(self._ai_loop_async())

    def _stop_ai_loop(self) -> None:
        self.ai_loop_running = False
        if self.ai_loop_task and not self.ai_loop_task.done():
            self.ai_loop_task.cancel()
        self.ai_loop_task = None

    async def _ai_loop_async(self) -> None:
        while self.ai_loop_running and self.game_started and self._is_ai_vs_ai_mode():
            ok = await self._ai_move_async()
            if not ok:
                break
            await asyncio.sleep(self.ai_delay_s)

    # UI helpers
    def _update_status(self, text: str) -> None:
        self.status_text.value = text

    def _update_turn(self, text: str | None = None) -> None:
        if text is not None:
            self.turn_text.value = text
        else:
            player_name = "Jugador 1 (X)" if self.current_player == 1 else "Jugador 2 (O)"
            self.turn_text.value = f"Turno: {player_name}"

    # -----------------------------
    # Events
    # -----------------------------
    def _on_cell_click(self, r: int, c: int) -> None:
        if not self.game_started or not self._is_human_vs_ai_mode():
            return
        if self.current_player != 1:
            return
        if self.board.board[r][c] != 0:
            return

        # Jugador 1 hace su movimiento
        if not self._make_move((r, c), 1):
            return

        # Actualizar visual del tablero con animación
        self._update_board_view()
        self._update_status("Turno del jugador 1 (X) completado")
        self.page.update()
        
        # Revisar si terminó el juego
        if self._check_end():
            self.page.update()
            return

        # Mostrar que la IA está pensando
        self._update_turn("Turno: Jugador 2 (O) pensando...")
        self._update_status("Esperando movimiento de IA...")
        self.page.update()
        
        # Ejecutar la IA en un hilo separado - NO bloquear aquí
        self._ai_move_with_delay()

    def _on_start_or_new(self, e: ft.ControlEvent) -> None:
        # Asegurar que usamos el valor actual del dropdown
        self.mode = self.mode_dropdown.value
        if not self.game_started:
            self.game_started = True
            self._sync_start_button()
            if self._is_ai_vs_ai_mode():
                self._update_turn("Turno: Jugador 1 (X)")
                self._update_status("IA vs IA en curso...")
                self.page.update()
                self._start_ai_loop()
            else:
                self._update_turn("Turno: Jugador 1 (X)")
                self._update_status("Tu turno. Haz clic en una celda.")
                self.page.update()
        else:
            self._reset_game()

    def _on_mode_change(self, e: ft.ControlEvent) -> None:
        self.mode = self.mode_dropdown.value
        if self._is_ai_vs_ai_mode():
            if self.game_started:
                self._update_turn("Turno: Jugador 1 (X)")
                self._update_status("IA vs IA en curso...")
                self.page.update()
                self._start_ai_loop()
                return
            self._update_status("Modo IA vs IA. Presiona 'Iniciar juego'.")
            self._update_turn("Turno: -")
        else:
            self._update_status("Modo Humano vs IA. Tu juegas primero.")
            self._stop_ai_loop()
            self._sync_start_button()
            if self.game_started:
                if self.current_player == 1:
                    self._update_turn("Turno: Jugador 1 (X)")
                    self._update_status("Tu turno. Haz clic en una celda.")
                else:
                    self._update_turn("Turno: Jugador 2 (O)")
                    self._update_status("IA pensando...")
                    self.page.update()
                    self._ai_move_with_delay()
        self.page.update()

    def _on_size_submit(self, e: ft.ControlEvent) -> None:
        try:
            value = int(self.size_input.value)
        except (TypeError, ValueError):
            return
        value = max(3, min(30, value))
        self.size_input.value = str(value)
        if value != self.size:
            self.size = value
            self._reset_game()

    def _on_time_change(self, e: ft.ControlEvent) -> None:
        self.time_limit = float(self.time_slider.value)
        self.ai_delay_s = self._calc_ai_delay_s()
        self._reset_game()

    def _sync_start_button(self) -> None:
        if self.game_started:
            self.start_btn.content = "Nuevo juego"
            self.start_btn.bgcolor = "#1f2a44"
        else:
            self.start_btn.content = "Iniciar juego"
            self.start_btn.bgcolor = "#2d7dd2"
        self.start_btn.update()

    def _calc_ai_delay_s(self) -> float:
        """IA vs IA: intervalo ligeramente mayor que el tiempo de dificultad."""
        return float(self.time_limit) + 0.3

    def _compute_cell_size(self) -> int:
        min_cell = 22
        max_cell = 72
        n = max(3, self.size)
        # Estimar área disponible para el tablero dentro de la ventana
        win_w = float(self.page.window_width or 1100)
        win_h = float(self.page.window_height or 760)
        panel_w = 300
        padding_w = 32
        spacing = 12
        board_area_w = max(320, win_w - panel_w - padding_w * 2 - spacing)
        board_area_h = max(300, win_h - 180)

        indent_factor = 0.45
        width_candidate = (board_area_w - (n - 1) * self.col_spacing) / (n + indent_factor)
        extra_border = 2 * (4 + self.row_spacing)
        height_candidate = (board_area_h - (n - 1) * self.row_spacing - extra_border) / n

        cell = min(width_candidate, height_candidate)
        if cell <= 0:
            cell = min_cell
        cell = max(min_cell, min(max_cell, cell))
        return int(cell)

    def _board_total_width(self, indent_step: float, margin: float) -> float:
        row_w = indent_step + self.size * self.cell_size + (self.size - 1) * self.col_spacing
        side_w = 4 + margin
        return row_w + side_w * 2

    def _board_total_height(self, margin: float) -> float:
        rows_count = self.size + 2
        return self.size * self.cell_size + 2 * 4 + (rows_count - 1) * self.row_spacing + 2 * margin


def main(page: ft.Page) -> None:
    HexApp(page)


def run() -> None:
    ft.run(main)


if __name__ == "__main__":
    run()
