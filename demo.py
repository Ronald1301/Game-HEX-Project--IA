"""
DEMO - Interfaz gráfica (Flet) para el juego HEX con MCTS
"""

import time
import threading
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
        self.autoplay = False
        self.autoplay_ms = 800
        self.autoplay_thread = None
        self.autoplay_stop_event = threading.Event()

        self.cell_size = 48
        self.cells: Dict[CellKey, ft.Container] = {}
        self.cell_texts: Dict[CellKey, ft.Text] = {}

        self.status_text = ft.Text("", size=14, weight=ft.FontWeight.W_500)
        self.turn_text = ft.Text("", size=14, weight=ft.FontWeight.W_500)

        self._build_ui()
        self._reset_game()

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
        )
        self.mode_dropdown.on_change = self._on_mode_change

        self.size_slider = ft.Slider(
            min=3,
            max=9,
            divisions=6,
            label="{value}",
            width=220,
            value=self.size,
        )
        self.size_slider.on_change = self._on_size_change

        self.time_slider = ft.Slider(
            min=0.5,
            max=4.5,
            divisions=8,
            label="{value}",
            width=220,
            value=self.time_limit,
        )
        self.time_slider.on_change = self._on_time_change

        self.speed_slider = ft.Slider(
            min=200,
            max=2000,
            divisions=9,
            label="{value} ms",
            width=220,
            value=self.autoplay_ms,
        )
        self.speed_slider.on_change = self._on_speed_change

        self.new_game_btn = ft.Button(
            "Nuevo juego",
            on_click=self._on_new_game,
            bgcolor="#1f2a44",
            color="#f5f2eb",
        )

        self.autoplay_btn = ft.Button(
            "Autoplay IA",
            on_click=self._on_autoplay_toggle,
            bgcolor="#2d7dd2",
            color="#f5f2eb",
        )

        self.ai_step_btn = ft.OutlinedButton(
            "Mover IA",
            on_click=self._on_ai_step,
        )

        self.hint_text = ft.Text(
            "Tip: en Humano vs IA, haces clic en una celda vacía.",
            size=12,
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
                    ft.Text("Panel de control", size=16, weight=ft.FontWeight.BOLD),
                    self.mode_dropdown,
                    ft.Text("Tamaño del tablero", size=12, color="#6b7a90"),
                    self.size_slider,
                    ft.Text("Tiempo por jugada (s)", size=12, color="#6b7a90"),
                    self.time_slider,
                    ft.Text("Velocidad autoplay", size=12, color="#6b7a90"),
                    self.speed_slider,
                    self.new_game_btn,
                    self.autoplay_btn,
                    self.ai_step_btn,
                    self.hint_text,
                ],
            ),
        )

        self.board_container = ft.Container(
            padding=20,
            border_radius=16,
            bgcolor="#ffffff",
            shadow=ft.BoxShadow(blur_radius=16, color="#e3dccf"),
            content=ft.Column(spacing=8),
        )

        info_bar = ft.Row(
            controls=[
                self.turn_text,
                ft.Container(width=12),
                self.status_text,
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
                        ft.Container(col={"sm": 12, "md": 8}, content=self.board_container),
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
        self.autoplay = False
        self._stop_autoplay()
        self._sync_autoplay_button()
        self._build_board()
        self._update_status("Listo para jugar.")
        self._update_turn()
        self.page.update()

    def _build_board(self) -> None:
        self.cells.clear()
        self.cell_texts.clear()

        rows = []
        indent_step = self.cell_size * 0.45
        margin = 6  # Espacio igual al spacing entre celdas
        
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
                rows.append(ft.Row(top_row, spacing=6))
                
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

            rows.append(ft.Row(row_controls, spacing=6))
            
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
                rows.append(ft.Row(bottom_row, spacing=6))
                
                # Segmento lateral para la línea naranja inferior
                left_segments.append(ft.Container(width=4, height=4 + margin, bgcolor="transparent"))
                right_segments.append(ft.Container(width=4, height=4 + margin, bgcolor="transparent"))

        # Board central sin indentación lateral
        board_column = ft.Column(rows, spacing=6)
        
        # Columnas laterales alineadas con espaciado
        left_column = ft.Column(left_segments, spacing=6)
        right_column = ft.Column(right_segments, spacing=6)

        # Layout final: segmentos laterales + board + segmentos laterales
        board_with_sides = ft.Row(
            [left_column, board_column, right_column],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        self.board_container.content = board_with_sides

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

    def _ai_move(self) -> None:
        if self._check_end():
            return
        player_id = self.current_player
        player_obj = self.players[player_id]
        self._update_status("IA pensando...")
        self.page.update()

        start = time.time()
        move = player_obj.play(self.board)
        elapsed = time.time() - start

        if not self._make_move(move, player_id):
            self._update_status("IA intentó movimiento inválido.")
            return

        self._update_status(f"IA movió en {move} ({elapsed:.2f}s)")
        self._update_turn()
        self._update_board_view()
        self._check_end()

    # Autoplay threading control
    def _start_autoplay(self) -> None:
        self.autoplay_stop_event.clear()
        self.autoplay_thread = threading.Thread(target=self._autoplay_loop, daemon=True)
        self.autoplay_thread.start()

    def _stop_autoplay(self) -> None:
        self.autoplay_stop_event.set()
        if self.autoplay_thread:
            self.autoplay_thread.join(timeout=1)
            self.autoplay_thread = None

    def _autoplay_loop(self) -> None:
        while not self.autoplay_stop_event.is_set():
            if self.autoplay:
                self._on_timer_tick(None)
            time.sleep(self.autoplay_ms / 1000.0)

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
        if self.mode != "human_vs_ai":
            return
        if self.current_player != 1:
            return
        if self.board.board[r][c] != 0:
            return

        if not self._make_move((r, c), 1):
            return

        self._update_board_view()
        if self._check_end():
            self.page.update()
            return

        self._update_turn()
        self.page.update()
        self._ai_move()
        self.page.update()

    def _on_new_game(self, e: ft.ControlEvent) -> None:
        self._reset_game()

    def _on_ai_step(self, e: ft.ControlEvent) -> None:
        if self.mode == "human_vs_ai" and self.current_player == 1:
            self._update_status("Es tu turno. Haz clic en el tablero.")
            self.page.update()
            return

        self._ai_move()
        self._update_board_view()
        self.page.update()

    def _on_mode_change(self, e: ft.ControlEvent) -> None:
        self.mode = self.mode_dropdown.value
        if self.mode == "ai_vs_ai":
            self._update_status("Modo IA vs IA. Usa 'Mover IA'.")
        else:
            self._update_status("Modo Humano vs IA. Tu juegas primero.")
            self.autoplay = False
            self.timer.disabled = True
            self._sync_autoplay_button()
        self.page.update()

    def _on_size_change(self, e: ft.ControlEvent) -> None:
        self.size = int(self.size_slider.value)
        self._reset_game()

    def _on_time_change(self, e: ft.ControlEvent) -> None:
        self.time_limit = float(self.time_slider.value)
        self._reset_game()

    def _on_speed_change(self, e: ft.ControlEvent) -> None:
        self.autoplay_ms = int(self.speed_slider.value)
        self.page.update()

    def _on_autoplay_toggle(self, e: ft.ControlEvent) -> None:
        if self.mode != "ai_vs_ai":
            self._update_status("Autoplay solo en modo IA vs IA.")
            self.page.update()
            return
        self.autoplay = not self.autoplay
        if self.autoplay:
            self._start_autoplay()
        else:
            self._stop_autoplay()
        self._sync_autoplay_button()
        self.page.update()

    def _sync_autoplay_button(self) -> None:
        if self.autoplay:
            self.autoplay_btn.text = "Pausar IA"
        else:
            self.autoplay_btn.text = "Autoplay IA"
            self._stop_autoplay()

    def _on_timer_tick(self, e: ft.ControlEvent) -> None:
        if not self.autoplay:
            return
        if self._check_end():
            self.autoplay = False
            self._sync_autoplay_button()
            self.page.update()
            return
        # En Humano vs IA, solo mover cuando es turno de la IA
        if self.mode == "human_vs_ai" and self.current_player != 2:
            return
        self._ai_move()
        self._update_board_view()
        self.page.update()


def main(page: ft.Page) -> None:
    HexApp(page)


def run() -> None:
    ft.run(main)


if __name__ == "__main__":
    run()
