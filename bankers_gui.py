"""Typed and button-controlled desktop interface for Banker’s Algorithm."""

import tkinter as tk
import threading
from pathlib import Path
from tkinter import ttk

try:
    import winsound
except ImportError:
    winsound = None

from bankers_simulator import (
    BankerState,
    check_request,
    check_safety,
    format_vector,
    vector_leq,
)


COLORS = {
    "background": "#090511",
    "panel": "#140C20",
    "panel_light": "#21122F",
    "input": "#0C0714",
    "border": "#4A2B5D",
    "text": "#FFF3FB",
    "muted": "#BDA9C7",
    "accent": "#FF3D9A",
    "accent_dark": "#451436",
    "blue": "#43E7FF",
    "warning": "#FFC857",
    "danger": "#FF657A",
    "disabled": "#766A7D",
}

MAX_PROCESSES = 8
MAX_RESOURCES = 5
MAX_UNITS = 99


class ScrollableFrame(tk.Frame):
    """Scrollable content area for larger process matrices."""

    def __init__(self, parent, background):
        super().__init__(parent, bg=background)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, bg=background, highlightthickness=0, borderwidth=0)
        self.scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
            bg=COLORS["panel_light"],
            troughcolor=background,
            activebackground=COLORS["accent"],
            borderwidth=0,
            highlightthickness=0,
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.content = tk.Frame(self.canvas, bg=background)
        self.window = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_content)
        self.canvas.bind_all("<MouseWheel>", self._mousewheel)

    def _update_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_content(self, event):
        self.canvas.itemconfigure(self.window, width=event.width)

    def _mousewheel(self, event):
        if self.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class BankersGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Neon Banker’s Algorithm | Fleischer’s Finest Five")
        self.root.geometry("1420x900")
        self.root.minsize(1180, 760)
        self.root.configure(bg=COLORS["background"])
        self.root.option_add("*Font", ("Segoe UI", 10))
        self._configure_table_styles()

        self.music_path = Path(__file__).resolve().with_name("nightclub_jazz.wav")
        self.button_sounds_available = winsound is not None
        self.music_available = self.button_sounds_available and self.music_path.is_file()
        self.music_enabled = self.music_available
        self.button_sounds_enabled = self.button_sounds_available

        self.process_count = 5
        self.resource_count = 3
        self.resource_ids = self._resource_labels(self.resource_count)
        self.total = [0] * self.resource_count
        self.allocation = [[0] * self.resource_count for _ in range(self.process_count)]
        self.maximum = [[0] * self.resource_count for _ in range(self.process_count)]
        self.request_process = 0
        self.request = [0] * self.resource_count
        self.mode = "safety"
        self._pending_edits = []
        self._integer_validator = self.root.register(self._validate_integer_text)

        self._build_layout()
        self.load_example()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        if self.music_enabled and not self._start_music():
            self.music_enabled = False
            self._sync_audio_buttons()

    def _configure_table_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Night.TNotebook",
            background=COLORS["panel"],
            borderwidth=0,
            tabmargins=(0, 0, 0, 0),
        )
        style.configure(
            "Night.TNotebook.Tab",
            background=COLORS["panel_light"],
            foreground=COLORS["muted"],
            padding=(12, 9),
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
        )
        style.map(
            "Night.TNotebook.Tab",
            background=[("selected", COLORS["accent_dark"])],
            foreground=[("selected", COLORS["accent"])],
        )
        style.configure(
            "Night.Treeview",
            background=COLORS["input"],
            fieldbackground=COLORS["input"],
            foreground=COLORS["text"],
            rowheight=29,
            borderwidth=0,
            relief="flat",
            font=("Segoe UI", 9),
        )
        style.configure(
            "Night.Treeview.Heading",
            background=COLORS["panel_light"],
            foreground=COLORS["blue"],
            relief="flat",
            borderwidth=0,
            padding=(8, 8),
            font=("Segoe UI", 8, "bold"),
        )
        style.map(
            "Night.Treeview",
            background=[("selected", COLORS["accent_dark"])],
            foreground=[("selected", COLORS["text"])],
        )
        for orientation in ("Vertical", "Horizontal"):
            style.configure(
                f"Night.{orientation}.TScrollbar",
                background=COLORS["panel_light"],
                troughcolor=COLORS["input"],
                bordercolor=COLORS["border"],
                lightcolor=COLORS["panel_light"],
                darkcolor=COLORS["border"],
                arrowcolor=COLORS["blue"],
                gripcount=0,
            )
            style.map(
                f"Night.{orientation}.TScrollbar",
                background=[("active", COLORS["accent_dark"])],
            )

    @staticmethod
    def _resource_labels(count):
        return tuple(chr(ord("A") + index) for index in range(count))

    def _music_button_text(self):
        if not self.music_available:
            return "♫ MUSIC: N/A"
        return "♫ MUSIC: ON" if self.music_enabled else "♫ MUSIC: OFF"

    def _button_sounds_text(self):
        if not self.button_sounds_available:
            return "SFX: N/A"
        return "SFX: ON" if self.button_sounds_enabled else "SFX: OFF"

    def _sync_audio_buttons(self):
        if hasattr(self, "music_button"):
            self.music_button.configure(text=self._music_button_text())
        if hasattr(self, "button_sounds_button"):
            self.button_sounds_button.configure(text=self._button_sounds_text())

    def _start_music(self):
        if not self.music_available or winsound is None:
            return False
        try:
            winsound.PlaySound(
                str(self.music_path),
                winsound.SND_FILENAME | winsound.SND_LOOP | winsound.SND_ASYNC,
            )
        except (OSError, RuntimeError):
            return False
        return True

    @staticmethod
    def _stop_music():
        if winsound is not None:
            try:
                winsound.PlaySound(None, 0)
            except (OSError, RuntimeError):
                pass

    def _toggle_music(self):
        self.music_enabled = not self.music_enabled
        if self.music_enabled and not self._start_music():
            self.music_enabled = False
            self._set_feedback("Could not start the included jazz loop.")
        elif not self.music_enabled:
            self._stop_music()
        self._sync_audio_buttons()

    def _toggle_button_sounds(self):
        self.button_sounds_enabled = not self.button_sounds_enabled
        self._sync_audio_buttons()

    def _play_button_sound(self):
        if not self.button_sounds_enabled or winsound is None:
            return

        def play_chime():
            try:
                winsound.Beep(880, 35)
                winsound.Beep(1320, 30)
            except RuntimeError:
                pass

        threading.Thread(target=play_chime, name="button-chime", daemon=True).start()

    def _on_close(self):
        self._stop_music()
        self.root.destroy()

    def _build_layout(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        header = tk.Frame(self.root, bg=COLORS["background"])
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(22, 15))
        header.grid_columnconfigure(1, weight=1)
        logo_frame = tk.Frame(
            header,
            bg=COLORS["panel_light"],
            highlightbackground=COLORS["accent"],
            highlightthickness=2,
        )
        logo_frame.grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 16))
        logo_path = Path(__file__).resolve().with_name("fleischers_finest_five_logo.png")
        try:
            source_logo = tk.PhotoImage(file=str(logo_path))
            scale = max(1, (max(source_logo.width(), source_logo.height()) + 127) // 128)
            self.logo_image = source_logo.subsample(scale, scale)
            tk.Label(
                logo_frame,
                image=self.logo_image,
                bg="#E9DCC3",
                borderwidth=0,
            ).pack(padx=3, pady=3)
        except tk.TclError:
            self.logo_image = None
            tk.Label(
                logo_frame,
                text="F5",
                bg=COLORS["panel_light"],
                fg=COLORS["blue"],
                font=("Segoe UI", 22, "bold"),
                width=5,
                height=3,
            ).pack(padx=5, pady=5)
        tk.Label(
            header,
            text="NEON BANKER’S ALGORITHM",
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Segoe UI", 22, "bold"),
        ).grid(row=0, column=1, sticky="w")
        tk.Label(
            header,
            text="FLEISCHER’S FINEST FIVE  ·  THE BOOP-OOP-A-DOOS  ·  PT 101  ·  TOPIC 5",
            bg=COLORS["background"],
            fg=COLORS["blue"],
            font=("Segoe UI", 8, "bold"),
        ).grid(row=1, column=1, sticky="w", pady=(3, 0))
        tk.Label(
            header,
            text="GROUP 06   •   TOPIC 05",
            bg=COLORS["panel_light"],
            fg=COLORS["accent"],
            font=("Segoe UI", 9, "bold"),
            padx=14,
            pady=9,
        ).grid(row=0, column=2, sticky="e", pady=(0, 4))
        audio_controls = tk.Frame(header, bg=COLORS["background"])
        audio_controls.grid(row=1, column=2, sticky="e")
        self.music_button = self._button(
            audio_controls,
            self._music_button_text(),
            self._toggle_music,
            kind="quiet",
            compact=True,
            enabled=self.music_available,
        )
        self.music_button.pack(side="left", padx=(0, 4))
        self.button_sounds_button = self._button(
            audio_controls,
            self._button_sounds_text(),
            self._toggle_button_sounds,
            kind="quiet",
            compact=True,
            enabled=self.button_sounds_available,
        )
        self.button_sounds_button.pack(side="left")
        tk.Frame(self.root, bg=COLORS["accent"], height=2).grid(
            row=0, column=0, sticky="sew", padx=28
        )

        content = tk.Frame(self.root, bg=COLORS["background"])
        content.grid(row=1, column=0, sticky="nsew", padx=28, pady=(18, 12))
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=11, minsize=590)
        content.grid_columnconfigure(1, weight=10, minsize=500)

        self.left_card = self._card(content)
        self.left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.right_card = self._card(content)
        self.right_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self._build_input_panel()
        self._build_result_panel()

        tk.Label(
            self.root,
            text="TYPE OR CLICK  ·  PROCESS, RESOURCE, AND UNIT LIMITS ARE ENFORCED",
            bg=COLORS["background"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8, "bold"),
        ).grid(row=2, column=0, sticky="e", padx=30, pady=(0, 15))

    @staticmethod
    def _card(parent):
        return tk.Frame(
            parent,
            bg=COLORS["panel"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )

    def _build_input_panel(self):
        self.left_card.grid_rowconfigure(1, weight=1)
        self.left_card.grid_columnconfigure(0, weight=1)
        heading = tk.Frame(self.left_card, bg=COLORS["panel"])
        heading.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 12))
        heading.grid_columnconfigure(0, weight=1)
        tk.Label(
            heading,
            text="01  /  SYSTEM STATE",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, sticky="w")
        self._button(heading, "LOAD SAMPLE", self.load_example, kind="quiet").grid(
            row=0, column=1, sticky="e", padx=(4, 0)
        )
        self._button(heading, "RESET", self.reset_state, kind="quiet").grid(
            row=0, column=2, sticky="e", padx=(4, 0)
        )

        scroll = ScrollableFrame(self.left_card, COLORS["panel"])
        scroll.grid(row=1, column=0, sticky="nsew", padx=(12, 7), pady=(0, 12))
        form = scroll.content
        form.grid_columnconfigure(0, weight=1)

        self.dimensions_frame = tk.Frame(form, bg=COLORS["panel"])
        self.dimensions_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 12))
        self.dimensions_frame.grid_columnconfigure(0, weight=1)
        self.dimensions_frame.grid_columnconfigure(1, weight=1)

        self.totals_frame = tk.Frame(form, bg=COLORS["panel"])
        self.totals_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 12))

        tk.Frame(form, bg=COLORS["border"], height=1).grid(
            row=2, column=0, sticky="ew", padx=8, pady=(0, 13)
        )
        self.matrix_frame = tk.Frame(form, bg=COLORS["panel"])
        self.matrix_frame.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 12))

        self.input_feedback = tk.Label(
            form,
            text="",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            anchor="w",
            justify="left",
            wraplength=560,
            font=("Segoe UI", 9),
        )
        self.input_feedback.grid(row=4, column=0, sticky="ew", padx=9, pady=(3, 10))

    def _build_result_panel(self):
        self.right_card.grid_rowconfigure(6, weight=1)
        self.right_card.grid_columnconfigure(0, weight=1)
        heading = tk.Frame(self.right_card, bg=COLORS["panel"])
        heading.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 12))
        heading.grid_columnconfigure(0, weight=1)
        tk.Label(
            heading,
            text="02  /  SAFETY WORKBENCH",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, sticky="w")
        self._button(
            heading,
            "EXPAND RESULTS",
            self.open_full_table,
            kind="quiet",
            compact=True,
        ).grid(row=0, column=1, sticky="e")

        mode_bar = tk.Frame(self.right_card, bg=COLORS["panel"])
        mode_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))
        self.safety_mode_button = self._button(
            mode_bar, "SAFETY CHECK", lambda: self.set_mode("safety"), kind="active"
        )
        self.safety_mode_button.pack(side="left", padx=(0, 8))
        self.request_mode_button = self._button(
            mode_bar,
            "RESOURCE REQUEST",
            lambda: self.set_mode("request"),
            kind="secondary",
        )
        self.request_mode_button.pack(side="left")

        self.request_frame = tk.Frame(self.right_card, bg=COLORS["panel_light"])
        self.request_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 12))
        self.request_frame.grid_columnconfigure(1, weight=1)
        self.request_frame.grid_remove()

        action_row = tk.Frame(self.right_card, bg=COLORS["panel"])
        action_row.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 15))
        self.run_button = self._button(
            action_row, "RUN SAFETY ALGORITHM", self.run_analysis, kind="primary"
        )
        self.run_button.pack(side="left", fill="x", expand=True)
        self._button(action_row, "CLEAR RESULTS", self.clear_results, kind="quiet").pack(
            side="left", padx=(8, 0)
        )

        summary = tk.Frame(self.right_card, bg=COLORS["panel"])
        summary.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 13))
        summary.grid_columnconfigure(0, weight=1)
        summary.grid_columnconfigure(1, weight=2)
        _, self.available_value = self._stat_card(
            summary, "AVAILABLE", "—", COLORS["blue"]
        )
        self.available_value.master.grid(row=0, column=0, sticky="ew", padx=(0, 7))
        _, self.sequence_value = self._stat_card(
            summary, "SAFE SEQUENCE", "—", COLORS["accent"]
        )
        self.sequence_value.master.grid(row=0, column=1, sticky="ew", padx=(7, 0))

        status_row = tk.Frame(self.right_card, bg=COLORS["panel"])
        status_row.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 9))
        self.status_badge = tk.Label(
            status_row,
            text="READY",
            bg=COLORS["panel_light"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=6,
        )
        self.status_badge.pack(side="left")
        self.status_message = tk.Label(
            status_row,
            text="Type a value or use the buttons. Press Enter or click an app button to apply it.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.status_message.pack(side="left", padx=10, fill="x", expand=True)

        self.output_tabs = ttk.Notebook(self.right_card, style="Night.TNotebook")
        self.output_tabs.grid(row=6, column=0, sticky="nsew", padx=20, pady=(0, 20))

        self.need_tab = tk.Frame(self.output_tabs, bg=COLORS["panel"], padx=8, pady=8)
        self.trace_tab = tk.Frame(self.output_tabs, bg=COLORS["panel"], padx=8, pady=8)
        self.request_tab = tk.Frame(self.output_tabs, bg=COLORS["panel"], padx=8, pady=8)
        self.output_tabs.add(self.need_tab, text="NEED MATRIX")
        self.output_tabs.add(self.trace_tab, text="SAFETY TRACE")
        self.output_tabs.add(self.request_tab, text="REQUEST CHECKS")

        self.result_table_specs = {
            "NEED MATRIX": (
                ("process", "Process", 78, "center"),
                ("allocation", "Allocation", 140, "center"),
                ("maximum", "Max", 140, "center"),
                ("need", "Need = Max − Allocation", 190, "center"),
            ),
            "SAFETY TRACE": (
                ("pass", "Pass", 55, "center"),
                ("process", "Process", 75, "center"),
                ("need", "Need", 105, "center"),
                ("work", "Work before", 105, "center"),
                ("eligible", "Need ≤ Work", 95, "center"),
                ("released", "Released", 100, "center"),
                ("work_after", "Work after", 100, "center"),
                ("finish", "Finish flags", 220, "w"),
            ),
            "REQUEST CHECKS": (
                ("check", "Request check", 160, "w"),
                ("compared", "Compared values", 330, "center"),
                ("result", "Result", 100, "center"),
            ),
        }
        self.need_table = self._make_table(
            self.need_tab, self.result_table_specs["NEED MATRIX"]
        )
        self.trace_table = self._make_table(
            self.trace_tab, self.result_table_specs["SAFETY TRACE"]
        )
        self.request_table = self._make_table(
            self.request_tab, self.result_table_specs["REQUEST CHECKS"]
        )
        self._set_placeholder_rows()

    def _make_table(self, parent, columns, stretch_all=False):
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        table = ttk.Treeview(
            parent,
            columns=tuple(column[0] for column in columns),
            show="headings",
            style="Night.Treeview",
        )
        for column_id, heading, width, anchor in columns:
            table.heading(column_id, text=heading, anchor="center")
            table.column(
                column_id,
                width=width,
                minwidth=min(width, 70),
                anchor=anchor,
                stretch=stretch_all or column_id in {"need", "finish", "compared"},
            )
        vertical = ttk.Scrollbar(
            parent,
            orient="vertical",
            style="Night.Vertical.TScrollbar",
            command=table.yview,
        )
        horizontal = ttk.Scrollbar(
            parent,
            orient="horizontal",
            style="Night.Horizontal.TScrollbar",
            command=table.xview,
        )
        table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        table.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        table.tag_configure("even", background="#130B1D", foreground=COLORS["text"])
        table.tag_configure("odd", background="#1B1028", foreground=COLORS["text"])
        table.tag_configure("pass", foreground=COLORS["accent"])
        table.tag_configure("fail", foreground=COLORS["warning"])
        table.tag_configure("safe", foreground=COLORS["accent"])
        table.tag_configure("unsafe", foreground=COLORS["danger"])
        table.tag_configure("wait", foreground=COLORS["warning"])
        return table

    def open_full_table(self):
        tab_name = self.output_tabs.tab(self.output_tabs.select(), "text")
        tables = {
            "NEED MATRIX": self.need_table,
            "SAFETY TRACE": self.trace_table,
            "REQUEST CHECKS": self.request_table,
        }
        source_table = tables[tab_name]
        columns = self.result_table_specs[tab_name]

        window = tk.Toplevel(self.root)
        window.title(f"{tab_name} | Fleischer’s Finest Five")
        window.configure(bg=COLORS["background"])
        window.geometry("1280x820")
        window.minsize(900, 600)
        try:
            window.state("zoomed")
        except tk.TclError:
            window.geometry("1600x900")

        header = tk.Frame(window, bg=COLORS["background"])
        header.pack(fill="x", padx=24, pady=(20, 14))
        header.grid_columnconfigure(0, weight=1)
        tk.Label(
            header,
            text=tab_name,
            bg=COLORS["background"],
            fg=COLORS["text"],
            font=("Segoe UI", 18, "bold"),
        ).grid(row=0, column=0, sticky="w")
        self._button(
            header,
            "CLOSE FULL VIEW",
            window.destroy,
            kind="quiet",
        ).grid(row=0, column=1, sticky="e")

        table_host = tk.Frame(
            window,
            bg=COLORS["panel"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=10,
            pady=10,
        )
        table_host.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        table_host.grid_rowconfigure(0, weight=1)
        table_host.grid_columnconfigure(0, weight=1)
        table = self._make_table(table_host, columns, stretch_all=True)
        for item in source_table.get_children(""):
            table.insert(
                "",
                "end",
                values=source_table.item(item, "values"),
                tags=source_table.item(item, "tags"),
            )
        window.bind("<Escape>", lambda _event: window.destroy())
        window.lift()

    def _set_placeholder_rows(self):
        self._fill_table(self.need_table, (("—", "Run Safety Check", "", ""),))
        self._fill_table(
            self.trace_table,
            (("—", "—", "—", "—", "—", "—", "—", "Run a check"),),
        )
        self._fill_table(
            self.request_table,
            (("—", "Run Resource Request", "—"),),
        )

    @staticmethod
    def _fill_table(table, rows):
        for item in table.get_children(""):
            table.delete(item)
        for index, values in enumerate(rows):
            table.insert("", "end", values=values, tags=("even" if index % 2 == 0 else "odd",))

    @staticmethod
    def _finish_label(process_ids, flags):
        return "  ".join(
            f"{process_id}={'✓' if finished else '·'}"
            for process_id, finished in zip(process_ids, flags)
        )

    def _populate_need_table(self, state):
        rows = []
        for index, process_id in enumerate(state.process_ids):
            rows.append(
                (
                    process_id,
                    format_vector(state.allocation[index]),
                    format_vector(state.maximum[index]),
                    format_vector(state.need[index]),
                )
            )
        self._fill_table(self.need_table, rows)

    def _populate_trace_table(self, state, result):
        rows = [
            (
                "Start",
                "—",
                "—",
                format_vector(state.available),
                "—",
                "—",
                format_vector(state.available),
                self._finish_label(state.process_ids, (False,) * len(state.process_ids)),
                "even",
            )
        ]
        for event in result.events:
            outcome_tag = "pass" if event.can_finish else "fail"
            rows.append(
                (
                    event.pass_number,
                    event.process_id,
                    format_vector(event.need),
                    format_vector(event.work_before),
                    "YES" if event.can_finish else "NO",
                    format_vector(event.allocation_released) if event.can_finish else "—",
                    format_vector(event.work_after) if event.can_finish else "—",
                    self._finish_label(state.process_ids, event.finish_after),
                    outcome_tag,
                )
            )
        for item in self.trace_table.get_children(""):
            self.trace_table.delete(item)
        for index, row in enumerate(rows):
            self.trace_table.insert(
                "",
                "end",
                values=row[:8],
                tags=(row[8] if row[8] in {"pass", "fail"} else ("even" if index % 2 == 0 else "odd"),),
            )

    def _populate_request_table(self, state, result):
        process_index = state.process_ids.index(result.process_id)
        need = state.need[process_index]
        request = result.request
        checks = [
            ("Request", f"{result.process_id}: {format_vector(request)}", "INPUT"),
            (
                "Request ≤ Need",
                f"{format_vector(request)} ≤ {format_vector(need)}",
                "YES" if vector_leq(request, need) else "NO",
            ),
            (
                "Request ≤ Available",
                f"{format_vector(request)} ≤ {format_vector(state.available)}",
                "YES" if vector_leq(request, state.available) else "NO",
            ),
        ]
        if result.safety_result is None:
            safety_status = "NOT RUN"
        else:
            safety_status = "SAFE" if result.safety_result.safe else "UNSAFE"
        checks.extend(
            [
                ("Tentative safety", "Run Safety Algorithm after provisional allocation", safety_status),
                ("Decision", result.reason, result.status),
            ]
        )
        rows = [
            (
                *check,
                "safe"
                if check[2] in {"YES", "SAFE", "GRANTED"}
                else "unsafe"
                if check[2] in {"NO", "UNSAFE", "REJECTED"}
                else "wait"
                if check[2] == "WAIT"
                else "even",
            )
            for check in checks
        ]
        for item in self.request_table.get_children(""):
            self.request_table.delete(item)
        for index, row in enumerate(rows):
            self.request_table.insert(
                "",
                "end",
                values=row[:3],
                tags=(
                    row[3]
                    if row[3] in {"safe", "unsafe", "wait"}
                    else ("even" if index % 2 == 0 else "odd"),
                ),
            )

    def _render_dimensions(self):
        for child in self.dimensions_frame.winfo_children():
            child.destroy()
        self._section_label(self.dimensions_frame, "PROCESSES", 0, 0)
        self._section_label(self.dimensions_frame, "RESOURCE TYPES", 0, 1)
        self._stepper(
            self.dimensions_frame,
            str(self.process_count),
            lambda: self._resize_dimensions(process_delta=-1),
            lambda: self._resize_dimensions(process_delta=1),
            self.process_count > 1,
            self.process_count < MAX_PROCESSES,
            minimum=1,
            maximum=MAX_PROCESSES,
            bounds=lambda: (1, MAX_PROCESSES),
            on_commit=lambda value, render=False: self._set_dimension_count(
                "process", value, render=render
            ),
            priority=1,
            section="dimensions",
        ).grid(row=1, column=0, sticky="w", padx=(0, 16), pady=(5, 0))
        self._stepper(
            self.dimensions_frame,
            str(self.resource_count),
            lambda: self._resize_dimensions(resource_delta=-1),
            lambda: self._resize_dimensions(resource_delta=1),
            self.resource_count > 1,
            self.resource_count < MAX_RESOURCES,
            minimum=1,
            maximum=MAX_RESOURCES,
            bounds=lambda: (1, MAX_RESOURCES),
            on_commit=lambda value, render=False: self._set_dimension_count(
                "resource", value, render=render
            ),
            priority=1,
            section="dimensions",
        ).grid(row=1, column=1, sticky="w", padx=(0, 8), pady=(5, 0))
        tk.Label(
            self.dimensions_frame,
            text=f"Limits: 1–{MAX_PROCESSES} processes · 1–{MAX_RESOURCES} resources",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(7, 0))

    def _render_totals(self):
        for child in self.totals_frame.winfo_children():
            child.destroy()
        self.totals_frame.grid_columnconfigure(0, weight=1)
        tk.Label(
            self.totals_frame,
            text="TOTAL RESOURCES",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(2, 7))
        vector_row = tk.Frame(self.totals_frame, bg=COLORS["panel"])
        vector_row.grid(row=1, column=0, sticky="w")
        for index, resource in enumerate(self.resource_ids):
            column_total = sum(row[index] for row in self.allocation)
            group = tk.Frame(vector_row, bg=COLORS["panel_light"], padx=8, pady=6)
            group.pack(side="left", padx=(0, 7))
            tk.Label(
                group,
                text=resource,
                bg=COLORS["panel_light"],
                fg=COLORS["blue"],
                font=("Segoe UI", 8, "bold"),
            ).pack(anchor="center", pady=(0, 2))
            self._stepper(
                group,
                str(self.total[index]),
                lambda i=index: self._adjust_total(i, -1),
                lambda i=index: self._adjust_total(i, 1),
                self.total[index] > column_total,
                self.total[index] < MAX_UNITS,
                compact=True,
                minimum=column_total,
                maximum=MAX_UNITS,
                bounds=lambda i=index: (
                    sum(row[i] for row in self.allocation),
                    MAX_UNITS,
                ),
                on_commit=lambda value, render=False, i=index: self._set_total_value(
                    i, value, render=render
                ),
                section="totals",
            ).pack()
        tk.Label(
            self.totals_frame,
            text=f"Each resource total is limited to 0–{MAX_UNITS}; Total cannot drop below allocated units.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
        ).grid(row=2, column=0, sticky="w", pady=(7, 0))

    def _render_matrix(self):
        for child in self.matrix_frame.winfo_children():
            child.destroy()
        resource_count = self.resource_count
        tk.Label(
            self.matrix_frame,
            text="ALLOCATION AND MAX MATRICES",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=0, columnspan=1 + 2 * resource_count, sticky="w", pady=(0, 4))
        tk.Label(
            self.matrix_frame,
            text="Type a value or use the buttons. Allocation cannot exceed Max or Total.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
        ).grid(row=1, column=0, columnspan=1 + 2 * resource_count, sticky="w", pady=(0, 8))

        self._cell_label(self.matrix_frame, "PROCESS", 2, 0, COLORS["muted"])
        allocation_title = tk.Label(
            self.matrix_frame,
            text="ALLOCATION",
            bg=COLORS["panel"],
            fg=COLORS["blue"],
            font=("Segoe UI", 8, "bold"),
            anchor="center",
        )
        allocation_title.grid(row=2, column=1, columnspan=resource_count, sticky="ew", pady=(0, 4))
        maximum_title = tk.Label(
            self.matrix_frame,
            text="MAX",
            bg=COLORS["panel"],
            fg=COLORS["accent"],
            font=("Segoe UI", 8, "bold"),
            anchor="center",
        )
        maximum_title.grid(
            row=2,
            column=resource_count + 1,
            columnspan=resource_count,
            sticky="ew",
            pady=(0, 4),
        )
        self._cell_label(self.matrix_frame, "", 3, 0, COLORS["muted"])
        for index, resource in enumerate(self.resource_ids):
            self._cell_label(self.matrix_frame, resource, 3, index + 1, COLORS["muted"])
            self._cell_label(
                self.matrix_frame,
                resource,
                3,
                resource_count + index + 1,
                COLORS["muted"],
            )

        for process_index in range(self.process_count):
            row = process_index + 4
            process_id = f"P{process_index}"
            self._cell_label(self.matrix_frame, process_id, row, 0, COLORS["text"])
            for resource_index in range(resource_count):
                allocated = self.allocation[process_index][resource_index]
                max_claim = self.maximum[process_index][resource_index]
                allocated_in_column = sum(
                    self.allocation[p][resource_index] for p in range(self.process_count)
                )
                other_allocated = allocated_in_column - allocated
                allocation_limit = min(
                    max_claim,
                    self.total[resource_index] - other_allocated,
                    MAX_UNITS,
                )
                self._stepper(
                    self.matrix_frame,
                    str(allocated),
                    lambda p=process_index, r=resource_index: self._adjust_allocation(p, r, -1),
                    lambda p=process_index, r=resource_index: self._adjust_allocation(p, r, 1),
                    allocated > 0,
                    allocated < allocation_limit,
                    compact=True,
                    minimum=0,
                    maximum=allocation_limit,
                    bounds=lambda p=process_index, r=resource_index: (
                        0,
                        min(
                            self.maximum[p][r],
                            self.total[r]
                            - sum(
                                self.allocation[other][r]
                                for other in range(self.process_count)
                                if other != p
                            ),
                            MAX_UNITS,
                        ),
                    ),
                    on_commit=lambda value, render=False, p=process_index, r=resource_index: self._set_allocation_value(
                        p, r, value, render=render
                    ),
                    section="matrix",
                ).grid(row=row, column=resource_index + 1, padx=1, pady=2)
                self._stepper(
                    self.matrix_frame,
                    str(max_claim),
                    lambda p=process_index, r=resource_index: self._adjust_maximum(p, r, -1),
                    lambda p=process_index, r=resource_index: self._adjust_maximum(p, r, 1),
                    max_claim > allocated,
                    max_claim < MAX_UNITS,
                    compact=True,
                    minimum=allocated,
                    maximum=MAX_UNITS,
                    bounds=lambda p=process_index, r=resource_index: (
                        self.allocation[p][r],
                        MAX_UNITS,
                    ),
                    on_commit=lambda value, render=False, p=process_index, r=resource_index: self._set_maximum_value(
                        p, r, value, render=render
                    ),
                    section="matrix",
                ).grid(row=row, column=resource_count + resource_index + 1, padx=1, pady=2)

    def _render_request_controls(self):
        self._pending_edits = [
            edit for edit in self._pending_edits if edit["section"] != "request"
        ]
        for child in self.request_frame.winfo_children():
            child.destroy()
        self.request_frame.grid_columnconfigure(0, weight=1)
        tk.Label(
            self.request_frame,
            text="REQUEST INPUTS  ·  OPTIONAL EXTENSION",
            bg=COLORS["panel_light"],
            fg=COLORS["text"],
            font=("Segoe UI", 8, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 6))

        process_row = tk.Frame(self.request_frame, bg=COLORS["panel_light"])
        process_row.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))
        tk.Label(
            process_row,
            text="PROCESS",
            bg=COLORS["panel_light"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8, "bold"),
        ).pack(side="left", padx=(0, 8))
        self._button(
            process_row,
            "‹",
            lambda: self._change_request_process(-1),
            kind="secondary",
            compact=True,
            enabled=self.request_process > 0,
        ).pack(side="left")
        tk.Label(
            process_row,
            text=f"P{self.request_process}",
            bg=COLORS["panel_light"],
            fg=COLORS["accent"],
            font=("Segoe UI", 11, "bold"),
            width=5,
        ).pack(side="left", padx=4)
        self._button(
            process_row,
            "›",
            lambda: self._change_request_process(1),
            kind="secondary",
            compact=True,
            enabled=self.request_process < self.process_count - 1,
        ).pack(side="left")

        vector_row = tk.Frame(self.request_frame, bg=COLORS["panel_light"])
        vector_row.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 10))
        for index, resource in enumerate(self.resource_ids):
            group = tk.Frame(vector_row, bg=COLORS["panel"] , padx=7, pady=5)
            group.pack(side="left", padx=(0, 6))
            tk.Label(
                group,
                text=resource,
                bg=COLORS["panel"],
                fg=COLORS["muted"],
                font=("Segoe UI", 8, "bold"),
            ).pack(anchor="center", pady=(0, 2))
            self._stepper(
                group,
                str(self.request[index]),
                lambda i=index: self._adjust_request(i, -1),
                lambda i=index: self._adjust_request(i, 1),
                self.request[index] > 0,
                self.request[index] < MAX_UNITS,
                compact=True,
                minimum=0,
                maximum=MAX_UNITS,
                bounds=lambda: (0, MAX_UNITS),
                on_commit=lambda value, render=False, i=index: self._set_request_value(
                    i, value, render=render
                ),
                section="request",
            ).pack()

    def _render_all_controls(self):
        self._pending_edits = []
        self._render_dimensions()
        self._render_totals()
        self._render_matrix()
        self._render_request_controls()

    def _resize_dimensions(self, process_delta=0, resource_delta=0, render=True):
        new_process_count = max(1, min(MAX_PROCESSES, self.process_count + process_delta))
        new_resource_count = max(1, min(MAX_RESOURCES, self.resource_count + resource_delta))
        old_allocation = self.allocation
        old_maximum = self.maximum
        old_total = self.total
        old_request = self.request

        self.process_count = new_process_count
        self.resource_count = new_resource_count
        self.resource_ids = self._resource_labels(new_resource_count)
        self.allocation = [
            [old_allocation[p][r] if p < len(old_allocation) and r < len(old_allocation[p]) else 0
             for r in range(new_resource_count)]
            for p in range(new_process_count)
        ]
        self.maximum = [
            [old_maximum[p][r] if p < len(old_maximum) and r < len(old_maximum[p]) else 0
             for r in range(new_resource_count)]
            for p in range(new_process_count)
        ]
        self.total = [
            old_total[r] if r < len(old_total) else 0
            for r in range(new_resource_count)
        ]
        self.request = [
            old_request[r] if r < len(old_request) else 0
            for r in range(new_resource_count)
        ]
        self.request_process = min(self.request_process, self.process_count - 1)
        if render:
            self._render_all_controls()
            self._mark_input_changed("Dimensions updated. Existing matching cells were preserved.")

    def _set_dimension_count(self, dimension, value, render=False):
        if dimension == "process":
            value = max(1, min(MAX_PROCESSES, value))
            self._resize_dimensions(process_delta=value - self.process_count, render=render)
            return self.process_count
        value = max(1, min(MAX_RESOURCES, value))
        self._resize_dimensions(resource_delta=value - self.resource_count, render=render)
        return self.resource_count

    def _set_total_value(self, resource_index, value, render=False):
        allocated = sum(row[resource_index] for row in self.allocation)
        value = max(allocated, min(MAX_UNITS, value))
        changed = value != self.total[resource_index]
        self.total[resource_index] = value
        if render and changed:
            self._render_all_controls()
            self._mark_input_changed("Total resources updated.")
        return value

    def _set_allocation_value(self, process_index, resource_index, value, render=False):
        allocated_elsewhere = sum(
            self.allocation[p][resource_index]
            for p in range(self.process_count)
            if p != process_index
        )
        limit = min(
            self.maximum[process_index][resource_index],
            self.total[resource_index] - allocated_elsewhere,
            MAX_UNITS,
        )
        value = max(0, min(limit, value))
        changed = value != self.allocation[process_index][resource_index]
        self.allocation[process_index][resource_index] = value
        if render and changed:
            self._render_all_controls()
            self._mark_input_changed("Allocation updated.")
        return value

    def _set_maximum_value(self, process_index, resource_index, value, render=False):
        minimum = self.allocation[process_index][resource_index]
        value = max(minimum, min(MAX_UNITS, value))
        changed = value != self.maximum[process_index][resource_index]
        self.maximum[process_index][resource_index] = value
        if render and changed:
            self._render_all_controls()
            self._mark_input_changed("Maximum claim updated.")
        return value

    def _set_request_value(self, resource_index, value, render=False):
        value = max(0, min(MAX_UNITS, value))
        changed = value != self.request[resource_index]
        self.request[resource_index] = value
        if render and changed:
            self._render_request_controls()
            self._mark_input_changed("Request vector updated.")
        return value

    def _adjust_total(self, resource_index, delta):
        allocated = sum(row[resource_index] for row in self.allocation)
        candidate = self.total[resource_index] + delta
        if allocated <= candidate <= MAX_UNITS:
            self.total[resource_index] = candidate
            self._render_all_controls()
            self._mark_input_changed("Total resources updated.")

    def _adjust_allocation(self, process_index, resource_index, delta):
        candidate = self.allocation[process_index][resource_index] + delta
        allocated_elsewhere = sum(
            self.allocation[p][resource_index]
            for p in range(self.process_count)
            if p != process_index
        )
        limit = min(
            self.maximum[process_index][resource_index],
            self.total[resource_index] - allocated_elsewhere,
            MAX_UNITS,
        )
        if 0 <= candidate <= limit:
            self.allocation[process_index][resource_index] = candidate
            self._render_all_controls()
            self._mark_input_changed("Allocation updated.")

    def _adjust_maximum(self, process_index, resource_index, delta):
        candidate = self.maximum[process_index][resource_index] + delta
        minimum = self.allocation[process_index][resource_index]
        if minimum <= candidate <= MAX_UNITS:
            self.maximum[process_index][resource_index] = candidate
            self._render_all_controls()
            self._mark_input_changed("Maximum claim updated.")

    def _adjust_request(self, resource_index, delta):
        candidate = self.request[resource_index] + delta
        if 0 <= candidate <= MAX_UNITS:
            self.request[resource_index] = candidate
            self._render_request_controls()
            self._mark_input_changed("Request vector updated.")

    def _change_request_process(self, delta):
        candidate = self.request_process + delta
        if 0 <= candidate < self.process_count:
            self.request_process = candidate
            self._render_request_controls()
            self._mark_input_changed("Requesting process updated.")

    @staticmethod
    def _section_label(parent, text, row, column):
        tk.Label(
            parent,
            text=text,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8, "bold"),
        ).grid(row=row, column=column, sticky="w", padx=(0, 8))

    def _cell_label(self, parent, text, row, column, color):
        tk.Label(
            parent,
            text=text,
            bg=COLORS["panel"],
            fg=color,
            font=("Segoe UI", 8, "bold"),
            anchor="center" if column else "w",
        ).grid(row=row, column=column, padx=(3, 4), pady=2, sticky="ew")

    def _stepper(
        self,
        parent,
        value,
        decrement,
        increment,
        can_decrement,
        can_increment,
        compact=False,
        minimum=0,
        maximum=MAX_UNITS,
        bounds=None,
        on_commit=None,
        priority=0,
        section="matrix",
    ):
        frame = tk.Frame(parent, bg=parent.cget("bg"))
        button_padx = 3 if compact else 5
        button_pady = 2 if compact else 4
        self._button(
            frame,
            "−",
            decrement,
            kind="step",
            compact=compact,
            enabled=can_decrement,
        ).pack(side="left", padx=(0, button_padx))
        value_var = tk.StringVar(value=str(value))
        validate_command = (self._integer_validator, "%P")
        entry = tk.Entry(
            frame,
            textvariable=value_var,
            validate="key",
            validatecommand=validate_command,
            bg=COLORS["input"],
            fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            selectbackground=COLORS["accent_dark"],
            selectforeground=COLORS["text"],
            font=("Consolas", 10 if compact else 12, "bold"),
            width=3 if compact else 5,
            justify="center",
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"],
        )
        entry.pack(side="left", padx=(0, button_padx), ipady=button_pady)
        self._pending_edits.append(
            {
                "variable": value_var,
                "original": int(value),
                "bounds": bounds or (lambda: (minimum, maximum)),
                "apply": on_commit,
                "priority": priority,
                "section": section,
            }
        )

        def commit_on_enter(_event=None):
            self._commit_pending_entries()
            return "break"

        entry.bind("<Return>", commit_on_enter)
        entry.bind("<KP_Enter>", commit_on_enter)
        self._button(
            frame,
            "+",
            increment,
            kind="step",
            compact=compact,
            enabled=can_increment,
        ).pack(side="left", padx=(button_padx, 0))
        return frame

    @staticmethod
    def _validate_integer_text(proposed):
        return proposed == "" or (
            len(proposed) <= 3 and all("0" <= char <= "9" for char in proposed)
        )

    def _commit_pending_entries(self):
        if not self._pending_edits:
            return

        edits = sorted(self._pending_edits, key=lambda edit: edit["priority"])
        changed = False
        for edit in edits:
            raw = edit["variable"].get().strip()
            try:
                candidate = int(raw) if raw else 0
            except ValueError:
                candidate = 0
            minimum, maximum = edit["bounds"]()
            candidate = max(minimum, min(maximum, candidate))
            apply_value = edit["apply"]
            actual = candidate if apply_value is None else apply_value(candidate, render=False)
            edit["variable"].set(str(actual))
            if actual != edit["original"]:
                changed = True

        if changed:
            self._render_all_controls()
            self._mark_input_changed("Typed values applied. Run the selected check to recalculate.")
        else:
            self._pending_edits = edits

    def _button(self, parent, text, command, kind="secondary", compact=False, enabled=True):
        palette = {
            "primary": (COLORS["accent"], COLORS["background"], COLORS["accent"]),
            "active": (COLORS["accent_dark"], COLORS["accent"], COLORS["accent_dark"]),
            "secondary": (COLORS["panel_light"], COLORS["text"], COLORS["border"]),
            "quiet": (COLORS["panel"], COLORS["muted"], COLORS["panel"]),
            "step": (COLORS["panel_light"], COLORS["accent"], COLORS["accent_dark"]),
        }
        background, foreground, active = palette[kind]

        def invoke():
            self._play_button_sound()
            self._commit_pending_entries()
            command()

        return tk.Button(
            parent,
            text=text,
            command=invoke,
            state=tk.NORMAL if enabled else tk.DISABLED,
            bg=background,
            fg=foreground,
            disabledforeground=COLORS["disabled"],
            activebackground=active,
            activeforeground=foreground,
            relief="flat",
            borderwidth=0,
            cursor="hand2" if enabled else "arrow",
            padx=8 if compact else 13,
            pady=4 if compact else 9,
            font=("Segoe UI", 9 if compact else 9, "bold"),
        )

    @staticmethod
    def _stat_card(parent, label, value, color):
        card = tk.Frame(
            parent,
            bg=COLORS["panel_light"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        tk.Label(
            card,
            text=label,
            bg=COLORS["panel_light"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=12, pady=(10, 2))
        value_label = tk.Label(
            card,
            text=value,
            bg=COLORS["panel_light"],
            fg=color,
            font=("Segoe UI", 13, "bold"),
            anchor="w",
            justify="left",
            wraplength=360,
        )
        value_label.pack(anchor="w", padx=12, pady=(0, 10))
        return card, value_label

    def _make_state(self):
        return BankerState(
            process_ids=tuple(f"P{index}" for index in range(self.process_count)),
            resource_ids=self.resource_ids,
            total=tuple(self.total),
            allocation=tuple(tuple(row) for row in self.allocation),
            maximum=tuple(tuple(row) for row in self.maximum),
        )

    def load_example(self):
        self.process_count = 5
        self.resource_count = 3
        self.resource_ids = self._resource_labels(self.resource_count)
        self.total = [10, 5, 7]
        self.allocation = [
            [0, 1, 0],
            [2, 0, 0],
            [3, 0, 2],
            [2, 1, 1],
            [0, 0, 2],
        ]
        self.maximum = [
            [7, 5, 3],
            [3, 2, 2],
            [9, 0, 2],
            [2, 2, 2],
            [4, 3, 3],
        ]
        self.request_process = 1
        self.request = [1, 0, 2]
        self.mode = "safety"
        self._render_all_controls()
        self.set_mode("safety")
        self._reset_summary()
        self._set_badge("READY", COLORS["muted"])
        self.status_message.config(text="Sample loaded. Run a check to calculate results.")
        self._clear_result_tables()

    def reset_state(self):
        self.total = [0] * self.resource_count
        self.allocation = [[0] * self.resource_count for _ in range(self.process_count)]
        self.maximum = [[0] * self.resource_count for _ in range(self.process_count)]
        self.request = [0] * self.resource_count
        self.request_process = 0
        self._render_all_controls()
        self._reset_summary()
        self._set_badge("READY", COLORS["muted"])
        self.status_message.config(text="State reset. Type values or use the stepper buttons.")
        self._clear_result_tables()

    def set_mode(self, mode):
        self.mode = mode
        if mode == "request":
            self.request_frame.grid()
            self.safety_mode_button.configure(bg=COLORS["panel_light"], fg=COLORS["text"])
            self.request_mode_button.configure(bg=COLORS["accent_dark"], fg=COLORS["accent"])
            self.run_button.configure(text="CHECK RESOURCE REQUEST")
        else:
            self.request_frame.grid_remove()
            self.safety_mode_button.configure(bg=COLORS["accent_dark"], fg=COLORS["accent"])
            self.request_mode_button.configure(bg=COLORS["panel_light"], fg=COLORS["text"])
            self.run_button.configure(text="RUN SAFETY ALGORITHM")

    def run_analysis(self):
        state = self._make_state()
        self.available_value.config(text=format_vector(state.available))
        self._populate_need_table(state)

        if self.mode == "safety":
            result = check_safety(state)
            self._populate_trace_table(state, result)
            self._fill_table(
                self.request_table,
                (("—", "Choose Resource Request and run the check", "—"),),
            )
            self.output_tabs.select(self.trace_tab)
            if result.safe:
                self._set_badge("SAFE", COLORS["accent"])
                self.status_message.config(text="Every process can finish in this state.")
                self.sequence_value.config(text=" → ".join(result.safe_sequence))
            else:
                unfinished = [
                    process_id
                    for process_id, finished in zip(state.process_ids, result.finish)
                    if not finished
                ]
                self._set_badge("UNSAFE", COLORS["danger"])
                self.status_message.config(
                    text="No safe completion order. Unfinished: " + ", ".join(unfinished)
                )
                self.sequence_value.config(text="No safe sequence")
        else:
            result = check_request(state, self.request_process, tuple(self.request))
            colors = {
                "GRANTED": COLORS["accent"],
                "WAIT": COLORS["warning"],
                "REJECTED": COLORS["danger"],
            }
            self._set_badge(result.status, colors[result.status])
            self.status_message.config(text=result.reason)
            self._populate_request_table(state, result)
            if result.safety_result is not None:
                trace_state = result.tentative_state or state
                self._populate_need_table(trace_state)
                self._populate_trace_table(trace_state, result.safety_result)
                self.sequence_value.config(
                    text=(
                        " → ".join(result.safety_result.safe_sequence)
                        if result.safety_result.safe
                        else "Request not granted"
                    )
                )
            else:
                self._fill_table(
                    self.trace_table,
                    (("—", "—", "—", "—", "—", "—", "—", "Safety check not run for this request"),),
                )
                self.sequence_value.config(text="—")
            self.output_tabs.select(self.request_tab)
        self._set_feedback("Calculation complete.")

    def clear_results(self):
        self._reset_summary()
        self._set_badge("READY", COLORS["muted"])
        self.status_message.config(text="Run a check to see the calculation trace.")
        self._clear_result_tables()

    def _mark_input_changed(self, message):
        self._reset_summary()
        self._set_badge("INPUT CHANGED", COLORS["warning"])
        self.status_message.config(text=message)
        self._clear_result_tables()
        self._set_feedback(message)

    def _reset_summary(self):
        self.available_value.config(text="—")
        self.sequence_value.config(text="—")

    def _set_badge(self, text, color):
        self.status_badge.configure(text=text, fg=color)

    def _set_feedback(self, message):
        self.input_feedback.configure(text=message)

    def _clear_result_tables(self):
        self._set_placeholder_rows()
        self.output_tabs.select(self.need_tab)


def main():
    root = tk.Tk()
    BankersGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
