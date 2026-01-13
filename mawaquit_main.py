#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mawaquit - Application de calcul des heures de prière avec visualisation cartographique

Version modulaire avec :
- Niveau administratif 3 optionnel
- Affichage des villes depuis fichier local
- Sélection de date personnalisée
- Limitation du zoom maximum
"""

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from tkinter import ttk, messagebox
import os
import tempfile
from datetime import date, timedelta
import warnings

# Import des modules personnalisés
from praytimes import PrayTimes
from isochrones import IsochroneGenerator

warnings.filterwarnings('ignore')


class MawaquitApp:
    """Application principale Mawaquit"""

    def __init__(self, root):
        self.root = root
        self.root.title("Mawaquit - Heures de Prière et Courbes Isochrones")
        self.root.geometry("1500x900")

        # Dictionnaire des codes pays (ISO Alpha-3)
        self.pays_codes = {
            "France": "FRA", "Germany": "DEU", "Italy": "ITA", "Spain": "ESP",
            "United Kingdom": "GBR", "Belgium": "BEL", "Netherlands": "NLD",
            "Switzerland": "CHE", "Portugal": "PRT", "Poland": "POL",
            "Greece": "GRC", "Austria": "AUT", "Sweden": "SWE", "Norway": "NOR",
            "Denmark": "DNK", "Morocco": "MAR", "Tunisia": "TUN", "Algeria": "DZA",
            "Egypt": "EGY", "South Africa": "ZAF", "United States": "USA",
            "Canada": "CAN", "Mexico": "MEX", "Brazil": "BRA", "Argentina": "ARG",
            "Saudi Arabia": "SAU", "UAE": "ARE", "Qatar": "QAT", "Kuwait": "KWT",
            "Turkey": "TUR", "Indonesia": "IDN", "Pakistan": "PAK", "India": "IND"
        }

        # Calculateur de prières
        self.pray_calc = PrayTimes('MWL')

        # Variables d'état
        self.marker_pos = None
        self.marker_artist = None
        self.current_gdf = None
        self.current_gdf_level2 = None
        self.cities_gdf = None
        self.cities_artists = []
        self.selected_date = date.today()
        self.initial_bounds = None
        self.max_zoom_factor = 20

        # Cache GADM
        self.cache_dir = os.path.join(tempfile.gettempdir(), "gadm_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

        # Créer l'interface
        self.setup_ui()

        # Générateur d'isochrones (initialisé après l'UI)
        self.isochrone_gen = IsochroneGenerator(self.pray_calc, self.ax)

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Frame gauche (carte)
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # === Contrôles ligne 1 ===
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        ttk.Label(control_frame, text="Pays:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

        self.pays_var = tk.StringVar()
        self.combo = ttk.Combobox(
            control_frame, textvariable=self.pays_var,
            values=sorted(list(self.pays_codes.keys())),
            state="readonly", width=20, font=("Arial", 10)
        )
        self.combo.pack(side=tk.LEFT, padx=5)
        self.combo.bind("<<ComboboxSelected>>", self.afficher_carte)

        ttk.Button(control_frame, text="Afficher Carte",
                   command=self.afficher_carte).pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="Méthode:",
                  font=("Arial", 10)).pack(side=tk.LEFT, padx=10)

        self.method_var = tk.StringVar(value='MWL')
        method_combo = ttk.Combobox(
            control_frame, textvariable=self.method_var,
            values=list(PrayTimes.methods.keys()),
            state="readonly", width=15
        )
        method_combo.pack(side=tk.LEFT, padx=5)
        method_combo.bind("<<ComboboxSelected>>", self.update_prayer_times)

        self.status_label = ttk.Label(control_frame, text="", foreground="blue")
        self.status_label.pack(side=tk.LEFT, padx=10)

        # === Contrôles ligne 2 ===
        control_frame2 = ttk.Frame(left_frame)
        control_frame2.pack(side=tk.TOP, fill=tk.X, pady=5)

        ttk.Label(control_frame2, text="Date:",
                  font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

        date_frame = ttk.Frame(control_frame2)
        date_frame.pack(side=tk.LEFT, padx=5)

        self.date_var = tk.StringVar(value=self.selected_date.strftime('%d/%m/%Y'))
        self.date_entry = ttk.Entry(date_frame, textvariable=self.date_var, width=12)
        self.date_entry.pack(side=tk.LEFT, padx=2)

        ttk.Button(date_frame, text="📅", width=3,
                   command=self.show_date_picker).pack(side=tk.LEFT)
        ttk.Button(date_frame, text="Aujourd'hui",
                   command=self.reset_to_today).pack(side=tk.LEFT, padx=2)

        self.show_level3_var = tk.BooleanVar(value=False)
        self.level3_check = ttk.Checkbutton(
            control_frame2, text="Afficher niveau 3",
            variable=self.show_level3_var, command=self.toggle_level3
        )
        self.level3_check.pack(side=tk.LEFT, padx=15)

        self.show_cities_var = tk.BooleanVar(value=False)
        self.cities_check = ttk.Checkbutton(
            control_frame2, text="Afficher villes",
            variable=self.show_cities_var, command=self.toggle_cities
        )
        self.cities_check.pack(side=tk.LEFT, padx=5)

        # === Frame carte ===
        map_frame = ttk.Frame(left_frame)
        map_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        toolbar_frame = ttk.Frame(map_frame)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)

        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=map_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        self.canvas.mpl_connect('button_press_event', self.on_map_click)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

        # === Frame droit ===
        right_frame = ttk.Frame(main_frame, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5)
        right_frame.pack_propagate(False)

        # Panel heures de prière
        prayer_frame = ttk.LabelFrame(right_frame, text="Heures de Prière", padding=10)
        prayer_frame.pack(fill=tk.BOTH, pady=5)

        self.coord_label = ttk.Label(prayer_frame, text="Position: --", font=("Arial", 9))
        self.coord_label.pack(anchor=tk.W, pady=2)

        self.date_label = ttk.Label(
            prayer_frame,
            text=f"Date: {self.selected_date.strftime('%d/%m/%Y')}",
            font=("Arial", 9)
        )
        self.date_label.pack(anchor=tk.W, pady=2)

        ttk.Separator(prayer_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        self.prayer_labels = {}
        for prayer in ['fajr', 'sunrise', 'dhuhr', 'asr', 'maghrib', 'isha']:
            frame = ttk.Frame(prayer_frame)
            frame.pack(fill=tk.X, pady=3)

            ttk.Label(frame, text=f"{prayer.capitalize()}:",
                      font=("Arial", 10, "bold"), width=10).pack(side=tk.LEFT)

            label = ttk.Label(frame, text="--:--",
                              font=("Arial", 11), foreground="darkblue")
            label.pack(side=tk.LEFT)
            self.prayer_labels[prayer] = label

        # Panel isochrones
        iso_frame = ttk.LabelFrame(right_frame, text="Courbes Isochrones", padding=10)
        iso_frame.pack(fill=tk.BOTH, pady=5)

        ttk.Label(iso_frame, text="Tracer les courbes pour:",
                  font=("Arial", 9)).pack(anchor=tk.W, pady=5)

        self.iso_buttons = {}
        for prayer in ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']:
            btn = ttk.Button(
                iso_frame, text=prayer.capitalize(),
                command=lambda p=prayer: self.tracer_isochrones(p)
            )
            btn.pack(fill=tk.X, pady=2)
            self.iso_buttons[prayer] = btn

        ttk.Separator(iso_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        ttk.Button(iso_frame, text="Effacer Courbes",
                   command=self.clear_isochrones).pack(fill=tk.X, pady=2)

        # Panel instructions
        info_frame = ttk.LabelFrame(right_frame, text="Instructions", padding=10)
        info_frame.pack(fill=tk.BOTH, pady=5)

        instructions = (
            "1. Sélectionnez un pays\n"
            "2. Modifiez la date si nécessaire\n"
            "3. Cliquez sur la carte pour placer le marqueur\n"
            "4. Les heures de prière s'affichent automatiquement\n"
            "5. Activez niveau 3 et villes pour plus de détails\n"
            "6. Cliquez sur un bouton pour tracer les isochrones"
        )
        ttk.Label(info_frame, text=instructions, font=("Arial", 8),
                  justify=tk.LEFT, wraplength=250).pack()

    def show_date_picker(self):
        """Affiche une fenêtre de sélection de date"""
        picker_window = tk.Toplevel(self.root)
        picker_window.title("Sélectionner une date")
        picker_window.geometry("300x250")
        picker_window.transient(self.root)
        picker_window.grab_set()

        current = self.selected_date
        year_var = tk.IntVar(value=current.year)
        month_var = tk.IntVar(value=current.month)
        day_var = tk.IntVar(value=current.day)

        spin_frame = ttk.Frame(picker_window)
        spin_frame.pack(pady=20)

        ttk.Label(spin_frame, text="Jour:").grid(row=0, column=0, padx=5)
        day_spin = ttk.Spinbox(spin_frame, from_=1, to=31, textvariable=day_var, width=5)
        day_spin.grid(row=1, column=0, padx=5)

        ttk.Label(spin_frame, text="Mois:").grid(row=0, column=1, padx=5)
        month_spin = ttk.Spinbox(spin_frame, from_=1, to=12, textvariable=month_var, width=5)
        month_spin.grid(row=1, column=1, padx=5)

        ttk.Label(spin_frame, text="Année:").grid(row=0, column=2, padx=5)
        year_spin = ttk.Spinbox(spin_frame, from_=2020, to=2050, textvariable=year_var, width=8)
        year_spin.grid(row=1, column=2, padx=5)

        quick_frame = ttk.LabelFrame(picker_window, text="Accès rapide", padding=10)
        quick_frame.pack(pady=10, padx=20, fill=tk.X)

        def set_today():
            today = date.today()
            day_var.set(today.day)
            month_var.set(today.month)
            year_var.set(today.year)

        def add_days(days):
            try:
                new_date = date(year_var.get(), month_var.get(), day_var.get()) + timedelta(days=days)
                day_var.set(new_date.day)
                month_var.set(new_date.month)
                year_var.set(new_date.year)
            except:
                pass

        btn_frame = ttk.Frame(quick_frame)
        btn_frame.pack()

        ttk.Button(btn_frame, text="Aujourd'hui", command=set_today).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="-7j", width=5, command=lambda: add_days(-7)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="+7j", width=5, command=lambda: add_days(7)).pack(side=tk.LEFT, padx=2)

        def validate_and_close():
            try:
                new_date = date(year_var.get(), month_var.get(), day_var.get())
                self.selected_date = new_date
                self.date_var.set(new_date.strftime('%d/%m/%Y'))
                self.date_label.config(text=f"Date: {new_date.strftime('%d/%m/%Y')}")
                self.update_prayer_times()
                picker_window.destroy()
            except ValueError:
                messagebox.showerror("Erreur", "Date invalide", parent=picker_window)

        button_frame = ttk.Frame(picker_window)
        button_frame.pack(pady=15)

        ttk.Button(button_frame, text="OK", command=validate_and_close).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annuler", command=picker_window.destroy).pack(side=tk.LEFT, padx=5)

    def reset_to_today(self):
        """Réinitialise la date à aujourd'hui"""
        self.selected_date = date.today()
        self.date_var.set(self.selected_date.strftime('%d/%m/%Y'))
        self.date_label.config(text=f"Date: {self.selected_date.strftime('%d/%m/%Y')}")
        self.update_prayer_times()

    def telecharger_gadm(self, code_pays, niveau):
        """Télécharge ou charge depuis le cache les données GADM"""
        cache_file = os.path.join(self.cache_dir, f"gadm41_{code_pays}_{niveau}.json")

        if os.path.exists(cache_file):
            try:
                return gpd.read_file(cache_file)
            except:
                os.remove(cache_file)

        url = f"https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_{code_pays}_{niveau}.json"

        try:
            self.status_label.config(text=f"Téléchargement niveau {niveau}...", foreground="orange")
            self.root.update()
            gdf = gpd.read_file(url)
            gdf.to_file(cache_file, driver='GeoJSON')
            return gdf
        except Exception as e:
            print(f"Erreur téléchargement niveau {niveau}: {e}")
            return None

    def charger_villes(self, code_pays):
        """Charge les villes depuis le fichier local populated_places.geojson"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cities_file = os.path.join(script_dir, "populated_places.geojson")

        if not os.path.exists(cities_file):
            print(f"Fichier {cities_file} non trouvé")
            return None

        try:
            cities_all = gpd.read_file(cities_file)

            # Filtrer par code pays (priorité à adm0_a3)
            if 'adm0_a3' in cities_all.columns:
                cities_country = cities_all[cities_all['adm0_a3'] == code_pays].copy()
            else:
                print("Colonne 'adm0_a3' non trouvée")
                return None

            if len(cities_country) == 0:
                print(f"Aucune ville trouvée pour {code_pays}")
                return None

            # Trier par population si disponible
            if 'pop_max' in cities_country.columns:
                cities_country = cities_country.sort_values('pop_max', ascending=False)

            return cities_country

        except Exception as e:
            print(f"Erreur lecture villes: {e}")
            return None

    def afficher_carte(self, event=None):
        """Affiche la carte du pays sélectionné"""
        pays = self.pays_var.get()
        if not pays:
            self.status_label.config(text="Sélectionnez un pays", foreground="red")
            return

        code_pays = self.pays_codes.get(pays)

        self.ax.clear()
        self.marker_pos = None
        self.marker_artist = None
        self.clear_isochrones()
        self.clear_cities()

        niveau0 = self.telecharger_gadm(code_pays, 0)
        niveau1 = self.telecharger_gadm(code_pays, 1)

        if niveau0 is None:
            self.status_label.config(text="Erreur chargement", foreground="red")
            return

        self.current_gdf = niveau0
        self.initial_bounds = niveau0.total_bounds

        niveau0.plot(ax=self.ax, color='lightblue', alpha=0.3,
                     edgecolor='navy', linewidth=2)

        if niveau1 is not None:
            niveau1.boundary.plot(ax=self.ax, edgecolor='darkred',
                                  linewidth=0.8, alpha=0.6)

        self.current_gdf_level2 = self.telecharger_gadm(code_pays, 2)
        self.cities_gdf = self.charger_villes(code_pays)

        if self.show_level3_var.get() and self.current_gdf_level2 is not None:
            self.current_gdf_level2.boundary.plot(
                ax=self.ax, edgecolor='green',
                linewidth=0.4, alpha=0.4, linestyle='--'
            )

        if self.show_cities_var.get() and self.cities_gdf is not None:
            self.draw_cities()

        self.ax.set_title(
            f"Carte de {pays} - Cliquez pour placer le marqueur",
            fontsize=12, fontweight='bold'
        )
        self.ax.set_xlabel("Longitude")
        self.ax.set_ylabel("Latitude")
        self.ax.grid(True, alpha=0.2)

        self.canvas.draw()
        self.status_label.config(
            text=f"Carte chargée. Cliquez pour calculer les heures de prière",
            foreground="green"
        )

    def toggle_level3(self):
        """Active/désactive l'affichage du niveau 3"""
        if self.current_gdf_level2 is None:
            self.show_level3_var.set(False)
            self.status_label.config(
                text="Niveau 3 non disponible pour ce pays",
                foreground="orange"
            )
            return

        self.afficher_carte()

    def toggle_cities(self):
        """Active/désactive l'affichage des villes"""
        if self.cities_gdf is None:
            self.show_cities_var.set(False)
            self.status_label.config(
                text="Données de villes non disponibles",
                foreground="orange"
            )
            return

        if self.show_cities_var.get():
            self.draw_cities()
            self.status_label.config(text="Villes affichées", foreground="green")
        else:
            self.clear_cities()
            self.status_label.config(text="Villes masquées", foreground="blue")

        self.canvas.draw()

    def draw_cities(self):
        """Dessine les villes sur la carte"""
        if self.cities_gdf is None:
            return

        self.clear_cities()

        x = self.cities_gdf.geometry.x
        y = self.cities_gdf.geometry.y

        # Dessiner les points pour toutes les villes
        scatter = self.ax.scatter(
            x, y, c='red', s=30, alpha=0.7,
            marker='o', edgecolors='darkred',
            linewidth=0.5, zorder=5
        )
        self.cities_artists.append(scatter)

        # Afficher les noms de TOUTES les villes
        if 'name' in self.cities_gdf.columns:
            for idx, row in self.cities_gdf.iterrows():
                text = self.ax.text(
                    row.geometry.x, row.geometry.y,
                    row['name'], fontsize=7,
                    ha='left', va='bottom', zorder=6,
                    bbox=dict(boxstyle='round,pad=0.3',
                              facecolor='white', alpha=0.7,
                              edgecolor='none')
                )
                self.cities_artists.append(text)

    def clear_cities(self):
        """Efface les villes de la carte"""
        for artist in self.cities_artists:
            try:
                artist.remove()
            except:
                pass
        self.cities_artists = []

    def limit_zoom(self):
        """Limite le niveau de zoom"""
        if self.initial_bounds is None:
            return

        min_lon, min_lat, max_lon, max_lat = self.initial_bounds

        initial_width = max_lon - min_lon
        initial_height = max_lat - min_lat

        min_width = initial_width / self.max_zoom_factor
        min_height = initial_height / self.max_zoom_factor

        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        current_width = cur_xlim[1] - cur_xlim[0]
        current_height = cur_ylim[1] - cur_ylim[0]

        if current_width < min_width or current_height < min_height:
            center_x = (cur_xlim[0] + cur_xlim[1]) / 2
            center_y = (cur_ylim[0] + cur_ylim[1]) / 2

            new_width = max(current_width, min_width)
            new_height = max(current_height, min_height)

            self.ax.set_xlim(center_x - new_width / 2, center_x + new_width / 2)
            self.ax.set_ylim(center_y - new_height / 2, center_y + new_height / 2)

    def on_map_click(self, event):
        """Gère le clic sur la carte"""
        if event.inaxes != self.ax or self.current_gdf is None:
            return

        if self.toolbar.mode != '':
            return

        lon, lat = event.xdata, event.ydata

        if self.marker_artist:
            self.marker_artist.remove()

        self.marker_artist = self.ax.plot(
            lon, lat, marker='+', color='red',
            markersize=15, markeredgewidth=2.5, zorder=10
        )[0]

        self.canvas.draw()

        self.marker_pos = (lat, lon)
        self.update_prayer_times()

    def on_scroll(self, event):
        """Gère le zoom avec la molette"""
        if event.inaxes != self.ax:
            return

        zoom_factor = 1.2 if event.button == 'up' else 0.8

        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        xdata = event.xdata
        ydata = event.ydata

        new_width = (cur_xlim[1] - cur_xlim[0]) * zoom_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * zoom_factor

        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

        self.ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])
        self.ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])

        # Appliquer la limitation du zoom
        self.limit_zoom()

        self.canvas.draw_idle()

    def update_prayer_times(self, event=None):
        """Met à jour l'affichage des heures de prière"""
        if not self.marker_pos:
            return

        lat, lon = self.marker_pos
        self.coord_label.config(text=f"Position: {lat:.4f}°N, {lon:.4f}°E")

        tz = round(lon / 15)

        method = self.method_var.get()
        if self.pray_calc.calcMethod != method:
            self.pray_calc = PrayTimes(method)

        times = self.pray_calc.getTimes(
            self.selected_date,
            (lat, lon, 0),
            tz,
            format='24h'
        )

        for prayer in self.prayer_labels:
            if prayer in times:
                self.prayer_labels[prayer].config(text=times[prayer])

    def tracer_isochrones(self, prayer_name):
        """Trace les courbes isochrones pour une prière"""
        if self.current_gdf is None:
            self.status_label.config(
                text="Chargez d'abord une carte",
                foreground="red"
            )
            return

        self.status_label.config(
            text=f"Calcul des isochrones pour {prayer_name}...",
            foreground="orange"
        )
        self.root.update()

        success = self.isochrone_gen.tracer_isochrones(
            prayer_name,
            self.current_gdf,
            self.selected_date
        )

        if success:
            self.canvas.draw()
            self.status_label.config(
                text=f"Isochrones tracées pour {prayer_name}",
                foreground="green"
            )
        else:
            self.status_label.config(
                text="Erreur lors du traçage",
                foreground="red"
            )

    def clear_isochrones(self):
        """Efface toutes les courbes isochrones"""
        self.isochrone_gen.clear_isochrones()
        if self.current_gdf is not None:
            self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = MawaquitApp(root)
    root.mainloop()