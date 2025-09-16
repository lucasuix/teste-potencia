from __future__ import annotations
import flet as ft
from queue import Queue
from utils import PathManager, peripherals_list, communication_test_list
from time import sleep
import os
class View:
    # ─────────────────────────────────────────────────
    #  Construtor: Inicializacao da UI 
    # ─────────────────────────────────────────────────
    
    # Modern Color Scheme
    PRIMARY_COLOR = "#212b59"
    PRIMARY_LIGHT = "#4a5d8a"
    SECONDARY_COLOR = "#6c7b95"
    BACKGROUND_COLOR = "#1e2329"
    SURFACE_COLOR = "#2a2f36"
    CARD_COLOR = "#333842"
    SUCCESS_COLOR = "#00d4aa"
    ERROR_COLOR = "#ff4757"
    WARNING_COLOR = "#ffa502"
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#8892b0"
    TEXT_MUTED = "#5a6c7d"
    BORDER_COLOR = "#3d4450"

    def __init__(self, controller) -> None:
        self._controller = controller
        self._update_queue = Queue()
        self.page = None
        self.username_dropdown = None
        self.comport_dropdown = None
        self.serial_number_input = None
        self.test_mode_checkbox = None
        self.connect_btn = None
        self.compile_btn = None
        self.results = {}
        self.loading_indicator = None
        self.final_results_container = None

    def main(self, page: ft.Page) -> None:
        self.page = page
        self._setup_layout()
        self._setup_ui()
        self._carregar_dados_iniciais()
        self.pool()

    def _setup_layout(self) -> None:
        self.page.title = "Jiga de Teste Unificada - TECSCI"
        self.page.window_width = 1600  # Reduced size
        self.page.window_height = 1000  # Reduced size
        self.page.window_maximized = True  # Start maximized
        self.page.window_full_screen = True  # Open in fullscreen
        self.page.window_resizable = True  # Allow resizing
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = self.BACKGROUND_COLOR
        
        # Modern theme
        self.page.theme = ft.Theme(
            color_scheme_seed=self.PRIMARY_COLOR,
            visual_density=ft.VisualDensity.COMFORTABLE,
        )
        
        # Custom fonts
        self.page.fonts = {
            "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
        }
        
        icon_path = PathManager.get_path("assets/icon.ico")
        if os.path.exists(icon_path):
            self.page.window_icon = icon_path
    
    def _carregar_dados_iniciais(self):
        # Delegate to controller to load initial data
        self._controller._carregar_dados_iniciais()


    def _setup_ui(self) -> None:
        # Input frame (left side)
        input_frame = self._create_input_frame()
        
        # Output frame (right side)
        output_frame = self._create_output_frame()
        
        # Modern header - reduced padding
        header = ft.Container(
            content=ft.Text(
                "JIGA DE TESTE UNIFICADA",
                size=22,  # Slightly smaller
                weight=ft.FontWeight.W_300,
                color=self.TEXT_PRIMARY,
                font_family="Inter",
                text_align=ft.TextAlign.CENTER,
            ),
            padding=ft.padding.symmetric(vertical=12),  # Reduced from 20 to 12
            alignment=ft.alignment.center,
        )
        
        # Main content with modern spacing
        main_content = ft.Row(
            [input_frame, output_frame],
            spacing=25,  # Reduced spacing
            expand=True,
            alignment=ft.MainAxisAlignment.START,  # Changed from CENTER to START
        )
        
        self.page.add(
            ft.Column(
                [
                    header,
                    ft.Container(
                        content=main_content,
                        padding=ft.padding.only(left=30, right=30, bottom=20),  # Reduced padding
                        expand=True,
                    )
                ],
                expand=True,
                spacing=0,
            )
        )

    def _create_input_frame(self) -> ft.Container:
        # Logo
        logo_path = PathManager.get_path("assets/logo-dark.png")
        logo = None
        if os.path.exists(logo_path):
            logo = ft.Image(
                src=logo_path,
                width=200,
                height=100,
                fit=ft.ImageFit.CONTAIN,
            )

        # Modern form controls
        self.test_mode_checkbox = ft.Container(
            content=ft.Row(
                [
                    ft.Checkbox(
                        value=False,
                        active_color=self.PRIMARY_COLOR,
                        check_color=self.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "Modo de teste",
                        size=14,
                        color=self.TEXT_SECONDARY,
                        font_family="Inter",
                        weight=ft.FontWeight.W_400,
                    ),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(vertical=8),
        )

        self.username_dropdown = ft.Container(
            content=ft.Dropdown(
                label="Usuário",
                options=[ft.dropdown.Option("Selecione o usuário")],
                bgcolor="transparent",
                border_color="transparent",
                color=self.TEXT_PRIMARY,
                label_style=ft.TextStyle(color=self.TEXT_MUTED, size=12),
            ),
            width=300,
            padding=ft.padding.all(16),
            bgcolor=self.CARD_COLOR,
            border_radius=12,
            border=ft.border.all(1, self.BORDER_COLOR),
        )

        self.comport_dropdown = ft.Container(
            content=ft.Dropdown(
                label="Porta Serial",
                options=[ft.dropdown.Option("Selecione a porta serial")],
                bgcolor="transparent",
                border_color="transparent",
                color=self.TEXT_PRIMARY,
                label_style=ft.TextStyle(color=self.TEXT_MUTED, size=12),
            ),
            width=300,
            padding=ft.padding.all(16),
            bgcolor=self.CARD_COLOR,
            border_radius=12,
            border=ft.border.all(1, self.BORDER_COLOR),
        )

        self.serial_number_input = ft.Container(
            content=ft.TextField(
                label="Número de Série",
                value="0",
                bgcolor="transparent",
                border_color="transparent",
                color=self.TEXT_PRIMARY,
                cursor_color=self.PRIMARY_COLOR,
                label_style=ft.TextStyle(color=self.TEXT_MUTED, size=12),
            ),
            width=300,
            padding=ft.padding.all(16),
            bgcolor=self.CARD_COLOR,
            border_radius=12,
            border=ft.border.all(1, self.BORDER_COLOR),
        )

        # Modern buttons
        self.connect_btn = ft.Container(
            content=ft.ElevatedButton(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.PLAY_ARROW, size=18, color=self.TEXT_PRIMARY),
                        ft.Text(
                            "INICIAR",
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=self.TEXT_PRIMARY,
                            font_family="Inter",
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                ),
                bgcolor=self.PRIMARY_COLOR,
                color=self.TEXT_PRIMARY,
                elevation=0,
                on_click=lambda _: self._controller.connect_btn_handler(),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=12),
                    overlay_color={"hovered": self.PRIMARY_LIGHT},
                ),
            ),
            width=300,
            height=52,
        )

        self.compile_btn = ft.Container(
            content=ft.OutlinedButton(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.FOLDER_ZIP_OUTLINED, size=18, color=self.TEXT_SECONDARY),
                        ft.Text(
                            "COMPILAR LOGS",
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=self.TEXT_SECONDARY,
                            font_family="Inter",
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                ),
                on_click=lambda _: self._controller.compile_btn_handler(),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=12),
                    side=ft.BorderSide(1, self.BORDER_COLOR),
                    overlay_color={"hovered": self.CARD_COLOR},
                ),
            ),
            width=300,
            height=52,
        )

        # Input frame container
        components = [
            logo,
            self.test_mode_checkbox,
            self.username_dropdown,
            self.comport_dropdown,
            self.serial_number_input,
            self.connect_btn,
            self.compile_btn,
        ]

        # Filter out None components
        components = [c for c in components if c is not None]

        return ft.Container(
            content=ft.Column(
                components,
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,  # Further reduced spacing
            ),
            width=300,  # Reduced width
            padding=16,  # Reduced padding
            bgcolor=self.SURFACE_COLOR,
            border_radius=16,
            border=ft.border.all(1, self.BORDER_COLOR),
        )




    def _create_test_section(self, test_dict: dict, section_title: str) -> list:
        """Create a section of test cards with title."""
        rows = []
        current_row = []
        
        for idx, (key, peripheral) in enumerate(test_dict.items()):
            # Modern peripheral card design
            status_color = self.TEXT_MUTED
            if peripheral.status == "OK":
                status_color = self.SUCCESS_COLOR
            elif peripheral.status == "NG":
                status_color = self.ERROR_COLOR
            
            label = ft.Text(
                peripheral.name,
                size=14,  # Slightly smaller to fit 3 columns
                weight=ft.FontWeight.W_500,
                color=self.TEXT_PRIMARY,
                font_family="Inter",
            )
            
            result_indicator = ft.Container(
                content=ft.Text(
                    peripheral.status,
                    size=13,  # Slightly smaller
                    color=self.TEXT_PRIMARY,
                    text_align=ft.TextAlign.CENTER,
                    weight=ft.FontWeight.W_700,
                    font_family="Inter",
                ),
                bgcolor=status_color,
                border_radius=8,
                width=60,  # Slightly smaller
                height=28,  # Slightly smaller
                alignment=ft.alignment.center,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=4,
                    color=status_color + "40",
                    offset=ft.Offset(0, 2),
                ),
            )
            
            # Store reference to result indicator
            self.results[key] = result_indicator
            
            # Create row with label and result
            row_content = ft.Row(
                [label, result_indicator],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=15,  # Reduced spacing
            )
            
            current_row.append(
                ft.Container(
                    content=row_content,
                    width=320,  # Reduced width
                    padding=14,  # Reduced padding
                    bgcolor=self.CARD_COLOR,
                    border_radius=12,
                    border=ft.border.all(1, self.BORDER_COLOR),
                )
            )
            
            # Add to rows when we have 3 items or it's the last item
            if len(current_row) == 3 or idx == len(test_dict) - 1:
                # Fill empty spaces in last row if needed
                while len(current_row) < 3 and idx == len(test_dict) - 1:
                    current_row.append(ft.Container(width=320))  # Empty spacer
                rows.append(ft.Row(current_row, spacing=35, alignment=ft.MainAxisAlignment.START))  # Increased spacing between cards
                current_row = []
        
        return rows

    def _create_output_frame(self) -> ft.Container:
        # Create main test section
        main_test_rows = self._create_test_section(peripherals_list, "TESTES PRINCIPAIS")
        
        # Create communication test section
        comm_test_rows = self._create_test_section(communication_test_list, "TESTE DE COMUNICAÇÃO")

        # Loading indicator
        self.loading_indicator = ft.Container(
            content=ft.Row(
                [
                    ft.ProgressRing(
                        width=24,
                        height=24,
                        stroke_width=3,
                        color=self.PRIMARY_COLOR,
                    ),
                    ft.Text(
                        "Teste em andamento...",
                        size=16,
                        color=self.TEXT_SECONDARY,
                        font_family="Inter",
                        weight=ft.FontWeight.W_500,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            ),
            width=1150,  # Match the output frame width
            padding=16,
            bgcolor=self.CARD_COLOR,
            border_radius=12,
            border=ft.border.all(1, self.BORDER_COLOR),
            visible=False,
        )

        # Final results container with table layout
        self.final_results_table = ft.Column([], spacing=4)  # Will hold table rows
        self.final_results_duration = ft.Container()  # Will hold duration info
        
        self.final_results_container = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Text(
                            "RESULTADOS FINAIS",
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=self.TEXT_SECONDARY,
                            font_family="Inter",
                            text_align=ft.TextAlign.CENTER,
                        ),
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=4),  # Minimal spacing
                    ft.Container(
                        content=ft.Row(
                            [
                                # Table container - compact width
                                ft.Container(
                                    content=ft.Column([
                                        self.final_results_table
                                    ], scroll=ft.ScrollMode.AUTO),  # Make scrollable
                                    height=280,  # Reduced height
                                    width=540,   # Much smaller width to match actual column usage
                                    padding=ft.padding.all(12),
                                ),
                                ft.Container(width=16),  # Gap between table and duration
                                # Duration in separate card beside table
                                ft.Container(
                                    content=self.final_results_duration,
                                    height=280,  # Same height as table
                                    width=180,   # Reduced duration card
                                    alignment=ft.alignment.center,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        padding=16,  # Reduced padding
                        bgcolor=self.CARD_COLOR,
                        border_radius=12,
                        border=ft.border.all(1, self.BORDER_COLOR),
                        alignment=ft.alignment.center,
                    ),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=1150,  # Match the output frame width
            padding=ft.padding.symmetric(horizontal=0, vertical=6),  # Reduced padding
            visible=False,
            alignment=ft.alignment.center,
        )

        return ft.Container(
            content=ft.Column(
                [
                    # Main tests section
                    ft.Text(
                        "TESTES PRINCIPAIS",
                        size=16,  # Reduced size
                        weight=ft.FontWeight.W_600,
                        color=self.TEXT_SECONDARY,
                        font_family="Inter",
                    ),
                    ft.Container(height=6),  # Reduced spacing
                    ft.Column(
                        main_test_rows,
                        spacing=12,  # Reduced spacing between test cards
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Container(height=20),  # Spacing between sections
                    # Communication tests section
                    ft.Text(
                        "TESTE DE COMUNICAÇÃO",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=self.TEXT_SECONDARY,
                        font_family="Inter",
                    ),
                    ft.Container(height=6),
                    ft.Column(
                        comm_test_rows,
                        spacing=12,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Container(height=10),  # Reduced spacing before loading
                    self.loading_indicator,
                    self.final_results_container,
                ],
                spacing=0,
                alignment=ft.MainAxisAlignment.START,
            ),
            width=1150,  # Increased the main output frame width
            padding=16,  # Reduced padding
            bgcolor=self.SURFACE_COLOR,
            border_radius=16,
            border=ft.border.all(1, self.BORDER_COLOR),
        )

    # ─────────────────────────────────────────────────
    #  Metodos Publicos: Interacoes e Atualizacoes da UI
    # ─────────────────────────────────────────────────

    def set_ports_available(self, ports: list[str]) -> None:
        options = [ft.dropdown.Option(port) for port in ports]
        self.comport_dropdown.content.options = options
        if self.page:
            self.page.update()

    def set_users_available(self, users: list[str]) -> None:
        options = [ft.dropdown.Option(user) for user in users]
        self.username_dropdown.content.options = options
        if self.page:
            self.page.update()

    def update_result_label(self, key: str, success: bool) -> None:
        container = self.results.get(key)
        if container:
            color = self.SUCCESS_COLOR if success else self.ERROR_COLOR
            text = "OK" if success else "NG"
            container.bgcolor = color
            container.content.value = text
            container.content.color = self.TEXT_PRIMARY
            container.shadow = ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=color + "40",
                offset=ft.Offset(0, 2),
            )
            if self.page:
                self.page.update()

    def toggle_connection(self, is_connected: bool) -> None:
        button = self.connect_btn.content
        button_row = button.content
        if is_connected:
            button_row.controls[0].name = ft.Icons.STOP
            button_row.controls[1].value = "PARAR"
            button.bgcolor = self.ERROR_COLOR
            button.on_click = lambda _: self._controller.cancel_btn_handler()
            disabled = True
        else:
            button_row.controls[0].name = ft.Icons.PLAY_ARROW
            button_row.controls[1].value = "INICIAR"
            button.bgcolor = self.PRIMARY_COLOR
            button.on_click = lambda _: self._controller.connect_btn_handler()
            disabled = False

        # Enable/disable inputs (access the inner controls)
        self.username_dropdown.content.disabled = disabled
        self.comport_dropdown.content.disabled = disabled
        self.serial_number_input.content.disabled = disabled
        self.test_mode_checkbox.content.controls[0].disabled = disabled
        self.compile_btn.content.disabled = disabled
        
        if self.page:
            self.page.update()

    def get_user_inputs(self) -> tuple[str, str, str, bool]:
        username = self.username_dropdown.content.value or ""
        comport = (self.comport_dropdown.content.value or "").split(":")[0]
        serial_number = self.serial_number_input.content.value or ""
        test_mode = self.test_mode_checkbox.content.controls[0].value or False
        return username, comport, serial_number, test_mode

    # def clear_terminal(self) -> None:
    #     self.terminal_output.configure(state="normal")
    #     self.terminal_output.delete("1.0", "end") 
    #     self.terminal_output.configure(state="disabled")

    def clear_serial_number(self) -> None:
        self.serial_number_input.content.value = "0"
        if self.page:
            self.page.update()

    def show_message(self, msg: str, error_tag: bool = False) -> None:
        print(msg)

    def show_test_result(self, msg: str, result: bool) -> str:
        # Create a simple alert dialog for Flet
        def close_dialog(e):
            dialog.open = False
            if self.page:
                self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text(
                "Sucesso" if result else "Erro",
                color=self.SUCCESS_COLOR if result else self.ERROR_COLOR,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Text(msg, color=self.TEXT_PRIMARY),
            bgcolor=self.SURFACE_COLOR,
            actions=[
                ft.TextButton(
                    "OK", 
                    on_click=close_dialog,
                    style=ft.ButtonStyle(
                        color=self.PRIMARY_COLOR,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        if self.page:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
        
        return "OK"
    
    def show_question(self, question: str) -> bool:
        result = [False]  # Using list to allow modification in nested function
        
        def on_yes(e):
            result[0] = True
            dialog.open = False
            if self.page:
                self.page.update()
        
        def on_no(e):
            result[0] = False
            dialog.open = False
            if self.page:
                self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text(
                "Confirmação",
                color=self.WARNING_COLOR,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Text(question, color=self.TEXT_PRIMARY),
            bgcolor=self.SURFACE_COLOR,
            actions=[
                ft.TextButton(
                    "SIM", 
                    on_click=on_yes,
                    style=ft.ButtonStyle(
                        color=self.SUCCESS_COLOR,
                    ),
                ),
                ft.TextButton(
                    "NÃO", 
                    on_click=on_no,
                    style=ft.ButtonStyle(
                        color=self.ERROR_COLOR,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        if self.page:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
        
        return result[0]

    def show_loading(self, show: bool = True) -> None:
        """Show or hide the loading indicator"""
        if self.loading_indicator:
            self.loading_indicator.visible = show
            if self.page:
                self.page.update()

    def _create_table_row(self, label: str, value: str, is_header: bool = False) -> ft.Container:
        """Create a table row with aligned columns"""
        if is_header:
            # Header row with underline
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(
                                label,
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=self.TEXT_SECONDARY,
                                font_family="Inter",
                            ),
                            width=400,  # Match the data row width
                            alignment=ft.alignment.center_left,
                        ),
                        ft.Container(
                            content=ft.Text(
                                value,
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=self.TEXT_SECONDARY,
                                font_family="Inter",
                                text_align=ft.TextAlign.LEFT,  # Changed to LEFT alignment
                            ),
                            width=100,  # Match the data row width
                            alignment=ft.alignment.center_left,  # Changed to LEFT alignment
                        ),
                    ],
                    spacing=2,  # Minimal spacing between header columns
                ),
                padding=ft.padding.symmetric(vertical=8, horizontal=4),
                border=ft.border.only(bottom=ft.BorderSide(1, self.BORDER_COLOR)),
            )
        else:
            # Regular data row - determine color based on value
            value_color = self.TEXT_PRIMARY
            if value == 'OK':
                value_color = self.SUCCESS_COLOR
            elif value == 'NG':
                value_color = self.ERROR_COLOR
            elif any(unit in value for unit in ['V', '%', 's']):
                value_color = self.WARNING_COLOR  # Use warning color for measurements
            else:
                value_color = self.SUCCESS_COLOR  # Default for other values
                
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(
                                label,
                                size=13,  # Reduced size
                                color=self.TEXT_PRIMARY,
                                font_family="Inter",
                            ),
                            width=400,  # Reduced width to bring columns closer
                            alignment=ft.alignment.center_left,
                        ),
                        ft.Container(
                            content=ft.Text(
                                value,
                                size=13,  # Reduced size
                                color=value_color,
                                font_family="Inter",
                                text_align=ft.TextAlign.LEFT,  # Changed to LEFT alignment
                                weight=ft.FontWeight.W_500,
                            ),
                            width=100,  # Reduced width for values
                            alignment=ft.alignment.center_left,  # Changed to LEFT alignment
                        ),
                    ],
                    spacing=2,  # Minimal spacing between test name and result
                ),
                padding=ft.padding.symmetric(vertical=6, horizontal=4),
            )

    def show_final_results(self, results_text: str, duration: float) -> None:
        """Display final results with test duration in table format"""
        if self.final_results_container:
            # Clear previous results
            self.final_results_table.controls.clear()
            
            # Parse results text and create table
            lines = results_text.split('\n')
            
            # Add header
            self.final_results_table.controls.append(
                self._create_table_row("TESTE", "RESULTADO", is_header=True)
            )
            
            # Process all lines
            for line in lines:
                line_clean = line.strip()
                if not line_clean:
                    continue
                    
                # Check if it's a test result line
                if ':' in line_clean and ('OK' in line_clean or 'NG' in line_clean):
                    # Split on the colon
                    parts = line_clean.split(':', 1)
                    if len(parts) == 2:
                        test_name = parts[0].strip()
                        result_part = parts[1].strip()
                        
                        # Extract status (OK/NG)
                        status = 'OK' if 'OK' in result_part else 'NG'
                        
                        self.final_results_table.controls.append(
                            self._create_table_row(test_name, status)
                        )
                        continue
                        
                # Check if it's a voltage/measurement line (starts with spaces, contains V)
                elif line_clean.startswith(' ') and 'V' in line_clean:
                    # This is a detail line, show it indented
                    self.final_results_table.controls.append(
                        ft.Container(
                            content=ft.Text(
                                line_clean,
                                size=12,
                                color=self.TEXT_SECONDARY,
                                font_family="Inter",
                            ),
                            padding=ft.padding.only(left=20, top=2, bottom=2),
                            alignment=ft.alignment.center_left,
                        )
                    )
                    continue
                    
                # Check for PWM results with specific patterns
                import re
                value_match = re.search(r'(\d+\.?\d*\s*[A-Za-z%]*)\s*$', line_clean)
                if value_match:
                    value = value_match.group(1).strip()
                    label_end = value_match.start()
                    label = line_clean[:label_end].strip()
                    
                    if label and value:
                        self.final_results_table.controls.append(
                            self._create_table_row(label, value)
                        )
                        continue
                        
                # For any other lines that don't match patterns, show as regular text
                if line_clean and not line_clean.startswith('─') and not line_clean.startswith('-'):
                    # Determine color based on content
                    text_color = self.TEXT_PRIMARY
                    if 'OK' in line_clean:
                        text_color = self.SUCCESS_COLOR
                    elif 'NG' in line_clean or 'falha' in line_clean.lower() or 'erro' in line_clean.lower():
                        text_color = self.ERROR_COLOR
                    
                    self.final_results_table.controls.append(
                        ft.Container(
                            content=ft.Text(
                                line_clean,
                                size=13,
                                color=text_color,
                                font_family="Inter",
                                weight=ft.FontWeight.W_500 if text_color != self.TEXT_PRIMARY else ft.FontWeight.W_400,
                            ),
                            padding=ft.padding.symmetric(vertical=4),
                            alignment=ft.alignment.center_left,
                        )
                    )
            
            # Update duration display for side card with status info
            duration_str = f"{duration:.2f}s"
            
            # Determine overall status for display
            status_text = "APROVADO"
            status_color = self.SUCCESS_COLOR
            status_icon = ft.Icons.CHECK_CIRCLE_OUTLINED
            
            # Check if there are any NG results in the test data
            if results_text and "NG" in results_text:
                status_text = "REPROVADO"
                status_color = self.ERROR_COLOR
                status_icon = ft.Icons.CANCEL_OUTLINED
            
            self.final_results_duration.content = ft.Column(
                [
                    ft.Text(
                        "RESUMO",
                        size=14,
                        color=self.TEXT_SECONDARY,
                        font_family="Inter",
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.W_600,
                    ),
                    ft.Container(height=12),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(
                                    status_icon,
                                    size=28,
                                    color=status_color,
                                ),
                                ft.Container(height=6),
                                ft.Text(
                                    status_text,
                                    size=14,
                                    color=status_color,
                                    font_family="Inter",
                                    text_align=ft.TextAlign.CENTER,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                ft.Container(height=8),
                                ft.Row([
                                    ft.Icon(ft.Icons.TIMER_OUTLINED, size=16, color=self.TEXT_SECONDARY),
                                    ft.Text(duration_str, size=12, color=self.TEXT_SECONDARY, font_family="Inter")
                                ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.all(12),
                        bgcolor=self.SURFACE_COLOR,
                        border_radius=8,
                        border=ft.border.all(2, status_color + "40"),
                        alignment=ft.alignment.center,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            )
            
            # Show the container
            self.final_results_container.visible = True
            
            if self.page:
                self.page.update()

    def hide_final_results(self) -> None:
        """Hide the final results container"""
        if self.final_results_container:
            self.final_results_container.visible = False
            if self.page:
                self.page.update()
        
    # ─────────────────────────────────────────────────
    #  UI Update Queue: Garante Thread Safety
    # ─────────────────────────────────────────────────

    def pool(self) -> None:
        if not self._update_queue.empty():
            func, args = self._update_queue.get()
            func(*args)
        # Schedule next check
        import threading
        threading.Timer(0.1, self.pool).start()

    def add_update(self, func: callable, *args: list) -> None:
        self._update_queue.put((func, args,))

    def run(self) -> None:
        """Run the Flet application"""
        ft.app(target=self.main, view=ft.AppView.FLET_APP)
    