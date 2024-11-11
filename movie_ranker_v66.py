import tkinter as tk
from tkinter import ttk, messagebox
import json
import random
import requests
from collections import defaultdict
import math
import textwrap

class MovieRanker:
    def __init__(self):
        # Initialize all instance variables first
        self.consecutive_losses = 0
        self.step = 3
        self.movies = []
        self.preferences = defaultdict(dict)
        self.confidence_scores = {}
        self.current_movie = None
        self.comparison_movie = None
        
        self.TMDB_API_KEY = "1b707e00ba3e60f3b0bbcb81a6ae5f21"
        self.TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
        self.TMDB_DETAILS_URL = "https://api.themoviedb.org/3/movie/{}"
        
        # Create main window
        self.window = tk.Tk()
        self.window.title("🎬 MovieRank")
        
        # Force the window to use black background
        self.window.tk_setPalette(background='#000000',
                                foreground='white',
                                activeBackground='#000000',
                                activeForeground='white')
        self.window.configure(bg='#000000')
        
        # Add these lines to override system theme
        style = ttk.Style(self.window)
        style.theme_use('default')  # or 'clam' depending on your system
        style.configure('.',        # configure all widgets
                       background='#000000',
                       foreground='white')
        style.configure('TFrame',
                       background='#000000')
        
        # Create the title label directly in the window (not in a frame)
        title = ttk.Label(
            self.window,
            text="🎬 MovieRanker",
            font=('Helvetica', 48, 'bold'),
            foreground='white',
            background='#000000'
        )
        title.pack(pady=(40, 40))  # Add padding above and below
        
        # Create top level container frame
        self.top_frame = ttk.Frame(self.window)
        self.top_frame.pack(fill=tk.X)
        
        # Enhanced styling with dark theme
        style = ttk.Style()
        style.configure('Modern.TButton', 
                       font=('Helvetica Neue', 13),
                       padding=12,
                       background='#000000',  # Changed to blue
                       foreground='white')
                       
        style.configure('Title.TLabel',
                       font=('Helvetica Neue', 20, 'bold'),
                       foreground='#ffffff',
                       background='#000000')  # Changed to blue
                       
        style.configure('Question.TLabel',
                       font=('Helvetica Neue', 16),
                       foreground='#ffffff',
                       background='#000000')  # Changed to blue
                       
        style.configure('TFrame', 
                       background='#000000')  # Changed to blue
        
        # Initialize ranking-related constants
        self.DEFAULT_ELO = 1400
        self.PROVISIONAL_K_FACTOR = 64
        self.STANDARD_K_FACTOR = 32
        self.MIN_K_FACTOR = 16
        self.PROVISIONAL_THRESHOLD = 5
        
        # Load saved data
        self.load_movies()
        
        # Create UI elements in new order
        self.create_add_movie_section()
        self.create_comparison_section()
        self.create_movie_list()
        
        # Add this with your other initializations
        self.calculating = False
        self.calculator_frame = None
        
        # Add new animation constants
        self.ANIMATION_DURATION = 300  # milliseconds
        self.FADE_STEPS = 10  # number of steps for fade animations
        
        # Configure additional styles for smooth transitions
        style = ttk.Style()
        style.configure('Smooth.TButton',
                       font=('Helvetica Neue', 13),
                       padding=12)
        style.configure('Smooth.TFrame',
                       background='#000000')
        
        # Add hover effects
        self.window.bind_class('TButton', '<Enter>', self._on_button_enter)
        self.window.bind_class('TButton', '<Leave>', self._on_button_leave)

        # Animation settings for natural feel
        self.FADE_DURATION = 150  # Shorter duration for more responsive feel
        self.TRANSITION_DURATION = 200
        self.EASING = 'ease'  # Natural easing function
        
        # Configure style for modern, subtle interactions
        style = ttk.Style()
        style.configure('Modern.TButton',
                       padding=(20, 10),  # More generous padding
                       font=('Helvetica Neue', 13),
                       background='#000000',
                       foreground='white')
        
        # Add subtle hover state
        style.map('Modern.TButton',
                 background=[('active', '#111111')],  # Very subtle highlight
                 foreground=[('active', '#ffffff')])

    def _on_button_enter(self, event):
        """Smooth hover effect for buttons"""
        button = event.widget
        self._animate_button(button, 0.8, 1.0)

    def _on_button_leave(self, event):
        """Smooth hover effect for buttons"""
        button = event.widget
        self._animate_button(button, 1.0, 0.8)

    def _animate_button(self, button, start_alpha, end_alpha):
        """Smooth alpha animation for buttons"""
        steps = self.FADE_STEPS
        step_size = (end_alpha - start_alpha) / steps
        
        def update_alpha(step):
            if step < steps:
                alpha = start_alpha + (step_size * step)
                button.configure(style=f'Smooth.TButton')
                self.window.after(self.ANIMATION_DURATION // steps, 
                                lambda: update_alpha(step + 1))
        
        update_alpha(0)

    def _smooth_pack(self, widget, **pack_options):
        """Smooth packing animation"""
        widget.pack(**pack_options)
        widget._alpha = 0.0
        
        def fade_in(step):
            if step < self.FADE_STEPS:
                widget._alpha = step / self.FADE_STEPS
                self.window.after(self.ANIMATION_DURATION // self.FADE_STEPS,
                                lambda: fade_in(step + 1))
        
        fade_in(0)

    def _smooth_pack_forget(self, widget):
        """Smooth unpacking animation"""
        def fade_out(step):
            if step > 0:
                widget._alpha = step / self.FADE_STEPS
                self.window.after(self.ANIMATION_DURATION // self.FADE_STEPS,
                                lambda: fade_out(step - 1))
            else:
                widget.pack_forget()
        
        fade_out(self.FADE_STEPS)

    def create_comparison_section(self):
        # Rating section
        self.rating_frame = ttk.Frame(self.top_frame, padding="30")
        self.rating_frame.pack(fill=tk.X)
        self.rating_frame.pack_forget()  # Hide initially
        
        self.rating_label = ttk.Label(
            self.rating_frame,
            text="",
            style='Title.TLabel'
        )
        self.rating_label.pack(pady=20)
        
        rating_buttons = ttk.Frame(self.rating_frame)
        rating_buttons.pack()
        
        rating_options = [
            ("⭐ Good", "good"),
            ("😐 Okay", "okay"),
            ("👎 Bad", "bad")
        ]
        
        for text, value in rating_options:
            btn = ttk.Button(
                rating_buttons,
                text=text,
                style='Modern.TButton',
                command=lambda r=value: self.set_initial_rating(r)
            )
            btn.pack(side=tk.LEFT, padx=15)
        
        # Comparison section
        self.rank_frame = ttk.Frame(self.top_frame, padding="30")
        self.rank_frame.pack(fill=tk.X)
        self.rank_frame.pack_forget()  # Hide initially
        
        self.question_label = ttk.Label(
            self.rank_frame,
            text="Which movie is better?",
            style='Question.TLabel'
        )
        self.question_label.pack(pady=20)
        
        compare_buttons = ttk.Frame(self.rank_frame)
        compare_buttons.pack()
        
        # Create buttons with placeholder text
        self.movie1_button = ttk.Button(
            compare_buttons,
            text="",  # Will be set later
            style='Modern.TButton',
            command=lambda: self.handle_comparison("better")
        )
        self.movie1_button.pack(side=tk.LEFT, padx=15)
        
        self.movie2_button = ttk.Button(
            compare_buttons,
            text="",  # Will be set later
            style='Modern.TButton',
            command=lambda: self.handle_comparison("worse")
        )
        self.movie2_button.pack(side=tk.LEFT, padx=15)
        
    def create_add_movie_section(self):
        self.add_frame = ttk.Frame(self.top_frame, padding="30")
        self.add_frame.pack(fill=tk.X)
        
        add_label = ttk.Label(
            self.add_frame,
            text="Search for a Movie",
            style='Title.TLabel'
        )
        add_label.pack(pady=(0, 10))
        
        # Center the entry and button
        entry_frame = ttk.Frame(self.add_frame)
        entry_frame.pack(fill=tk.X)
        
        # Add a spacer frame on the left
        ttk.Frame(entry_frame).pack(side=tk.LEFT, expand=True)
        
        # Simple Entry widget
        self.title_entry = ttk.Entry(
            entry_frame,
            width=40,
            font=('Helvetica', 14),
            style='Dark.TEntry',
            foreground='black'
        )
        self.title_entry.pack(side=tk.LEFT)
        
        add_button = ttk.Button(
            entry_frame,
            text="➕ Add Movie",
            style='Modern.TButton',
            command=self.start_comparison
        )
        add_button.pack(side=tk.LEFT, padx=5)
        
        # Add a spacer frame on the right
        ttk.Frame(entry_frame).pack(side=tk.LEFT, expand=True)
        
        # Create suggestion listbox with improved styling
        self.suggestion_listbox = tk.Listbox(
            self.window,
            font=('Helvetica', 12),
            height=5,
            bg='#000000',           # Changed to blue
            fg='white',
            selectmode=tk.SINGLE,
            activestyle='none',
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=1,
            highlightcolor='#000088',  # Slightly lighter blue for borders
            highlightbackground='#000088',
            selectbackground='#000099',  # Lighter blue for selection
            selectforeground='#ffffff'
        )
        
        # Bind events for keyboard navigation
        self.title_entry.bind('<KeyRelease>', self.handle_key_release)
        self.title_entry.bind('<Down>', self.handle_down_key)
        self.title_entry.bind('<Return>', lambda e: self.use_suggestion(e))
        self.suggestion_listbox.bind('<Return>', self.use_suggestion)
        self.suggestion_listbox.bind('<Double-Button-1>', self.use_suggestion)
        self.suggestion_listbox.bind('<Up>', self.handle_up_key)
        self.suggestion_listbox.bind('<Down>', self.handle_down_key)
        
    def handle_key_release(self, event):
        # Ignore arrow keys and return in key release handler
        if event.keysym in ('Up', 'Down', 'Return'):
            return 'break'
        
        # Get the current query
        query = self.title_entry.get().strip()
        
        # If query is too short, hide suggestions
        if len(query) < 2:
            self.suggestion_listbox.place_forget()
            return
        
        # Store the current query to check if it changed
        if not hasattr(self, '_last_query'):
            self._last_query = ''
        
        if query != self._last_query:
            self._last_query = query
            # Delay the search to avoid too many API calls
            if hasattr(self, '_after_id'):
                self.window.after_cancel(self._after_id)
            self._after_id = self.window.after(300, self.search_movies)

    def search_movies(self):
        query = self.title_entry.get().strip()
        if len(query) < 2:
            self.suggestion_listbox.place_forget()
            return
        
        try:
            params = {
                'api_key': self.TMDB_API_KEY,
                'query': query,
                'language': 'en-US',
                'page': 1
            }
            
            response = requests.get(self.TMDB_SEARCH_URL, params=params, timeout=5)
            response.raise_for_status()
            results = response.json().get('results', [])[:5]
            
            if results:
                self.suggestion_listbox.delete(0, tk.END)
                for movie in results:
                    year = movie.get('release_date', '')[:4]
                    title = movie.get('title', '')
                    if title:
                        display_text = f"  {title} ({year})" if year else f"  {title}"
                        self.suggestion_listbox.insert(tk.END, display_text)
                
                try:
                    # Position the listbox below the entry
                    entry_x = self.title_entry.winfo_rootx() - self.window.winfo_rootx()
                    entry_y = (self.title_entry.winfo_rooty() - self.window.winfo_rooty() + 
                              self.title_entry.winfo_height())
                    
                    self.suggestion_listbox.place(x=entry_x, y=entry_y, 
                                                width=self.title_entry.winfo_width())
                    self.suggestion_listbox.lift()
                    
                except tk.TclError as e:
                    print(f"Error positioning suggestion listbox: {e}")
                    self.suggestion_listbox.place_forget()
            else:
                self.suggestion_listbox.place_forget()
                
        except requests.RequestException as e:
            print(f"API request failed: {e}")
            self.suggestion_listbox.place_forget()
        except Exception as e:
            print(f"Unexpected error in search_movies: {e}")
            self.suggestion_listbox.place_forget()

    def handle_down_key(self, event):
        # If suggestions aren't visible and we're in the entry widget
        if not self.suggestion_listbox.winfo_viewable() and event.widget == self.title_entry:
            query = self.title_entry.get().strip()
            if len(query) >= 2:  # Only search if we have enough characters
                # Perform immediate search
                self.search_movies()
                # After search completes, try to select first item
                self.window.after(50, self._select_first_suggestion)
            return 'break'
        
        # If suggestions are visible and focus is on entry
        if self.suggestion_listbox.winfo_viewable() and event.widget == self.title_entry:
            if self.suggestion_listbox.size() > 0:
                self.suggestion_listbox.focus_set()
                self.suggestion_listbox.selection_clear(0, tk.END)
                self.suggestion_listbox.selection_set(0)
                self.suggestion_listbox.activate(0)
            return 'break'
        
        # Handle navigation within listbox
        if event.widget == self.suggestion_listbox:
            current = self.suggestion_listbox.curselection()
            if current and current[0] < self.suggestion_listbox.size() - 1:
                next_index = current[0] + 1
                self.suggestion_listbox.selection_clear(0, tk.END)
                self.suggestion_listbox.selection_set(next_index)
                self.suggestion_listbox.activate(next_index)
                self.suggestion_listbox.see(next_index)
        return 'break'

    def _select_first_suggestion(self):
        """Helper method to select first suggestion after search"""
        if self.suggestion_listbox.winfo_viewable() and self.suggestion_listbox.size() > 0:
            self.suggestion_listbox.focus_set()
            self.suggestion_listbox.selection_clear(0, tk.END)
            self.suggestion_listbox.selection_set(0)
            self.suggestion_listbox.activate(0)

    def use_suggestion(self, event):
        selection = self.suggestion_listbox.curselection()
        if selection:
            selected_movie = self.suggestion_listbox.get(selection[0])
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, selected_movie)
            self.suggestion_listbox.place_forget()  # Hide the suggestions
            self.start_comparison()

    def create_movie_list(self):
        # Create main list frame
        list_frame = ttk.Frame(self.window, padding="20")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header frame for title only (removing delete button from here)
        header_frame = ttk.Frame(list_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # List title
        list_title = ttk.Label(
            header_frame,
            text="🎯 Ranked Movies",
            style='Title.TLabel'
        )
        list_title.pack(side=tk.LEFT)
        
        # Container for listbox, scrollbar, and buttons
        self.list_container = ttk.Frame(list_frame)
        self.list_container.pack(fill=tk.BOTH, expand=True)
        
        # Create a frame for the listbox and action buttons
        list_actions_frame = ttk.Frame(self.list_container)
        list_actions_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create listbox with larger font and adjusted height
        self.movie_listbox = tk.Listbox(
            list_actions_frame,
            font=('Helvetica Neue', 24),
            selectmode=tk.SINGLE,
            activestyle='none',
            height=15,  # Increased height to accommodate info
            bg='#000000',
            fg='#ffffff',
            selectbackground='#000099',
            selectforeground='#ffffff',
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=1,
            highlightcolor='#000088',
            highlightbackground='#000088'
        )
        self.movie_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Store the currently expanded info index
        self.expanded_info_index = None
        
        # Create frame for action buttons
        self.action_buttons_frame = ttk.Frame(list_actions_frame)
        self.action_buttons_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Create buttons (initially hidden)
        self.rerank_button = ttk.Button(
            self.action_buttons_frame,
            text="🔄 Re-rank",
            style='Modern.TButton',
            command=self.rerank_movie
        )
        
        self.delete_button = ttk.Button(
            self.action_buttons_frame,
            text="🗑️ Delete",
            style='Modern.TButton',
            command=self.delete_movie
        )
        
        # Add info button
        self.info_button = ttk.Button(
            self.action_buttons_frame,
            text="ℹ️ Info",
            style='Modern.TButton',
            command=self.show_movie_info
        )
        
        # Create scrollbar
        self.scrollbar = ttk.Scrollbar(
            list_actions_frame,
            orient=tk.VERTICAL,
            command=self.movie_listbox.yview
        )
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure listbox to use scrollbar
        self.movie_listbox.config(yscrollcommand=self.scrollbar.set)
        
        # Bind selection event
        self.movie_listbox.bind('<<ListboxSelect>>', self.on_movie_select)
        
        # Create info frame (initially hidden)
        self.info_frame = ttk.Frame(list_frame)
        self.info_label = ttk.Label(
            self.info_frame,
            text="",
            style='Question.TLabel',
            wraplength=600,
            justify=tk.LEFT
        )
        self.info_label.pack(pady=10)
        
        # Add a back button to the info frame
        self.back_button = ttk.Button(
            self.info_frame,
            text="← Back",
            style='Modern.TButton',
            command=self.hide_movie_info
        )
        self.back_button.pack(pady=10)
        
        # Initial update of the list
        self.update_movie_list()
        
        # Bind mousewheel events
        self.movie_listbox.bind('<MouseWheel>', self._on_mousewheel)
        self.movie_listbox.bind('<Button-4>', self._on_mousewheel)
        self.movie_listbox.bind('<Button-5>', self._on_mousewheel)

    def on_movie_select(self, event=None):
        selection = self.movie_listbox.curselection()
        if not selection:
            return
            
        selected_index = selection[0]
        selected_text = self.movie_listbox.get(selected_index)
        
        # Check if clicking the back button
        if "⬅️ Back to List" in selected_text:
            self.hide_movie_info()
            return
            
        # Don't show buttons if clicking on info text
        if self.expanded_info_index is not None:
            if selected_index > self.expanded_info_index:
                self.movie_listbox.selection_clear(0, tk.END)
                return
        
        # Show buttons for movie entries
        self.rerank_button.pack(side=tk.TOP, pady=2)
        self.delete_button.pack(side=tk.TOP, pady=2)
        self.info_button.pack(side=tk.TOP, pady=2)

    def rerank_movie(self):
        selection = self.movie_listbox.curselection()
        if not selection:
            return
        
        # Get the selected movie title
        movie_text = self.movie_listbox.get(selection[0])
        parts = movie_text.split('. ', 1)
        if len(parts) < 2:
            return
        
        text_after_number = parts[1].strip()
        title_part = text_after_number.split(' (')[0]
        movie_title = title_part[2:].strip()
        
        # Remove the movie from all data structures
        self.movies = [m for m in self.movies if m['title'] != movie_title]
        if movie_title in self.confidence_scores:
            del self.confidence_scores[movie_title]
        if movie_title in self.preferences:
            del self.preferences[movie_title]
        for prefs in self.preferences.values():
            if movie_title in prefs:
                del prefs[movie_title]
        
        # Start the ranking process for this movie
        self.current_movie = {"title": movie_title, "rating": None}
        
        # Hide the add movie section and show rating section
        self.add_frame.pack_forget()
        self.rating_label.config(text=f"How would you rate '{movie_title}'?")
        self.rating_frame.pack(fill=tk.X)
        
        # Update the display
        self.save_movies()
        self.update_movie_list()

    def start_comparison(self):
        selected = self.title_entry.get().strip()
        if not selected:
            return
            
        # Extract title from the format "Movie Title (Year)"
        title = selected.split(' (')[0].strip()
        
        # Check if movie already exists
        if any(m['title'] == title for m in self.movies):
            messagebox.showwarning("Warning", "This movie is already in your list!")
            return
        
        self.current_movie = {"title": title, "rating": None}
        self.title_entry.delete(0, tk.END)
        self.suggestion_listbox.place_forget()
        
        # Transition between frames
        self._transition_frames(self.add_frame, self.rating_frame)
        self.rating_label.config(text=f"How would you rate '{title}'?")
        
    def handle_comparison(self, result):
        if not self.current_movie or not self.comparison_movie:
            return
            
        movie_a = self.current_movie['title']
        movie_b = self.comparison_movie['title']
        
        if result == "better":
            self.update_elo(movie_a, movie_b, 1)
        else:
            self.update_elo(movie_a, movie_b, 0)
        
        # Record the comparison
        self.preferences[movie_a][movie_b] = result == "better"
        self.preferences[movie_b][movie_a] = result != "better"
        
        # Hide calculator frame if it exists
        if self.calculator_frame and self.calculator_frame.winfo_ismapped():
            self.calculator_frame.pack_forget()
        
        # Transition between frames
        self._transition_frames(
            self.rank_frame,
            self.calculator_frame if self.comparisons_remaining > 0 else self.add_frame
        )
        
        # Decrement remaining comparisons and continue
        self.comparisons_remaining -= 1
        if self.comparisons_remaining > 0:
            self.start_next_comparison()
        else:
            # No more comparisons needed
            if self.current_movie not in self.movies:
                self.movies.append(self.current_movie)
            self.save_movies()
            self.update_movie_list()
            self.add_frame.pack(fill=tk.X)
            
            # Clear current comparison
            self.current_movie = None
            self.comparison_movie = None
            
            # Ensure calculator frame is hidden
            if self.calculator_frame:
                self.calculator_frame.pack_forget()

    def update_elo(self, movie_a, movie_b, result):
        # Initialize confidence scores if they don't exist
        for movie in [movie_a, movie_b]:
            if movie not in self.confidence_scores:
                self.confidence_scores[movie] = {
                    'elo': self.DEFAULT_ELO,
                    'games_played': 0,
                    'provisional': True,
                    'wins': 0,
                    'losses': 0
                }
        
        # Get current ratings
        rating_a = self.confidence_scores[movie_a]['elo']
        rating_b = self.confidence_scores[movie_b]['elo']
        
        # Calculate expected scores
        expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
        expected_b = 1 - expected_a
        
        # Get K-factors
        ka = self.get_k_factor(movie_a)
        kb = self.get_k_factor(movie_b)
        
        # Update ratings
        self.confidence_scores[movie_a]['elo'] = rating_a + ka * (result - expected_a)
        self.confidence_scores[movie_b]['elo'] = rating_b + kb * ((1 - result) - expected_b)
        
        # Update stats
        self.confidence_scores[movie_a]['games_played'] += 1
        self.confidence_scores[movie_b]['games_played'] += 1
        
        if result == 1:
            self.confidence_scores[movie_a]['wins'] += 1
            self.confidence_scores[movie_b]['losses'] += 1
        else:
            self.confidence_scores[movie_a]['losses'] += 1
            self.confidence_scores[movie_b]['wins'] += 1
        
        # Check if movies should lose provisional status
        for movie in [movie_a, movie_b]:
            if (self.confidence_scores[movie]['games_played'] >= self.PROVISIONAL_THRESHOLD):
                self.confidence_scores[movie]['provisional'] = False

    def get_k_factor(self, movie_title):
        stats = self.confidence_scores.get(movie_title, {
            'elo': self.DEFAULT_ELO,
            'games_played': 0,
            'provisional': True,
            'wins': 0,
            'losses': 0
        })
        
        if stats['provisional']:
            return self.PROVISIONAL_K_FACTOR
        
        # After provisional period, K-factor decreases with more games
        games_played = stats['games_played']
        if games_played < self.PROVISIONAL_THRESHOLD:
            return self.STANDARD_K_FACTOR
        else:
            return self.MIN_K_FACTOR

    def check_and_resolve_conflicts(self, new_movie):
        conflicts = []
        for movie_a, prefs in self.preferences.items():
            for movie_b, result in prefs.items():
                if movie_b in self.preferences and movie_a in self.preferences[movie_b]:
                    if self.preferences[movie_a][movie_b] == self.preferences[movie_b][movie_a]:
                        conflicts.append((movie_a, movie_b))
                        
        # Resolve conflicts using Elo ratings
        for movie_a, movie_b in conflicts:
            if self.confidence_scores[movie_a]['elo'] > self.confidence_scores[movie_b]['elo']:
                self.preferences[movie_a][movie_b] = 1
                self.preferences[movie_b][movie_a] = 0
            else:
                self.preferences[movie_a][movie_b] = 0
                self.preferences[movie_b][movie_a] = 1

    def find_optimal_comparison(self):
        if not self.current_movie:
            return None
            
        current_movie = self.current_movie['title']
        current_rating = self.current_movie['rating']
        
        # Get all movies with the same rating that haven't been compared yet
        candidates = [
            m for m in self.movies 
            if m.get('rating') == current_rating 
            and m['title'] != current_movie
            and m['title'] not in self.preferences.get(current_movie, {})
        ]
        
        if not candidates:
            return None
            
        # Get current Elo rating
        current_elo = self.confidence_scores.get(current_movie, {'elo': self.DEFAULT_ELO})['elo']
        
        # Find the closest rated movie
        best_candidate = min(
            candidates,
            key=lambda m: abs(
                self.confidence_scores.get(m['title'], {'elo': self.DEFAULT_ELO})['elo'] - current_elo
            )
        )
        
        return best_candidate

    def finalize_ranking(self):
        # Group movies by rating category
        rating_groups = {'good': [], 'okay': [], 'bad': []}
        
        # Sort within each rating group
        for movie in self.movies:
            rating_groups[movie['rating']].append(movie)
            
        for rating in rating_groups:
            rated_movies = [(m['title'], self.confidence_scores.get(m['title'], {'elo': self.DEFAULT_ELO})['elo']) 
                          for m in rating_groups[rating]]
            rated_movies.sort(key=lambda x: x[1], reverse=True)
            rating_groups[rating] = [next(m for m in self.movies if m['title'] == title) 
                                   for title, _ in rated_movies]
        
        # Combine groups maintaining rating boundaries
        self.movies = (rating_groups['good'] + 
                      rating_groups['okay'] + 
                      rating_groups['bad'])

    def delete_movie(self):
        selection = self.movie_listbox.curselection()
        if not selection:
            return
        
        # Get the full text from listbox
        movie_text = self.movie_listbox.get(selection[0])
        
        # Extract just the movie title (everything after the rank number and emoji)
        try:
            # Split by dot and space to remove ranking number
            parts = movie_text.split('. ', 1)
            if len(parts) < 2:
                return
            
            # Get the part after the ranking number
            text_after_number = parts[1].strip()
            
            # Find the title between the emoji and the Elo rating
            title_part = text_after_number.split(' (')[0]  # Split before the Elo rating
            # Remove the emoji and any leading/trailing spaces
            movie_title = title_part[2:].strip()  # Skip the emoji and following space
            
            # Remove from movies list
            self.movies = [m for m in self.movies if m['title'] != movie_title]
            
            # Remove from confidence scores
            if movie_title in self.confidence_scores:
                del self.confidence_scores[movie_title]
            
            # Remove from preferences
            if movie_title in self.preferences:
                del self.preferences[movie_title]
            for prefs in self.preferences.values():
                if movie_title in prefs:
                    del prefs[movie_title]
            
            # Save and update display
            self.save_movies()
            self.update_movie_list()
            
        except Exception as e:
            print(f"Error deleting movie: {e}")

    def update_movie_list(self):
        """Update the movie list with smooth animations"""
        # Clear the current list
        self.movie_listbox.delete(0, tk.END)
        
        # If no movies, show a message
        if not self.movies:
            self.movie_listbox.insert(tk.END, "  No movies added yet")
            return
        
        # Group movies by rating
        rating_groups = {
            'good': [],
            'okay': [],
            'bad': []
        }
        
        # Sort movies into rating groups
        for movie in self.movies:
            rating = movie.get('rating')
            if rating in rating_groups:
                rating_groups[rating].append(movie)
        
        # Sort each group by Elo rating
        for rating in rating_groups:
            rating_groups[rating].sort(
                key=lambda x: self.confidence_scores.get(x['title'], {'elo': self.DEFAULT_ELO})['elo'],
                reverse=True
            )
        
        # Add movies to list in order: good -> okay -> bad
        rank = 1
        for rating in ['good', 'okay', 'bad']:
            for movie in rating_groups[rating]:
                rating_symbol = self._get_rating_symbol(movie.get('rating'))
                elo = int(self.confidence_scores.get(movie['title'], {'elo': self.DEFAULT_ELO})['elo'])
                text = f"  {rank:2d}. {rating_symbol} {movie['title']} ({elo})"
                self.movie_listbox.insert(tk.END, text)
                rank += 1

    def _get_rating_symbol(self, rating):
        """Convert rating to appropriate emoji symbol"""
        if rating == 'good':
            return '⭐'
        elif rating == 'okay':
            return '😐'
        elif rating == 'bad':
            return '👎'
        return '❓'  # Default symbol for unknown ratings

    def save_movies(self):
        data = {
            'movies': self.movies,
            'preferences': dict(self.preferences),
            'confidence_scores': self.confidence_scores
        }
        try:
            with open('movies.json', 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving movies: {e}")
            
    def load_movies(self):
        try:
            with open('movies.json', 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Old format - just movies list
                    self.movies = data
                elif isinstance(data, dict):
                    # New format with preferences and confidence scores
                    self.movies = data.get('movies', [])
                    self.preferences = defaultdict(dict, data.get('preferences', {}))
                    self.confidence_scores = data.get('confidence_scores', {})
                else:
                    # Invalid format, use defaults
                    self.movies = []
        except (FileNotFoundError, json.JSONDecodeError):
            # File doesn't exist or is invalid, use defaults
            self.movies = []
            
    def set_initial_rating(self, rating):
        self.current_movie["rating"] = rating
        self.confidence_scores[self.current_movie['title']] = {
            'elo': self.DEFAULT_ELO,
            'games_played': 0,
            'provisional': True,
            'wins': 0,
            'losses': 0
        }
        
        # Hide rating frame and calculator frame if it exists
        self.rating_frame.pack_forget()
        if self.calculator_frame and self.calculator_frame.winfo_ismapped():
            self.calculator_frame.pack_forget()
        
        # Get similar rated movies for comparison
        same_rating_movies = [m for m in self.movies if m.get("rating") == rating]
        
        if not same_rating_movies:
            # If no movies with same rating, just add it
            self.movies.append(self.current_movie)
            self.save_movies()
            self.update_movie_list()
            self.add_frame.pack(fill=tk.X)
            
            # Ensure calculator frame is hidden
            if self.calculator_frame:
                self.calculator_frame.pack_forget()
        else:
            # Set up comparisons
            self.comparisons_remaining = min(len(same_rating_movies), 3)  # Compare with up to 3 movies
            self.start_next_comparison()

    def show_calculator_animation(self):
        if not self.calculator_frame:
            self.calculator_frame = ttk.Frame(self.top_frame, padding="30")
            self.calculator_label = ttk.Label(
                self.calculator_frame,
                text="🧮 Calculating optimal comparison...",
                style='Question.TLabel'  # Using the same style as the question label
            )
            self.calculator_label.pack(pady=20)
        
        self._smooth_pack_forget(self.rank_frame)
        self._smooth_pack(self.calculator_frame, fill=tk.X)

    def hide_calculator_animation(self):
        if self.calculator_frame:
            self._smooth_pack_forget(self.calculator_frame)

    def start_next_comparison(self):
        if not hasattr(self, 'comparisons_remaining'):
            self.comparisons_remaining = 0
        
        # Show calculator animation
        self.show_calculator_animation()
        
        # Use after to create a small delay and show the animation
        self.window.after(500, self._continue_comparison)

    def _continue_comparison(self):
        next_movie = self.find_optimal_comparison()
        
        # Hide calculator animation
        self.hide_calculator_animation()
        
        if next_movie and self.comparisons_remaining > 0:
            self.comparison_movie = next_movie
            # Changed emojis here - using ⬆️ for first movie and ⬇️ for second
            self.movie1_button.config(text=f"⬆️ {self.current_movie['title']}")
            self.movie2_button.config(text=f"⬇️ {self.comparison_movie['title']}")
            self.rank_frame.pack(fill=tk.X)
        else:
            # No more comparisons needed
            if self.current_movie not in self.movies:
                self.movies.append(self.current_movie)
            self.save_movies()
            self.update_movie_list()
            self.add_frame.pack(fill=tk.X)
            
            # Clear current comparison
            self.current_movie = None
            self.comparison_movie = None
            
            # Ensure calculator frame is hidden
            if self.calculator_frame:
                self.calculator_frame.pack_forget()

    def get_insert_index(self, rating):
        if rating == 'good':
            return len([m for m in self.movies if m["rating"] == "good"])
        elif rating == 'okay':
            return len([m for m in self.movies if m["rating"] in ["good", "okay"]])
        else:
            return len(self.movies)
            
    def run(self):
        self.window.mainloop()

    def show_movie_info(self):
        try:
            selection = self.movie_listbox.curselection()
            if not selection:
                return
                
            selected_index = selection[0]
            
            # If there's already expanded info, remove it first
            if self.expanded_info_index is not None:
                self.hide_movie_info()
                if self.expanded_info_index == selected_index:
                    return
            
            # Extract movie title
            movie_text = self.movie_listbox.get(selected_index)
            parts = movie_text.split('. ', 1)
            if len(parts) < 2:
                return
            
            text_after_number = parts[1].strip()
            title_part = text_after_number.split(' (')[0]
            movie_title = title_part[2:].strip()
            
            if not movie_title:
                messagebox.showwarning("Warning", "Could not extract movie title")
                return
                
            # Search for movie ID
            params = {
                'api_key': self.TMDB_API_KEY,
                'query': movie_title,
                'language': 'en-US',
            }
            
            response = requests.get(self.TMDB_SEARCH_URL, params=params, timeout=5)
            response.raise_for_status()
            results = response.json().get('results', [])
            
            if not results:
                messagebox.showinfo("Info", "No movie information found.")
                return
                
            movie_id = results[0]['id']
            
            details_url = self.TMDB_DETAILS_URL.format(movie_id)
            details_response = requests.get(details_url, 
                                         params={'api_key': self.TMDB_API_KEY},
                                         timeout=5)
            details_response.raise_for_status()
            movie_details = details_response.json()
            
            # Get movie details
            title = movie_details.get('title', 'N/A')
            release_date = movie_details.get('release_date', 'N/A')
            rating = movie_details.get('vote_average', 'N/A')
            runtime = movie_details.get('runtime', 'N/A')
            overview = movie_details.get('overview', 'N/A')
            genres = ', '.join(g.get('name', '') for g in movie_details.get('genres', []))
            
            try:
                current_index = selected_index + 1
                
                # Add spacing and divider
                self.movie_listbox.insert(current_index, "")
                current_index += 1
                self.movie_listbox.insert(current_index, "   ━━━━━━━━━━━━━━━━━━━━━━")
                self.movie_listbox.itemconfig(current_index, fg='#E0E0E0')
                current_index += 1
                
                # Format info items with shorter labels and better wrapping
                info_items = [
                    f"  🎬 {title}",
                    f"  📅 {release_date}",
                    f"  ⭐ {rating}/10",
                    f"  ⏱️ {runtime} min",
                    f"  🎭 {genres}"
                ]
                
                # Insert info items
                for item in info_items:
                    self.movie_listbox.insert(current_index, item)
                    self.movie_listbox.itemconfig(current_index, fg='#E0E0E0')
                    current_index += 1
                
                # Add overview header
                self.movie_listbox.insert(current_index, "")
                current_index += 1
                self.movie_listbox.insert(current_index, "  📝 Overview:")
                self.movie_listbox.itemconfig(current_index, fg='#E0E0E0')
                current_index += 1
                
                # Add overview text with better wrapping
                wrapped_lines = textwrap.wrap(overview, width=80)  # Increased width from 40 to 80
                for line in wrapped_lines:
                    self.movie_listbox.insert(current_index, f"     {line}")
                    self.movie_listbox.itemconfig(current_index, fg='#E0E0E0')
                    current_index += 1
                
                # Add closing elements
                self.movie_listbox.insert(current_index, "")
                current_index += 1
                self.movie_listbox.insert(current_index, "   ━━━━━━━━━━━━━━━━━━━━━━")
                self.movie_listbox.itemconfig(current_index, fg='#E0E0E0')
                current_index += 1
                
                # Add back button with clear visual distinction
                self.movie_listbox.insert(current_index, "")
                current_index += 1
                self.movie_listbox.insert(current_index, "  ⬅️ Back to List")
                self.movie_listbox.itemconfig(current_index, fg='#00BFFF')  # Bright blue for visibility
                current_index += 1
                self.movie_listbox.insert(current_index, "")
                
                # Store the expanded index and back button index
                self.expanded_info_index = selected_index
                self.back_button_index = current_index - 2  # Store the back button index
                
                # Ensure visibility
                self.movie_listbox.see(selected_index)
                self.movie_listbox.see(current_index)
                
            except tk.TclError as e:
                print(f"Error updating listbox: {e}")
                self.hide_movie_info()
                
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to fetch movie information: {str(e)}")
        except Exception as e:
            print(f"Unexpected error in show_movie_info: {e}")
            messagebox.showerror("Error", "An unexpected error occurred")
            self.hide_movie_info()

    def hide_movie_info(self):
        """Remove expanded movie information"""
        if hasattr(self, 'expanded_info_index') and self.expanded_info_index is not None:
            try:
                # Get the original movie entry
                original_movie = self.movie_listbox.get(self.expanded_info_index)
                
                # Delete all expanded info
                start_index = self.expanded_info_index + 1
                end_index = self.back_button_index + 2 if hasattr(self, 'back_button_index') else tk.END
                self.movie_listbox.delete(start_index, end_index)
                
                # Restore selection to original movie
                self.movie_listbox.selection_clear(0, tk.END)
                self.movie_listbox.selection_set(self.expanded_info_index)
                self.movie_listbox.see(self.expanded_info_index)
                
                # Clear the tracking variables
                self.expanded_info_index = None
                if hasattr(self, 'back_button_index'):
                    delattr(self, 'back_button_index')
                
            except Exception as e:
                print(f"Error hiding movie info: {e}")
                # Fallback: refresh the entire list
                self.update_movie_list()

    def _on_mousewheel(self, event):
        # Handle mousewheel scrolling
        if event.num == 4:
            self.movie_listbox.yview_scroll(-1, "units")
        elif event.num == 5:
            self.movie_listbox.yview_scroll(1, "units")
        else:
            self.movie_listbox.yview_scroll(int(-1*(event.delta/120)), "units")

    def handle_up_key(self, event):
        # If suggestions aren't visible, do nothing
        if not self.suggestion_listbox.winfo_viewable():
            return 'break'
        
        # If focus is in listbox
        if event.widget == self.suggestion_listbox:
            current = self.suggestion_listbox.curselection()
            if current:
                if current[0] == 0:  # If at first item
                    # Move focus back to entry
                    self.title_entry.focus_set()
                    self.suggestion_listbox.selection_clear(0, tk.END)
                else:
                    # Move up in list
                    prev_index = current[0] - 1
                    self.suggestion_listbox.selection_clear(0, tk.END)
                    self.suggestion_listbox.selection_set(prev_index)
                    self.suggestion_listbox.activate(prev_index)
                    self.suggestion_listbox.see(prev_index)
        
        return 'break'

    def _transition_frames(self, old_frame, new_frame):
        """Smoothly transition between frames"""
        if old_frame:
            old_frame.pack_forget()
        
        if new_frame:
            new_frame.pack(fill=tk.X, pady=10)

if __name__ == "__main__":
    app = MovieRanker()
    app.run()

