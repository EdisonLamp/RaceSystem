"""
Renn-Dashboard - NiceGUI Web-GUI
==================================
Nachbau der bereitgestellten UI-Vorlage (4-Spalten Renn-/Rundenzeiten-Anzeige)
mit NiceGUI.

Korrekturen gegenüber der Vorlage:
- "ZURÜCK-SETZEN" -> "Zurücksetzen" (falscher Trennstrich entfernt, ist ein
  zusammengeschriebenes Wort)
- Einheitliche Groß-/Kleinschreibung bei allen Buttons (nur Substantive groß)
- Einheitliche Abstände (Gaps/Paddings) zwischen allen Panels, Labels und der
  Buttonleiste
- Die Gesamt-Rundenzeit (Standard 05:00) ist jetzt klickbar/editierbar
- Die Zeitenlisten je Fahrer sind Single-Select (nur ein Eintrag pro Liste
  gleichzeitig markierbar)

Start:
    pip install nicegui
    python renn_dashboard.py
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from nicegui import ui

# --------------------------------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------------------------------

def format_time(seconds: float) -> str:
    """Formatiert Sekunden als '000,00' (3 Stellen, Komma, 2 Nachkommastellen)."""
    seconds = max(0.0, seconds)
    return f"{seconds:06.2f}".replace(".", ",")


def format_mmss(seconds: float) -> str:
    """Formatiert Sekunden als 'MM:SS'."""
    seconds = max(0, int(round(seconds)))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


# --------------------------------------------------------------------------
# Fahrer-Panel (eine der 4 Spalten)
# --------------------------------------------------------------------------

class RacerPanel:
    def __init__(self, number: int) -> None:
        self.number = number
        self.name = "Mustermann"
        self.current_time = 0.0
        self.best_time = 0.0
        self.rounds = 0
        self.laps: list[float] = []
        self.selected_lap: Optional[int] = None

        self._build()

    # -- UI-Aufbau ---------------------------------------------------------
    def _build(self) -> None:
        with ui.column().classes("items-center flex-1 gap-2"):
            ui.label(str(self.number)).classes("panel-number")

            with ui.column().classes("panel-card items-center w-full"):
                ui.input(value=self.name,
                          on_change=lambda e: setattr(self, "name", e.value)) \
                    .classes("name-input") \
                    .props('borderless input-class="text-center text-white text-lg"')

                self.current_label = ui.label(format_time(self.current_time)) \
                    .classes("current-time")

                ui.label("Bestzeit").classes("sub-label")
                self.best_label = ui.label(format_time(self.best_time)) \
                    .classes("best-time")

                ui.label("Runden").classes("sub-label")
                self.rounds_label = ui.label(f"{self.rounds:03d}") \
                    .classes("rounds-value")

                self.laps_container = ui.column().classes("lap-list w-full gap-0")
                self._render_laps()

    def _render_laps(self) -> None:
        self.laps_container.clear()
        with self.laps_container:
            if not self.laps:
                ui.label("Noch keine Zeiten").classes("lap-empty")
            for idx, lap in enumerate(self.laps):
                row_classes = "lap-row"
                if idx == self.selected_lap:
                    row_classes += " selected"
                with ui.row().classes(row_classes).on(
                        "click", lambda e, idx=idx: self._select_lap(idx)):
                    ui.label(f"{idx + 1}.").classes("lap-index")
                    ui.label(format_time(lap)).classes("lap-value")

    # -- Interaktion ---------------------------------------------------------
    def _select_lap(self, idx: int) -> None:
        # Nur ein Eintrag pro Liste kann gleichzeitig markiert sein.
        # Erneuter Klick auf denselben Eintrag hebt die Markierung wieder auf.
        self.selected_lap = None if self.selected_lap == idx else idx
        self._render_laps()

    def add_lap(self, seconds: float) -> None:
        self.laps.append(seconds)
        self.rounds = len(self.laps)
        self.current_time = seconds
        if self.best_time == 0 or seconds < self.best_time:
            self.best_time = seconds
        self._refresh_labels()

    def delete_selected(self) -> bool:
        if self.selected_lap is None or not (0 <= self.selected_lap < len(self.laps)):
            return False
        del self.laps[self.selected_lap]
        self.selected_lap = None
        self.rounds = len(self.laps)
        self.best_time = min(self.laps) if self.laps else 0.0
        self._refresh_labels()
        return True

    def reset(self) -> None:
        self.current_time = 0.0
        self.best_time = 0.0
        self.rounds = 0
        self.laps.clear()
        self.selected_lap = None
        self._refresh_labels()

    def _refresh_labels(self) -> None:
        self.current_label.text = format_time(self.current_time)
        self.best_label.text = format_time(self.best_time)
        self.rounds_label.text = f"{self.rounds:03d}"
        self._render_laps()


# --------------------------------------------------------------------------
# Globaler Zustand für die Runden-Uhr
# --------------------------------------------------------------------------

class RaceClock:
    def __init__(self) -> None:
        self.total_seconds = 5 * 60  # Standard 05:00
        self.elapsed_seconds = 0.0
        self.running = False

    def start(self) -> None:
        self.elapsed_seconds = 0.0
        self.running = True

    def stop(self) -> None:
        self.running = False

    def reset(self) -> None:
        self.elapsed_seconds = 0.0
        self.running = False

    def tick(self, dt: float) -> None:
        if not self.running:
            return
        self.elapsed_seconds += dt
        if self.elapsed_seconds >= self.total_seconds:
            self.elapsed_seconds = self.total_seconds
            self.running = False


# --------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------

def build_app() -> None:
    ui.dark_mode().enable()

    ui.add_head_html("""
    <style>
        body {
            background-color: #0b0b0b;
            background-image: radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px);
            background-size: 10px 10px;
        }
        .panel-number {
            font-size: 2rem;
            font-weight: 800;
            color: white;
        }
        .panel-card {
            background: linear-gradient(180deg, rgba(150,40,40,0.85), rgba(65,14,14,0.9));
            border-radius: 16px;
            padding: 28px 22px;
            gap: 6px;
        }
        .name-input input {
            text-align: center;
        }
        .current-time {
            font-size: 2.5rem;
            font-weight: 700;
            color: white;
            margin: 10px 0 4px 0;
        }
        .sub-label {
            color: rgba(255,255,255,0.65);
            font-size: 0.85rem;
            margin-top: 10px;
        }
        .best-time, .rounds-value {
            font-size: 1.7rem;
            font-weight: 600;
            color: white;
        }
        .lap-list {
            background: rgba(0,0,0,0.35);
            border-radius: 10px;
            padding: 12px 16px;
            margin-top: 18px;
            width: 100%;
        }
        .lap-row {
            display: flex;
            justify-content: space-between;
            padding: 5px 8px;
            border-radius: 6px;
            cursor: pointer;
            color: rgba(255,255,255,0.85);
            transition: background 0.15s ease;
        }
        .lap-row:hover {
            background: rgba(255,255,255,0.08);
        }
        .lap-row.selected {
            background: rgba(255, 196, 64, 0.35);
            color: white;
        }
        .lap-empty {
            color: rgba(255,255,255,0.4);
            font-size: 0.85rem;
            text-align: center;
            padding: 6px;
        }
        .round-timer {
            font-size: 2.6rem;
            font-weight: 700;
            color: white;
        }
        .round-duration {
            font-size: 1.3rem;
            color: rgba(255,255,255,0.7);
            cursor: pointer;
            border-bottom: 1px dashed rgba(255,255,255,0.35);
        }
        .round-duration:hover {
            color: white;
        }
        .menu-bar {
            border: 1px dashed rgba(255,255,255,0.3);
            border-radius: 12px;
            padding: 18px 24px;
        }
        .menu-btn {
            min-width: 150px;
            font-weight: 700;
        }
        .clock-label {
            font-size: 1.6rem;
            font-weight: 600;
            color: white;
        }
    </style>
    """)

    clock = RaceClock()

    # -- Kopfzeile -----------------------------------------------------------
    with ui.row().classes("w-full items-center justify-between px-6 pt-6"):
        ui.icon("cloud_sync").classes("text-4xl").style("color:#e07a5f")
        clock_label = ui.label(datetime.now().strftime("%H:%M")).classes("clock-label")

    def update_clock() -> None:
        clock_label.text = datetime.now().strftime("%H:%M")

    ui.timer(1.0, update_clock)

    # -- Dialog zum Bearbeiten der Rundenzeit ---------------------------------
    with ui.dialog() as duration_dialog, ui.card():
        ui.label("Rundenzeit festlegen").classes("text-lg font-bold")
        with ui.row().classes("items-center gap-2"):
            minutes_input = ui.number(label="Minuten", value=5, min=0, max=59).classes("w-24")
            seconds_input = ui.number(label="Sekunden", value=0, min=0, max=59).classes("w-24")
        with ui.row().classes("justify-end w-full gap-2"):
            ui.button("Abbrechen", on_click=duration_dialog.close).props("flat")

            def apply_duration() -> None:
                clock.total_seconds = int(minutes_input.value or 0) * 60 + int(seconds_input.value or 0)
                duration_label.text = format_mmss(clock.total_seconds)
                duration_dialog.close()

            ui.button("Übernehmen", on_click=apply_duration).props("color=primary")

    def open_duration_dialog() -> None:
        minutes_input.value = clock.total_seconds // 60
        seconds_input.value = clock.total_seconds % 60
        duration_dialog.open()

    # -- Hauptbereich: Sidebar + 4 Fahrer-Panels -----------------------------
    with ui.row().classes("w-full flex-1 px-6 gap-8 items-start"):
        # Sidebar
        with ui.column().classes("items-start gap-2 pt-4"):
            ui.label("Aktuelle Runde").classes("text-white text-lg")
            timer_label = ui.label(format_mmss(clock.elapsed_seconds)).classes("round-timer")
            duration_label = ui.label(format_mmss(clock.total_seconds)) \
                .classes("round-duration") \
                .on("click", open_duration_dialog)
            ui.tooltip("Klicken zum Bearbeiten")

        # 4 Fahrer-Panels
        racers = [RacerPanel(i) for i in range(1, 5)]

    def tick(dt: float = 0.1) -> None:
        clock.tick(dt)
        timer_label.text = format_mmss(clock.elapsed_seconds)

    ui.timer(0.1, tick)

    # -- Buttonleiste ----------------------------------------------------------
    def action_delete_entry() -> None:
        deleted_any = False
        for racer in racers:
            if racer.delete_selected():
                deleted_any = True
        ui.notify("Eintrag gelöscht" if deleted_any else "Kein Eintrag markiert",
                   type="positive" if deleted_any else "warning")

    def action_load_data() -> None:
        ui.notify("Daten laden ist als Platzhalter vorgesehen (z. B. Datei-Upload)",
                   type="info")

    def action_start_race() -> None:
        clock.start()
        ui.notify("Rennen gestartet", type="positive")

    def action_save_times() -> None:
        for racer in racers:
            racer.add_lap(clock.elapsed_seconds)
        clock.elapsed_seconds = 0.0
        ui.notify("Zeiten gespeichert", type="positive")

    def action_end_race() -> None:
        clock.stop()
        ui.notify("Rennen beendet", type="warning")

    def action_reset_all() -> None:
        clock.reset()
        timer_label.text = format_mmss(clock.elapsed_seconds)
        for racer in racers:
            racer.reset()
        ui.notify("Alles zurückgesetzt", type="negative")

    with ui.row().classes("w-full justify-center px-6 pb-4 pt-2"):
        with ui.row().classes("menu-bar gap-4"):
            ui.button("Eintrag löschen", on_click=action_delete_entry) \
                .props("color=red-9").classes("menu-btn")
            ui.button("Daten laden", on_click=action_load_data) \
                .props("color=green-8").classes("menu-btn")
            ui.button("Rennen starten", on_click=action_start_race) \
                .props("color=green-8").classes("menu-btn")
            ui.button("Zeiten speichern", on_click=action_save_times) \
                .props("color=green-8").classes("menu-btn")
            ui.button("Rennen beenden", on_click=action_end_race) \
                .props("color=red-9").classes("menu-btn")
            ui.button("Zurücksetzen", on_click=action_reset_all) \
                .props("color=red-9").classes("menu-btn")

    # -- Einstellungen (Zahnrad unten rechts) -----------------------------
    with ui.row().classes("fixed bottom-4 right-6"):
        ui.button(icon="settings", on_click=open_duration_dialog) \
            .props("flat round color=grey-5")


build_app()

ui.run(title="Renn-Dashboard", dark=True, reload=False)