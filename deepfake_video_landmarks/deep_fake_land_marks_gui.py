import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
import os
import dlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import time
from collections import deque
from PIL import Image, ImageTk
import seaborn as sns
from queue import Queue
import gc
import sys

# Force CPU usage only - import TensorFlow after setting environment variables
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU usage
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce TensorFlow logging noise

# Now import TensorFlow after setting environment variables
import tensorflow as tf
from tensorflow.keras.models import load_model


class DeepfakeDetectionGUI:
    """
    Enhanced Professional GUI for deepfake detection analysis with dual video display
    Compatible with Multi-Head LSTM Model
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Head Deepfake Analyzer v3.0")
        self.root.geometry("1800x1100")
        self.root.configure(bg='#1a1a1a')

        # Set window icon and make it resizable
        self.root.minsize(1400, 900)

        # Initialize variables
        self.model = None
        self.face_detector = None
        self.landmark_predictor = None
        self.current_video = None
        self.is_analyzing = False
        self.is_loading_video = False
        self.video_loaded_successfully = False
        self.analysis_thread = None
        self.display_thread = None
        self.video_loading_thread = None
        self.model_path = "multi_head_lstm.h5"

        # Analysis parameters (updated for multi-head model)
        self.chunk_size = 64
        self.num_landmarks = 68
        self.features_per_landmark = 5
        self.feature_dim = self.num_landmarks * self.features_per_landmark

        # Data storage - REMOVED maxlen to store ALL predictions, not just last 200!
        self.prediction_history = deque()  # No maxlen = stores ALL predictions
        self.confidence_history = deque()  # No maxlen = stores ALL confidences
        self.frame_timestamps = deque()  # Store timestamps for each prediction
        self.frame_features = []
        self.current_frame = None
        self.current_frame_processed = None
        self.frame_index = 0
        self.total_video_frames = 0
        self.video_fps = 30

        # Threading for smooth display
        self.frame_queue = Queue(maxsize=10)
        self.display_queue = Queue(maxsize=10)
        self.analysis_queue = Queue(maxsize=15)

        # Enhanced colors with gradients
        self.colors = {
            'real': '#00ff88',
            'fake': '#ff4757',
            'uncertain': '#ffa502',
            'bg': '#1a1a1a',
            'card': '#2f3542',
            'card_light': '#3d4454',
            'text': '#f1f2f6',
            'text_dim': '#a4b0be',
            'accent': '#3742fa',
            'accent_light': '#5352ed',
            'success': '#2ed573',
            'warning': '#ff6348',
            'border': '#57606f'
        }

        # IMPORTANT: Setup styles FIRST before creating GUI components
        self.setup_styles()
        self.setup_gui()
        self.auto_load_model()

    def setup_styles(self):
        """Setup modern styling - MUST be called before creating any styled widgets"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Configure the custom progress bar style
        self.style.configure('Modern.TProgressbar',
                             background=self.colors['accent'],
                             troughcolor=self.colors['card'],
                             borderwidth=0,
                             lightcolor=self.colors['accent'],
                             darkcolor=self.colors['accent'])

        # Configure loading progress bar style
        self.style.configure('Loading.TProgressbar',
                             background=self.colors['success'],
                             troughcolor=self.colors['card'],
                             borderwidth=0,
                             lightcolor=self.colors['success'],
                             darkcolor=self.colors['success'])

        # Create the layout for the progress bar to avoid the layout error
        self.style.layout('Modern.TProgressbar',
                          [('Horizontal.Progressbar.trough',
                            {'children': [('Horizontal.Progressbar.pbar',
                                           {'side': 'left', 'sticky': 'ns'})],
                             'sticky': 'nswe'})])

        self.style.layout('Loading.TProgressbar',
                          [('Horizontal.Progressbar.trough',
                            {'children': [('Horizontal.Progressbar.pbar',
                                           {'side': 'left', 'sticky': 'ns'})],
                             'sticky': 'nswe'})])

    def setup_gui(self):
        """Setup the enhanced GUI layout with modern styling"""
        # Main container with padding
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Enhanced title with gradient effect
        title_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        title_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = tk.Label(
            title_frame,
            text="🎯 MULTI-STREAM DEEPFAKE ANALYZER",
            font=('Segoe UI', 26, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['bg']
        )
        title_label.pack()

        subtitle_label = tk.Label(
            title_frame,
            text="v3.0 • Multi-Head Architecture • Real-time Analysis • Enhanced LSTM Model",
            font=('Segoe UI', 11),
            fg=self.colors['text_dim'],
            bg=self.colors['bg']
        )
        subtitle_label.pack(pady=(5, 0))

        # Top control panel with modern cards
        self.setup_control_panel(main_frame)

        # Main content area with improved layout
        content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

        # Left panel - Dual video display
        left_panel = self.create_card_frame(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Right panel - Analysis and charts
        right_panel = self.create_card_frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        self.setup_dual_video_panel(left_panel)
        self.setup_analysis_panel(right_panel)

        # Enhanced status bar
        self.setup_status_bar(main_frame)

    def create_card_frame(self, parent):
        """Create a modern card-style frame"""
        card = tk.Frame(parent, bg=self.colors['card'], relief=tk.FLAT, bd=0)

        # Add subtle border
        border_frame = tk.Frame(card, bg=self.colors['border'], height=1)
        border_frame.pack(fill=tk.X, side=tk.TOP)

        return card

    def create_modern_button(self, parent, text, command, bg_color, size='normal'):
        """Create modern styled buttons"""
        font_size = 12 if size == 'large' else 10
        pad_x = 25 if size == 'large' else 15
        pad_y = 8 if size == 'large' else 6

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg='white',
            font=('Segoe UI', font_size, 'bold'),
            relief=tk.FLAT,
            padx=pad_x,
            pady=pad_y,
            cursor='hand2',
            activebackground=self.lighten_color(bg_color),
            activeforeground='white',
            bd=0
        )

        # Add hover effects
        btn.bind("<Enter>", lambda e: btn.config(bg=self.lighten_color(bg_color)))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg_color))

        return btn

    def lighten_color(self, color):
        """Lighten a hex color"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
        rgb = tuple(min(255, int(c * 1.2)) for c in rgb)
        return '#%02x%02x%02x' % rgb

    def setup_control_panel(self, parent):
        """Setup the enhanced control panel"""
        control_frame = self.create_card_frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 15))

        # Inner padding
        inner_frame = tk.Frame(control_frame, bg=self.colors['card'])
        inner_frame.pack(fill=tk.X, padx=20, pady=15)

        # Model section
        model_section = tk.Frame(inner_frame, bg=self.colors['card'])
        model_section.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(
            model_section,
            text="🧠 AI MODEL",
            font=('Segoe UI', 11, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['card']
        ).pack(anchor=tk.W)

        model_controls = tk.Frame(model_section, bg=self.colors['card'])
        model_controls.pack(fill=tk.X, pady=(8, 0))

        self.load_model_btn = self.create_modern_button(
            model_controls, "Load Different Model", self.load_model, self.colors['accent']
        )
        self.load_model_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.model_status = tk.Label(
            model_controls,
            text="🔄 Loading Multi-Head Model...",
            fg=self.colors['uncertain'],
            bg=self.colors['card'],
            font=('Segoe UI', 10)
        )
        self.model_status.pack(side=tk.LEFT)

        # Separator
        separator = tk.Frame(inner_frame, bg=self.colors['border'], width=2)
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=30)

        # Video section
        video_section = tk.Frame(inner_frame, bg=self.colors['card'])
        video_section.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(
            video_section,
            text="🎬 VIDEO INPUT",
            font=('Segoe UI', 11, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['card']
        ).pack(anchor=tk.W)

        video_controls = tk.Frame(video_section, bg=self.colors['card'])
        video_controls.pack(fill=tk.X, pady=(8, 0))

        self.load_video_btn = self.create_modern_button(
            video_controls, "📁 Load Video", self.load_video, self.colors['success']
        )
        self.load_video_btn.pack(side=tk.LEFT, padx=(0, 15))

        # Video loading progress
        self.video_loading_frame = tk.Frame(video_controls, bg=self.colors['card'])
        self.video_loading_frame.pack(side=tk.LEFT)

        self.video_loading_var = tk.DoubleVar()
        self.video_loading_progress = ttk.Progressbar(
            self.video_loading_frame,
            variable=self.video_loading_var,
            maximum=100,
            length=200,
            style='Loading.TProgressbar'
        )

        self.video_loading_label = tk.Label(
            self.video_loading_frame,
            text="",
            fg=self.colors['success'],
            bg=self.colors['card'],
            font=('Segoe UI', 9)
        )

        # Analysis controls (right side)
        analysis_section = tk.Frame(inner_frame, bg=self.colors['card'])
        analysis_section.pack(side=tk.RIGHT, fill=tk.Y)

        self.analyze_btn = self.create_modern_button(
            analysis_section, "🔍 START ANALYSIS", self.toggle_analysis,
            self.colors['real'], 'large'
        )
        self.analyze_btn.config(state=tk.DISABLED)
        self.analyze_btn.pack()

    def setup_dual_video_panel(self, parent):
        """Setup the dual video display panel"""
        # Title
        title_frame = tk.Frame(parent, bg=self.colors['card'])
        title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        tk.Label(
            title_frame,
            text="📹 MULTI-HEAD VIDEO ANALYSIS",
            font=('Segoe UI', 16, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['card']
        ).pack()

        # Video container
        video_container = tk.Frame(parent, bg=self.colors['card'])
        video_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Left video (Original) - Larger size
        left_video_frame = tk.Frame(video_container, bg=self.colors['card'])
        left_video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        tk.Label(
            left_video_frame,
            text="📺 ORIGINAL VIDEO",
            font=('Segoe UI', 12, 'bold'),
            fg=self.colors['text_dim'],
            bg=self.colors['card']
        ).pack(pady=(0, 8))

        self.original_video_frame = tk.Frame(left_video_frame, bg='black', relief=tk.SUNKEN, bd=2)
        self.original_video_frame.pack(fill=tk.BOTH, expand=True)

        self.original_video_label = tk.Label(
            self.original_video_frame,
            text="🎬 Original Video\nNo Processing Applied\n\nLoad a video to begin multi-head analysis",
            font=('Segoe UI', 12),
            fg='white',
            bg='black',
            justify=tk.CENTER
        )
        self.original_video_label.pack(expand=True)

        # Right video (Processed with landmarks) - Larger size
        right_video_frame = tk.Frame(video_container, bg=self.colors['card'])
        right_video_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        tk.Label(
            right_video_frame,
            text="🎯 ANALYSIS VIEW",
            font=('Segoe UI', 12, 'bold'),
            fg=self.colors['text_dim'],
            bg=self.colors['card']
        ).pack(pady=(0, 8))

        self.processed_video_frame = tk.Frame(right_video_frame, bg='black', relief=tk.SUNKEN, bd=2)
        self.processed_video_frame.pack(fill=tk.BOTH, expand=True)

        self.processed_video_label = tk.Label(
            self.processed_video_frame,
            text="🎯 Analysis View\nMulti-Head Processing\n\nProcessed frames will appear here",
            font=('Segoe UI', 12),
            fg='white',
            bg='black',
            justify=tk.CENTER
        )
        self.processed_video_label.pack(expand=True)

        # Enhanced controls
        controls_frame = tk.Frame(parent, bg=self.colors['card'])
        controls_frame.pack(fill=tk.X, padx=20, pady=10)

        # Progress section
        progress_section = tk.Frame(controls_frame, bg=self.colors['card'])
        progress_section.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            progress_section,
            text="Multi-Head Analysis Progress:",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['text_dim'],
            bg=self.colors['card']
        ).pack(side=tk.LEFT)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_section,
            variable=self.progress_var,
            maximum=100,
            length=350,
            style='Modern.TProgressbar'
        )
        self.progress_bar.pack(side=tk.LEFT, padx=(10, 15))

        self.frame_label = tk.Label(
            progress_section,
            text="Frame: 0/0",
            fg=self.colors['text_dim'],
            bg=self.colors['card'],
            font=('Segoe UI', 10)
        )
        self.frame_label.pack(side=tk.LEFT)

        # Current prediction display with enhanced styling
        prediction_frame = tk.Frame(parent, bg=self.colors['card_light'], relief=tk.FLAT, bd=0)
        prediction_frame.pack(fill=tk.X, padx=20, pady=(10, 20))

        pred_inner = tk.Frame(prediction_frame, bg=self.colors['card_light'])
        pred_inner.pack(pady=15)

        self.prediction_label = tk.Label(
            pred_inner,
            text="PREDICTION: AWAITING MULTI-HEAD ANALYSIS",
            font=('Segoe UI', 18, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['card_light']
        )
        self.prediction_label.pack()

        self.confidence_label = tk.Label(
            pred_inner,
            text="Confidence: ---%",
            font=('Segoe UI', 14),
            fg=self.colors['text_dim'],
            bg=self.colors['card_light']
        )
        self.confidence_label.pack(pady=(5, 0))

        # Confidence explanation
        self.confidence_explanation = tk.Label(
            pred_inner,
            text="Multi-Head Model Confidence: How certain the AI model is about its prediction\n• 90-100%: Very High Certainty • 70-89%: High Certainty\n• 50-69%: Moderate Certainty • Below 50%: Low Certainty",
            font=('Segoe UI', 9),
            fg=self.colors['text_dim'],
            bg=self.colors['card_light'],
            justify=tk.CENTER
        )
        self.confidence_explanation.pack(pady=(8, 0))

    def setup_analysis_panel(self, parent):
        """Setup the enhanced analysis panel"""
        # Title
        title_frame = tk.Frame(parent, bg=self.colors['card'])
        title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        tk.Label(
            title_frame,
            text="📊 REAL-TIME ANALYSIS",
            font=('Segoe UI', 16, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['card']
        ).pack()

        # Charts with modern styling
        chart_frame = tk.Frame(parent, bg=self.colors['card'])
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.fig = Figure(figsize=(8, 10), facecolor=self.colors['card'])
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.setup_charts()

        # Enhanced statistics panel
        stats_frame = tk.Frame(parent, bg=self.colors['card_light'], relief=tk.FLAT, bd=0)
        stats_frame.pack(fill=tk.X, padx=20, pady=(10, 20))

        stats_header = tk.Frame(stats_frame, bg=self.colors['card_light'])
        stats_header.pack(fill=tk.X, pady=(15, 5))

        tk.Label(
            stats_header,
            text="📈 ANALYSIS STATISTICS",
            font=('Segoe UI', 14, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['card_light']
        ).pack()

        self.stats_text = tk.Text(
            stats_frame,
            height=8,
            bg=self.colors['bg'],
            fg=self.colors['text'],
            font=('Consolas', 9),
            relief=tk.FLAT,
            bd=0,
            wrap=tk.WORD,
            insertbackground=self.colors['accent']
        )
        self.stats_text.pack(fill=tk.X, padx=15, pady=(0, 15))

        # Add scrollbar for stats text
        stats_scrollbar = tk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.config(yscrollcommand=stats_scrollbar.set)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 15))

    def setup_charts(self):
        """Setup enhanced analysis charts with better spacing"""
        self.fig.clear()
        self.fig.patch.set_facecolor(self.colors['card'])

        # Create subplots with equal heights but MORE vertical space between them
        gs = self.fig.add_gridspec(3, 1, height_ratios=[1, 1, 1], hspace=0.8)

        # Top plot - taller for confidence over time
        self.ax1 = self.fig.add_subplot(gs[0])
        self.ax1.set_title('Multi-Head Confidence Score Over Time', color=self.colors['text'],
                           fontsize=12, fontweight='bold', pad=20)
        self.ax1.set_facecolor(self.colors['bg'])
        self.ax1.tick_params(colors=self.colors['text_dim'], labelsize=9)
        self.ax1.grid(True, alpha=0.3, color=self.colors['text_dim'])

        # Middle plot - timeline without legend
        self.ax2 = self.fig.add_subplot(gs[1])
        self.ax2.set_title('Multi-Head Temporal Authenticity Analysis', color=self.colors['text'],
                           fontsize=12, fontweight='bold', pad=20)
        self.ax2.set_facecolor(self.colors['bg'])
        self.ax2.tick_params(colors=self.colors['text_dim'], labelsize=9)

        # Bottom plot - horizontal bar chart
        self.ax3 = self.fig.add_subplot(gs[2])
        self.ax3.set_title('Multi-Head Frame Analysis Percentage', color=self.colors['text'],
                           fontsize=12, fontweight='bold', pad=20)
        self.ax3.set_facecolor(self.colors['bg'])
        self.ax3.tick_params(colors=self.colors['text_dim'], labelsize=9)

    def setup_status_bar(self, parent):
        """Setup enhanced status bar"""
        self.status_frame = tk.Frame(parent, bg=self.colors['card_light'], relief=tk.FLAT, bd=0)
        self.status_frame.pack(fill=tk.X, pady=(15, 0))

        # Status content
        status_inner = tk.Frame(self.status_frame, bg=self.colors['card_light'])
        status_inner.pack(fill=tk.X, pady=8)

        self.status_label = tk.Label(
            status_inner,
            text="🔄 Initializing Multi-Head Deepfake Analyzer...",
            fg=self.colors['text'],
            bg=self.colors['card_light'],
            font=('Segoe UI', 10),
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=15)

        # Processing indicator with animation
        self.processing_label = tk.Label(
            status_inner,
            text="",
            fg=self.colors['accent'],
            bg=self.colors['card_light'],
            font=('Segoe UI', 10)
        )
        self.processing_label.pack(side=tk.RIGHT, padx=15)

    def safe_load_model(self, model_path):
        """Safely load the Multi-Head LSTM model"""
        tf.keras.backend.clear_session()
        gc.collect()

        try:
            self.update_status(f"🔄 Loading Multi-Head model: {os.path.basename(model_path)}...")

            def load_model_isolated():
                with tf.keras.utils.custom_object_scope({}):
                    model = load_model(model_path, compile=False)
                model.compile(
                    optimizer='adam',
                    loss='binary_crossentropy',
                    metrics=['accuracy']
                )
                return model

            self.model = load_model_isolated()

            # Test the model with 9 dummy inputs (for multi-head model)
            test_inputs = self.create_dummy_inputs()
            _ = self.model.predict(test_inputs, verbose=0)

            self.update_status("✅ Multi-Head model loaded and verified successfully")
            return True

        except Exception as e:
            self.update_status(f"❌ Error loading model: {str(e)}")
            return False

    def create_dummy_inputs(self):
        """Create dummy inputs for the multi-head model"""
        # The multi-head model expects 9 inputs:
        # 4 facial regions (shape: batch, 64, 85 each)
        # 3 temporal chunks (shapes: batch, 22, 340), (batch, 22, 340), (batch, 20, 340)
        # 1 motion input (shape: batch, 64, 340)
        # 1 overall input (shape: batch, 64, 340)

        dummy_inputs = []

        # 4 facial region inputs (each 64 frames, 85 features)
        for i in range(4):
            dummy_inputs.append(np.zeros((1, 64, 85)).astype(np.float32))

        # 3 temporal inputs
        dummy_inputs.append(np.zeros((1, 22, 340)).astype(np.float32))  # early frames
        dummy_inputs.append(np.zeros((1, 22, 340)).astype(np.float32))  # middle frames
        dummy_inputs.append(np.zeros((1, 20, 340)).astype(np.float32))  # late frames

        # Motion input
        dummy_inputs.append(np.zeros((1, 64, 340)).astype(np.float32))

        # Overall input
        dummy_inputs.append(np.zeros((1, 64, 340)).astype(np.float32))

        return dummy_inputs

    def multi_head_feature_engineering(self, feature_buffer):
        """
        Apply multi-head feature engineering for the model
        """
        if len(feature_buffer) < self.chunk_size:
            return None

        # Convert to numpy array
        X = np.array(feature_buffer[-self.chunk_size:])
        X = X.reshape(1, self.chunk_size, -1)  # Add batch dimension

        n_features = X.shape[2]  # 340 features
        chunk_size = n_features // 4

        # Split features into 4 semantic groups
        face_region_1 = X[:, :, :chunk_size]
        face_region_2 = X[:, :, chunk_size:2 * chunk_size]
        face_region_3 = X[:, :, 2 * chunk_size:3 * chunk_size]
        face_region_4 = X[:, :, 3 * chunk_size:]

        # Temporal perspectives
        early_frames = X[:, :22, :]
        middle_frames = X[:, 22:44, :]
        late_frames = X[:, 44:, :]

        # Frame differences (motion)
        frame_diffs = np.diff(X, axis=1)
        frame_diffs = np.concatenate([frame_diffs, frame_diffs[:, -1:, :]], axis=1)

        # Return the 9 inputs in the correct order
        return [
            face_region_1,  # region 1
            face_region_2,  # region 2
            face_region_3,  # region 3
            face_region_4,  # region 4
            early_frames,  # temporal 1
            middle_frames,  # temporal 2
            late_frames,  # temporal 3
            frame_diffs,  # motion
            X  # overall
        ]

    def auto_load_model(self):
        """Automatically load the multi-head deepfake model if it exists"""
        if os.path.exists(self.model_path):
            try:
                self.update_status("🚀 Auto-loading Multi-Head Deepfake Model...")

                model_loaded = self.safe_load_model(self.model_path)

                if not model_loaded:
                    raise Exception("Failed to load Multi-Head model safely")

                # Initialize face detection
                self.face_detector = dlib.get_frontal_face_detector()

                # Try to load landmark predictor
                if os.path.exists("shape_predictor_68_face_landmarks.dat"):
                    self.landmark_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

                    self.model_status.config(
                        text="✅ Multi-Head Model Loaded",
                        fg=self.colors['real']
                    )
                    self.update_status(
                        "🚀 Multi-Head Deepfake Model loaded successfully - Ready for analysis!")
                else:
                    self.model_status.config(
                        text="⚠️ Multi-Head Model Loaded - Missing Landmarks",
                        fg=self.colors['uncertain']
                    )
                    self.update_status("⚠️ Multi-Head model loaded but landmark predictor missing")
                    messagebox.showwarning(
                        "Landmark Predictor Missing",
                        "Multi-Head model loaded successfully!\n\n"
                        "However, 'shape_predictor_68_face_landmarks.dat' is missing.\n"
                        "Please download it from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2\n\n"
                        "Extract and place it in the same directory as this script."
                    )

            except Exception as e:
                self.model_status.config(
                    text="❌ Failed to Load Multi-Head Model",
                    fg=self.colors['fake']
                )
                self.update_status(f"❌ Failed to auto-load Multi-Head model: {str(e)}")
                messagebox.showerror(
                    "Multi-Head Model Loading Error",
                    f"Failed to load multi_head_lstm.h5:\n\n{str(e)}\n\n"
                    "You can try loading a different model using 'Load Different Model' button."
                )
        else:
            self.model_status.config(
                text="❌ Multi-Head Model Not Found",
                fg=self.colors['fake']
            )
            self.update_status("❌ multi_head_lstm.h5 not found in current directory")
            messagebox.showinfo(
                "Multi-Head Model Not Found",
                "Could not find 'multi_head_lstm.h5' in the current directory.\n\n"
                "Please ensure the Multi-Head model file is in the same folder as this script,\n"
                "or use 'Load Different Model' to browse for your model file."
            )

    def load_model(self):
        """Load a different deepfake detection model"""
        file_path = filedialog.askopenfilename(
            title="Select Multi-Head Deepfake Detection Model",
            filetypes=[("Keras Model", "*.h5"), ("Keras Model", "*.keras"), ("All files", "*.*")]
        )

        if file_path:
            try:
                self.update_status("Loading Multi-Head alternative model...")

                model_loaded = self.safe_load_model(file_path)

                if not model_loaded:
                    raise Exception("Failed to load Multi-Head model safely")

                # Initialize face detection
                self.face_detector = dlib.get_frontal_face_detector()
                try:
                    self.landmark_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
                except:
                    messagebox.showwarning(
                        "Landmark Predictor Missing",
                        "shape_predictor_68_face_landmarks.dat not found. Please ensure it's in the current directory."
                    )
                    return

                self.model_status.config(text="✅ Multi-Head Alternative Model Loaded", fg=self.colors['real'])
                self.update_status(f"🚀 Multi-Head alternative model loaded: {os.path.basename(file_path)}")

                if self.video_loaded_successfully:
                    self.analyze_btn.config(state=tk.NORMAL)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load Multi-Head model: {str(e)}")
                self.update_status("❌ Failed to load Multi-Head alternative model")

    def load_video(self):
        """Load video file for analysis with smooth loading progress"""
        file_path = filedialog.askopenfilename(
            title="Select Video for Multi-Head Analysis",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            # Start video loading process
            self.is_loading_video = True
            self.video_loaded_successfully = False
            self.load_video_btn.config(state=tk.DISABLED, text="Loading...")
            self.analyze_btn.config(state=tk.DISABLED)

            # Show loading progress
            self.video_loading_progress.pack(side=tk.LEFT, padx=(0, 10))
            self.video_loading_label.pack(side=tk.LEFT)

            self.current_video = file_path
            self.update_status(f"🚀 Loading video for Multi-Head analysis: {os.path.basename(file_path)}...")

            # Start video loading in separate thread
            self.video_loading_thread = threading.Thread(
                target=self.load_video_async,
                args=(file_path,),
                daemon=True
            )
            self.video_loading_thread.start()

    def load_video_async(self, file_path):
        """Asynchronously load video and show progress"""
        try:
            # Open video to get properties
            cap = cv2.VideoCapture(file_path)

            if not cap.isOpened():
                raise Exception("Failed to open video file")

            # Get video properties
            self.total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.video_fps = cap.get(cv2.CAP_PROP_FPS)

            # Simulate loading progress by reading through video
            frames_processed = 0

            while frames_processed < self.total_video_frames and self.is_loading_video:
                ret, frame = cap.read()
                if not ret:
                    break

                frames_processed += 1
                progress = (frames_processed / self.total_video_frames) * 100

                # Update progress every 50 frames for smooth animation
                if frames_processed % 50 == 0 or frames_processed == self.total_video_frames:
                    self.root.after(0, self.update_video_loading_progress, progress, frames_processed)

                # Add small delay to show progress
                time.sleep(0.001)

            cap.release()

            # Video loaded successfully
            if self.is_loading_video:
                self.root.after(0, self.video_loading_complete, file_path)

        except Exception as e:
            self.root.after(0, self.video_loading_error, str(e))

    def update_video_loading_progress(self, progress, frames_processed):
        """Update video loading progress"""
        self.video_loading_var.set(progress)
        self.video_loading_label.config(
            text=f"Loading... {progress:.1f}% ({frames_processed:,}/{self.total_video_frames:,} frames)"
        )

    def video_loading_complete(self, file_path):
        """Handle video loading completion"""
        self.is_loading_video = False
        self.video_loaded_successfully = True

        # Hide loading progress
        self.video_loading_progress.pack_forget()
        self.video_loading_label.pack_forget()

        # Reset button and enable analysis
        self.load_video_btn.config(state=tk.NORMAL, text="📁 Load Video")

        if self.model:
            self.analyze_btn.config(state=tk.NORMAL)

        # Reset analysis data
        self.prediction_history.clear()
        self.confidence_history.clear()
        self.frame_timestamps.clear()
        self.frame_features.clear()
        self.frame_index = 0

        # Clear queues
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except:
                break

        self.update_status(
            f"✅ Video loaded for Multi-Head analysis: {os.path.basename(file_path)} ({self.total_video_frames:,} frames, {self.video_fps:.1f} fps)")

        # Show video info in status
        duration_seconds = self.total_video_frames / self.video_fps if self.video_fps > 0 else 0
        duration_minutes = duration_seconds / 60

        messagebox.showinfo(
            "Video Loaded for Multi-Head Analysis",
            f"✅ Video loaded and ready for Multi-Head analysis!\n\n"
            f"📊 Video Information:\n"
            f"• Total Frames: {self.total_video_frames:,}\n"
            f"• Frame Rate: {self.video_fps:.1f} fps\n"
            f"• Duration: {duration_minutes:.1f} minutes\n"
            f"• File: {os.path.basename(file_path)}\n\n"
            f"🚀 You can now click 'START MULTI-HEAD ANALYSIS' to begin!"
        )

    def video_loading_error(self, error_message):
        """Handle video loading error"""
        self.is_loading_video = False
        self.video_loaded_successfully = False

        # Hide loading progress
        self.video_loading_progress.pack_forget()
        self.video_loading_label.pack_forget()

        # Reset button
        self.load_video_btn.config(state=tk.NORMAL, text="📁 Load Video")

        self.update_status(f"❌ Failed to load video: {error_message}")
        messagebox.showerror("Video Loading Error", f"Failed to load video:\n\n{error_message}")

    def toggle_analysis(self):
        """Start or stop the analysis"""
        if not self.is_analyzing:
            self.start_analysis()
        else:
            self.stop_analysis()

    def start_analysis(self):
        """Start the video analysis with improved threading"""
        if not self.model or not self.current_video or not self.video_loaded_successfully:
            messagebox.showwarning("Missing Components", "Please load both Multi-Head model and video first.")
            return

        self.is_analyzing = True
        self.analyze_btn.config(text="⏹ STOP ANALYSIS", bg=self.colors['fake'])
        self.update_status("🚀 Multi-Head analysis in progress...")

        # Start analysis thread
        self.analysis_thread = threading.Thread(target=self.analyze_video, daemon=True)
        self.analysis_thread.start()

        # Start display thread for smooth video playback
        self.display_thread = threading.Thread(target=self.display_video, daemon=True)
        self.display_thread.start()

    def stop_analysis(self):
        """Stop the video analysis"""
        self.is_analyzing = False
        self.analyze_btn.config(text="🚀 START MULTI-HEAD ANALYSIS", bg=self.colors['real'])
        self.update_status("⏸ Multi-Head analysis stopped")

        # Clean up resources
        gc.collect()

    def analyze_video(self):
        """Main video analysis loop with Multi-Head model"""
        cap = cv2.VideoCapture(self.current_video)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        frame_count = 0
        features_buffer = []

        try:
            while self.is_analyzing and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Put frame in queue for display (non-blocking for smoother performance)
                try:
                    self.frame_queue.put(frame.copy(), block=False)
                except:
                    pass  # Skip if queue is full to maintain smooth playback

                # Extract features from current frame
                features = self.extract_frame_features(frame)
                if features is not None:
                    features_buffer.append(features)

                # Make prediction when we have enough frames using Multi-Head model
                if len(features_buffer) >= self.chunk_size:
                    try:
                        # Apply multi-head feature engineering
                        multi_head_inputs = self.multi_head_feature_engineering(features_buffer)

                        if multi_head_inputs is not None:
                            # Make prediction with the multi-head model
                            prediction = self.model.predict(multi_head_inputs, verbose=0)[0][0]

                            # FIXED: Calculate actual timestamp for this prediction
                            current_timestamp = frame_count / fps if fps > 0 else frame_count * (1 / 30)

                            self.prediction_history.append(prediction)
                            self.confidence_history.append(abs(prediction - 0.5) * 2)
                            self.frame_timestamps.append(current_timestamp)  # Store actual timestamp

                            # Update displays (throttled)
                            if frame_count % 3 == 0:  # Update every 3rd frame for smoothness
                                self.root.after(0, self.update_prediction_display, prediction)
                                self.root.after(0, self.update_charts)

                    except Exception as pred_error:
                        self.update_status(f"⚠️ Multi-Head prediction error: {str(pred_error)}")
                        gc.collect()
                        continue

                # Update progress
                frame_count += 1
                if frame_count % 5 == 0:  # Update progress every 5th frame
                    progress = (frame_count / total_frames) * 100
                    self.root.after(0, self.update_progress, progress, frame_count, total_frames)

                # Control analysis speed (smoother frame processing)
                time.sleep(1 / min(90, fps * 2.5))  # Increased FPS for smoother analysis

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Multi-Head Analysis Error",
                                                            f"Error during Multi-Head analysis: {str(e)}"))
        finally:
            cap.release()
            if self.is_analyzing:
                self.root.after(0, self.analysis_complete)

    def display_video(self):
        """Separate thread for smooth video display"""
        while self.is_analyzing:
            try:
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get(timeout=0.1)

                    # Create original and processed versions
                    original_frame = frame.copy()
                    processed_frame = self.add_analysis_overlay(frame.copy())

                    # Update displays
                    self.root.after(0, self.update_dual_video_display, original_frame, processed_frame)

                    # Memory cleanup
                    del frame, original_frame, processed_frame
                    gc.collect()

                time.sleep(1 / 60)  # 60 FPS display for smoother playback

            except Exception as e:
                continue

    def add_analysis_overlay(self, frame):
        """Add Multi-Head analysis overlay to frame"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_detector(gray)

            if len(faces) > 0:
                largest_face = max(faces, key=lambda rect: rect.width() * rect.height())

                # Draw face rectangle with Multi-Head styling
                x, y, w, h = largest_face.left(), largest_face.top(), largest_face.width(), largest_face.height()
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 3)  # Magenta for Multi-Head

                # Add face detection label
                cv2.putText(frame, 'MULTI-HEAD ANALYSIS', (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

                # Draw landmarks if predictor is available
                if self.landmark_predictor:
                    landmarks = self.landmark_predictor(gray, largest_face)

                    # Draw landmarks with Multi-Head color coding
                    for i in range(self.num_landmarks):
                        x_pt = landmarks.part(i).x
                        y_pt = landmarks.part(i).y

                        # Multi-Head color coding for different facial features
                        if i < 17:  # Jaw line
                            color = (255, 255, 0)  # Yellow
                        elif i < 27:  # Eyebrows
                            color = (255, 0, 255)  # Magenta
                        elif i < 36:  # Nose
                            color = (0, 255, 255)  # Cyan
                        elif i < 48:  # Eyes
                            color = (255, 0, 0)  # Blue
                        else:  # Mouth
                            color = (0, 255, 0)  # Green

                        cv2.circle(frame, (x_pt, y_pt), 2, color, -1)

            # Add Multi-Head analysis info overlay
            cv2.rectangle(frame, (10, 10), (350, 100), (0, 0, 0), -1)
            cv2.rectangle(frame, (10, 10), (350, 100), (255, 0, 255), 2)
            cv2.putText(frame, 'MULTI-HEAD STREAMS', (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
            cv2.putText(frame, f'9 Parallel Heads Active', (20, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame,
                        f'Faces: {len(faces)} | Landmarks: {self.num_landmarks if self.landmark_predictor else 0}',
                        (20, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            cv2.putText(frame, f'Multi-Head LSTM Processing', (20, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

        except Exception as e:
            pass  # Return frame as-is if processing fails

        return frame

    def update_dual_video_display(self, original_frame, processed_frame):
        """Update both video displays with larger size"""
        try:
            # Larger display size for better visibility
            display_size = (480, 360)

            # Original frame
            original_resized = cv2.resize(original_frame, display_size)
            original_rgb = cv2.cvtColor(original_resized, cv2.COLOR_BGR2RGB)
            original_image = Image.fromarray(original_rgb)
            original_photo = ImageTk.PhotoImage(original_image)

            # Processed frame
            processed_resized = cv2.resize(processed_frame, display_size)
            processed_rgb = cv2.cvtColor(processed_resized, cv2.COLOR_BGR2RGB)
            processed_image = Image.fromarray(processed_rgb)
            processed_photo = ImageTk.PhotoImage(processed_image)

            # Update labels
            self.original_video_label.config(image=original_photo)
            self.original_video_label.image = original_photo

            self.processed_video_label.config(image=processed_photo)
            self.processed_video_label.image = processed_photo

        except Exception as e:
            pass  # Silently handle display errors

    def extract_frame_features(self, frame):
        """Extract features from a single frame (optimized)"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_detector(gray)

            if len(faces) > 0:
                largest_face = max(faces, key=lambda rect: rect.width() * rect.height())
                return self.extract_landmarks_with_color(frame, largest_face)
            else:
                return np.zeros(self.feature_dim)
        except:
            return np.zeros(self.feature_dim)

    def extract_landmarks_with_color(self, frame, face_rect):
        """Extract facial landmarks with color information (optimized)"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_height, frame_width = frame_rgb.shape[:2]
        max_dim = max(frame_height, frame_width)

        landmarks = self.landmark_predictor(frame_rgb, face_rect)
        landmarks_with_color = []

        for i in range(self.num_landmarks):
            x = landmarks.part(i).x
            y = landmarks.part(i).y

            x = max(0, min(x, frame_width - 1))
            y = max(0, min(y, frame_height - 1))

            r, g, b = frame_rgb[y, x]

            x_norm = x / max_dim
            y_norm = y / max_dim
            r_norm = r / 255.0
            g_norm = g / 255.0
            b_norm = b / 255.0

            landmarks_with_color.extend([x_norm, y_norm, r_norm, g_norm, b_norm])

        return np.array(landmarks_with_color)

    def update_prediction_display(self, prediction):
        """Update prediction display with enhanced styling"""
        if prediction > 0.7:
            pred_text = "REAL"
            color = self.colors['real']
            icon = "✅"
        elif prediction < 0.3:
            pred_text = "FAKE"
            color = self.colors['fake']
            icon = "⚠️"
        else:
            pred_text = "UNCERTAIN"
            color = self.colors['uncertain']
            icon = "❓"

        confidence = abs(prediction - 0.5) * 2 * 100

        self.prediction_label.config(text=f"{icon} MULTI-HEAD PREDICTION: {pred_text}", fg=color)
        self.confidence_label.config(text=f"Multi-Head Confidence: {confidence:.1f}%")

    def update_charts(self):
        """Update analysis charts with Multi-Head data"""
        if not self.prediction_history:
            return

        # Clear axes
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        # Confidence over time
        confidence_data = list(self.confidence_history)
        if confidence_data:
            self.ax1.plot(confidence_data, color=self.colors['accent'], linewidth=2.5, alpha=0.8)
            self.ax1.fill_between(range(len(confidence_data)), confidence_data, alpha=0.3, color=self.colors['accent'])

        self.ax1.set_title('Multi-Head Confidence Over Time', color=self.colors['text'], fontsize=11,
                           fontweight='bold', pad=10)
        self.ax1.set_facecolor(self.colors['bg'])
        self.ax1.tick_params(colors=self.colors['text_dim'], labelsize=8)
        self.ax1.set_ylim(0, 1)
        self.ax1.grid(True, alpha=0.2, color=self.colors['text_dim'])

        # Timeline visualization
        predictions = list(self.prediction_history)
        if len(predictions) > 5:
            timeline_length = min(len(predictions), 100)
            recent_predictions = predictions[-timeline_length:]

            x_values = range(len(recent_predictions))
            self.ax2.plot(x_values, recent_predictions, color=self.colors['accent'], linewidth=3, alpha=0.8)

            real_mask = np.array(recent_predictions) > 0.5
            fake_mask = np.array(recent_predictions) < 0.5

            if np.any(real_mask):
                self.ax2.fill_between(x_values, recent_predictions, 0.5, where=real_mask,
                                      color=self.colors['real'], alpha=0.3, label='REAL')
            if np.any(fake_mask):
                self.ax2.fill_between(x_values, recent_predictions, 0.5, where=fake_mask,
                                      color=self.colors['fake'], alpha=0.3, label='FAKE')

            self.ax2.axhline(y=0.5, color=self.colors['text_dim'], linestyle='--', alpha=0.7, linewidth=2)
            self.ax2.set_ylim(0, 1)
            self.ax2.set_xlim(0, len(recent_predictions))
            self.ax2.grid(True, alpha=0.3, color=self.colors['text_dim'])

        self.ax2.set_title('Multi-Head Analysis Timeline', color=self.colors['text'], fontsize=12, fontweight='bold',
                           pad=15)
        self.ax2.set_facecolor(self.colors['bg'])
        self.ax2.tick_params(colors=self.colors['text_dim'], labelsize=8)

        # Bar chart - Cumulative percentages over ALL predictions made so far (NOT just last 200!)
        if self.prediction_history:
            # Get ALL predictions made since analysis started
            all_predictions = list(self.prediction_history)  # This gets ALL predictions, not just last 200!
            total_analyzed_frames = len(all_predictions)

            # Count REAL and FAKE from ALL predictions made so far
            real_count = sum(1 for p in all_predictions if p > 0.5)
            fake_count = total_analyzed_frames - real_count

            # Calculate cumulative percentages from ALL predictions
            real_percentage = (real_count / total_analyzed_frames) * 100 if total_analyzed_frames > 0 else 0
            fake_percentage = (fake_count / total_analyzed_frames) * 100 if total_analyzed_frames > 0 else 0

            # SAFETY CHECK: Ensure percentages add up to 100%
            total_percentage = real_percentage + fake_percentage
            if total_percentage > 0:
                real_percentage = (real_percentage / total_percentage) * 100
                fake_percentage = (fake_percentage / total_percentage) * 100

            # Create the bar chart
            categories = ['REAL', 'FAKE']
            percentages = [real_percentage, fake_percentage]
            colors = [self.colors['real'], self.colors['fake']]

            bars = self.ax3.barh(categories, percentages, color=colors, alpha=0.8, height=0.6)

            # Add percentage labels on bars with CLEAR indication this is ALL frames
            for i, (bar, percentage, count, category) in enumerate(
                    zip(bars, percentages, [real_count, fake_count], categories)):
                width = bar.get_width()

                # Position text based on bar width
                if percentage > 15:
                    x_pos = width / 2
                    ha = 'center'
                    color = 'white'
                    fontweight = 'bold'
                else:
                    x_pos = width + 2
                    ha = 'left'
                    color = self.colors['text']
                    fontweight = 'normal'

                # Display both percentage and count - CLEARLY showing ALL frames
                text = f'{category}: {percentage:.1f}% ({count:,} frames)'

                self.ax3.text(x_pos, bar.get_y() + bar.get_height() / 2, text,
                              ha=ha, va='center', color=color, fontsize=10, fontweight=fontweight)

            # Set up the axes
            self.ax3.set_xlim(0, 100)
            self.ax3.set_xlabel('Percentage of ALL Analyzed Frames (%)', color=self.colors['text_dim'], fontsize=10)

            # Remove y-axis labels
            self.ax3.set_yticks([])
            self.ax3.set_yticklabels([])
            self.ax3.tick_params(left=False, right=False, labelleft=False, labelright=False)

            # Add grid for x-axis only
            self.ax3.grid(True, alpha=0.3, color=self.colors['text_dim'], axis='x')
            self.ax3.set_facecolor(self.colors['bg'])
            self.ax3.tick_params(colors=self.colors['text_dim'], labelsize=8)

            # Add VERY CLEAR summary showing this is ALL frames analyzed
            self.ax3.text(50, -0.5,
                          f'📊 CUMULATIVE RESULTS - ALL {total_analyzed_frames:,} ANALYZED FRAMES | Real: {real_count:,} | Fake: {fake_count:,}',
                          ha='center', va='center', color=self.colors['text_dim'], fontsize=9, fontweight='bold')

        # CRYSTAL CLEAR title showing this is ALL frames, not recent ones
        self.ax3.set_title('📊 CUMULATIVE ANALYSIS - ALL FRAMES ANALYZED SO FAR', color=self.colors['text'],
                           fontsize=12, fontweight='bold', pad=15)

        plt.tight_layout(pad=1.5)
        self.canvas.draw()

        # Update statistics
        self.update_statistics()

    def find_fake_timestamps(self):
        """Find specific timestamps where the model is most confident the video is fake"""
        if not self.prediction_history:
            print("DEBUG: No prediction history")
            return []

        predictions = list(self.prediction_history)
        timestamps = list(self.frame_timestamps) if self.frame_timestamps else []
        confidences = list(self.confidence_history)

        print(f"DEBUG: Predictions: {len(predictions)}, Timestamps: {len(timestamps)}, Confidences: {len(confidences)}")

        # FIXED: Create accurate timestamps based on actual video duration
        if len(timestamps) == 0:
            print("DEBUG: No timestamps found, creating accurate ones based on video properties")
            # Calculate actual video duration in seconds
            total_video_duration = self.total_video_frames / self.video_fps if self.video_fps > 0 else len(
                predictions) * 0.5

            for i in range(len(predictions)):
                # Calculate proportional timestamp within actual video duration
                timestamp = (i / len(predictions)) * total_video_duration
                timestamps.append(timestamp)

            print(f"DEBUG: Created {len(timestamps)} timestamps for {total_video_duration:.1f}s video")

        # Only return timestamps if overall prediction is FAKE
        fake_count = sum(1 for p in predictions if p < 0.5)
        total_count = len(predictions)
        overall_fake_percentage = (fake_count / total_count) * 100

        print(
            f"DEBUG: Total predictions: {total_count}, Fake count: {fake_count}, Fake %: {overall_fake_percentage:.1f}")

        # MUCH MORE LENIENT: Show timestamps if >30% fake frames
        if overall_fake_percentage <= 30:
            print(f"DEBUG: Video not fake enough ({overall_fake_percentage:.1f}% fake), no timestamps")
            return []

        # VERY LENIENT CRITERIA - just find the most fake predictions
        suspicious_moments = []

        # Find bottom 25% of predictions (most fake)
        sorted_predictions = sorted(enumerate(predictions), key=lambda x: x[1])
        bottom_25_percent = sorted_predictions[:max(1, len(sorted_predictions) // 4)]

        print(f"DEBUG: Looking at bottom 25% of predictions ({len(bottom_25_percent)} frames)")

        for idx, pred in bottom_25_percent:
            if idx < len(timestamps):
                suspicious_moments.append({
                    'timestamp': timestamps[idx],
                    'prediction': pred,
                    'confidence': confidences[idx] if idx < len(confidences) else 0.5,
                    'certainty': (0.5 - pred) * 2
                })

        print(f"DEBUG: Found {len(suspicious_moments)} suspicious moments")

        if len(suspicious_moments) == 0:
            print("DEBUG: No suspicious moments found, returning empty")
            return []

        # Sort by how fake they are
        suspicious_moments.sort(key=lambda x: x['prediction'])  # Most fake first (lowest values)

        # Group nearby timestamps (within 5 seconds) to avoid spam
        grouped_moments = []
        for moment in suspicious_moments[:10]:
            # Check if this timestamp is close to any existing one
            is_close = False
            for existing in grouped_moments:
                if abs(moment['timestamp'] - existing['timestamp']) < 5.0:
                    is_close = True
                    break

            if not is_close:
                grouped_moments.append(moment)

            # Max 5 timestamps
            if len(grouped_moments) >= 5:
                break

        print(f"DEBUG: Final grouped moments: {len(grouped_moments)}")
        for i, moment in enumerate(grouped_moments):
            print(f"  {i + 1}. {self.format_timestamp(moment['timestamp'])}: pred={moment['prediction']:.3f}")

        return grouped_moments

    def format_timestamp(self, seconds):
        """Format seconds to MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def update_statistics(self):
        if not self.prediction_history:
            return

        predictions = list(self.prediction_history)
        confidences = list(self.confidence_history)

        # Calculate percentages based on analyzed frames
        analyzed_real_count = sum(1 for p in predictions if p > 0.5)
        analyzed_fake_count = len(predictions) - analyzed_real_count

        # Calculate percentages from analyzed frames
        real_percentage = (analyzed_real_count / len(predictions)) * 100
        fake_percentage = (analyzed_fake_count / len(predictions)) * 100

        # Apply these percentages to total video frames
        total_real_frames = int((real_percentage / 100) * self.total_video_frames)
        total_fake_frames = self.total_video_frames - total_real_frames

        avg_confidence = np.mean(confidences) if confidences else 0
        max_confidence = np.max(confidences) if confidences else 0
        min_confidence = np.min(confidences) if confidences else 0

        # Calculate trend
        if len(predictions) >= 10:
            recent_trend = np.mean(predictions[-10:]) - np.mean(predictions[-20:-10]) if len(predictions) >= 20 else 0
            trend_text = "📈 Trending REAL" if recent_trend > 0.1 else "📉 Trending FAKE" if recent_trend < -0.1 else "➡️ Stable"
        else:
            trend_text = "🔄 Analyzing..."

        # Find suspicious timestamps (only if video is determined fake)
        suspicious_moments = self.find_fake_timestamps()

        stats_text = f"""╔══════════════════════════════════════════════════════════════╗
║                   MULTI-HEAD ANALYSIS                        ║
╠══════════════════════════════════════════════════════════════╣
║ TOTAL VIDEO ANALYSIS (Multi-Head LSTM)                      ║
║ Total Frames:          {self.total_video_frames:>6}                             ║
║ Real Frames:           {total_real_frames:>6} ({real_percentage:>5.1f}%)                ║
║ Fake Frames:           {total_fake_frames:>6} ({fake_percentage:>5.1f}%)                ║
║                                                              ║
║ SAMPLE ANALYSIS                                              ║
║ Frames Analyzed:       {len(predictions):>6}                             ║
║ Analysis Coverage:     {(len(predictions) / self.total_video_frames) * 100:>5.1f}%                          ║
║                                                              ║
║ CONFIDENCE METRICS                                           ║
║ Average Confidence:    {avg_confidence * 100:>5.1f}%                          ║
║ Peak Confidence:       {max_confidence * 100:>5.1f}%                          ║
║ Lowest Confidence:     {min_confidence * 100:>5.1f}%                          ║
║                                                              ║
║ CURRENT STATUS                                               ║
║ Head Status:           9 Heads Active                       ║
║ Trend:                 {trend_text:<20}                    ║
║ Latest Prediction:     {'REAL' if predictions[-1] > 0.5 else 'FAKE':<6} ({confidences[-1] * 100:>5.1f}%)              ║"""

        # Add suspicious timestamps as SEPARATE LINES for better visibility
        if suspicious_moments:
            stats_text += f"""
║                                                              ║
║ 🚨 SUSPICIOUS TIMESTAMPS DETECTED:                          ║"""

            # Add each timestamp on its own line for maximum visibility
            for i, moment in enumerate(suspicious_moments[:5]):
                timestamp_str = self.format_timestamp(moment['timestamp'])
                confidence_str = f"{moment['certainty'] * 100:.0f}%"
                stats_text += f"""
║ • {timestamp_str} - Fake Confidence: {confidence_str:<20}              ║"""

        stats_text += """
╚══════════════════════════════════════════════════════════════╝"""

        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, stats_text)

        # IMPORTANT: Auto-scroll to show suspicious timestamps at the bottom
        if suspicious_moments:
            self.stats_text.see(tk.END)  # Scroll to bottom to show timestamps

    def update_progress(self, progress, current_frame, total_frames):
        """Update progress bar and frame counter"""
        self.progress_var.set(progress)
        self.frame_label.config(text=f"Frame: {current_frame:,}/{total_frames:,}")

    def analysis_complete(self):
        """Handle analysis completion with enhanced results"""
        self.is_analyzing = False
        self.analyze_btn.config(text="🔍 START ANALYSIS", bg=self.colors['real'])
        self.update_status("✅ Multi-Head analysis completed successfully")

        # Clean up resources
        gc.collect()

        # Show enhanced final results with custom dialog
        if self.prediction_history:
            self.show_multi_head_results_dialog()

    def export_multi_head_report(self, real_percentage, fake_percentage, total_real_frames, total_fake_frames,
                                 avg_confidence):
        """Export Multi-Head analysis report"""
        try:
            from datetime import datetime

            # Determine verdict
            if real_percentage > 70:
                verdict = "REAL"
            elif real_percentage < 30:
                verdict = "FAKE"
            else:
                verdict = "UNCERTAIN"

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"multi_head_deepfake_analysis_{timestamp}.txt"
            video_name = os.path.basename(self.current_video) if self.current_video else "Unknown"

            report_content = f"""MULTI-HEAD DEEPFAKE ANALYSIS REPORT
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{'=' * 60}

FILE: {video_name}
VERDICT: {verdict}
MODEL: Multi-Head LSTM Architecture

MULTI-HEAD ANALYSIS RESULTS:
Total Frames: {self.total_video_frames:,}
Real: {total_real_frames:,} frames ({real_percentage:.1f}%)
Fake: {total_fake_frames:,} frames ({fake_percentage:.1f}%)
Average Multi-Head Confidence: {avg_confidence:.1f}%

MULTI-HEAD ANALYSIS DETAILS:
Frames Analyzed: {len(self.prediction_history):,}
Coverage: {(len(self.prediction_history) / self.total_video_frames) * 100:.1f}%
Architecture: Multi-Head Multi-Input LSTM
Heads: 4 Facial Regions + 3 Temporal + Motion + Overall
Model: Multi-Head Deepfake Detector v3.0

TECHNICAL SPECIFICATIONS:
- Parallel Processing Heads: 9
- Feature Engineering: Multi-Head Multi-Perspective
- Temporal Analysis: Early/Middle/Late Frame Chunks
- Motion Detection: Frame Difference Analysis
- Facial Region Analysis: 4 Specialized Regions
- Confidence Calculation: Multi-Head Ensemble
"""

            with open(report_filename, 'w') as f:
                f.write(report_content)

            messagebox.showinfo("Multi-Head Report Exported",
                                f"Multi-Head report saved: {report_filename}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export Multi-Head report: {str(e)}")

    def show_multi_head_results_dialog(self):
        """Show Multi-Head results dialog"""
        predictions = list(self.prediction_history)
        confidences = list(self.confidence_history)

        # Calculate percentages based on analyzed frames
        analyzed_frames = len(predictions)
        analyzed_real_count = sum(1 for p in predictions if p > 0.5)

        # Calculate percentages from analyzed frames
        real_percentage = (analyzed_real_count / analyzed_frames) * 100
        fake_percentage = 100 - real_percentage

        # Apply these percentages to total video frames
        total_real_frames = int((real_percentage / 100) * self.total_video_frames)
        total_fake_frames = self.total_video_frames - total_real_frames

        # Determine verdict based on Multi-Head criteria
        if real_percentage > 80:
            verdict = "REAL"
            verdict_icon = "✅"
            verdict_color = self.colors['real']
        elif real_percentage < 30:
            verdict = "FAKE"
            verdict_icon = "❌"
            verdict_color = self.colors['fake']
        else:
            verdict = "UNCERTAIN"
            verdict_icon = "❓"
            verdict_color = self.colors['uncertain']

        # Calculate average confidence
        avg_confidence = np.mean(confidences) * 100 if confidences else 0

        # Create Multi-Head results dialog
        result_dialog = tk.Toplevel(self.root)
        result_dialog.title("🚀 Multi-Head Analysis Results")
        result_dialog.geometry("650x500")
        result_dialog.configure(bg=self.colors['bg'])
        result_dialog.resizable(False, False)

        # Center the dialog
        result_dialog.transient(self.root)
        result_dialog.grab_set()

        # Main container
        main_frame = tk.Frame(result_dialog, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)

        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors['card'], relief=tk.FLAT, bd=0)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        header_inner = tk.Frame(header_frame, bg=self.colors['card'])
        header_inner.pack(pady=20)

        # Title
        title_label = tk.Label(
            header_inner,
            text=f"🚀 MULTI-HEAD ANALYSIS",
            font=('Segoe UI', 24, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['card']
        )
        title_label.pack()

        verdict_label = tk.Label(
            header_inner,
            text=f"{verdict_icon} {verdict}",
            font=('Segoe UI', 28, 'bold'),
            fg=verdict_color,
            bg=self.colors['card']
        )
        verdict_label.pack(pady=(10, 0))

        # Results section
        results_frame = tk.Frame(main_frame, bg=self.colors['card_light'], relief=tk.FLAT, bd=0)
        results_frame.pack(fill=tk.X, pady=(0, 25))

        results_inner = tk.Frame(results_frame, bg=self.colors['card_light'])
        results_inner.pack(pady=20)

        # Multi-Head results
        tk.Label(
            results_inner,
            text="MULTI-HEAD ANALYSIS RESULTS",
            font=('Segoe UI', 16, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['card_light']
        ).pack()

        # Results text
        results_text = f"""
Multi-Head Architecture Analysis:

Total Frames: {self.total_video_frames:,}
Real: {total_real_frames:,} frames ({real_percentage:.1f}%)
Fake: {total_fake_frames:,} frames ({fake_percentage:.1f}%)

Multi-Head Confidence: {avg_confidence:.1f}%
Frames Analyzed: {analyzed_frames:,}
        """

        # Add suspicious timestamps to results dialog if video is fake
        suspicious_moments = self.find_fake_timestamps()
        if suspicious_moments:
            results_text += f"\n\n🚨 SUSPICIOUS TIMESTAMPS DETECTED:\n"
            for i, moment in enumerate(suspicious_moments[:5]):
                timestamp_str = self.format_timestamp(moment['timestamp'])
                confidence_str = f"{moment['certainty'] * 100:.0f}%"
                results_text += f"• {timestamp_str} - Fake Confidence: {confidence_str}\n"

        results_label = tk.Label(
            results_inner,
            text=results_text,
            font=('Segoe UI', 12),
            fg=self.colors['text'],
            bg=self.colors['card_light'],
            justify=tk.CENTER
        )
        results_label.pack(pady=10)

        # Enhanced buttons section with Multi-Head styling
        button_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, pady=(25, 0))

        # Separator line above buttons
        separator = tk.Frame(button_frame, bg=self.colors['border'], height=1)
        separator.pack(fill=tk.X, pady=(0, 20))

        # Create a sub-frame for button alignment
        button_container = tk.Frame(button_frame, bg=self.colors['bg'])
        button_container.pack(fill=tk.X)

        # Export/Save button - LEFT side with Multi-Head styling
        export_btn = tk.Button(
            button_container,
            text="💾 SAVE MULTI-HEAD REPORT",
            command=lambda: self.export_multi_head_report(real_percentage, fake_percentage, total_real_frames,
                                                          total_fake_frames, avg_confidence),
            bg=self.colors['accent'],
            fg='white',
            font=('Segoe UI', 14, 'bold'),
            relief=tk.FLAT,
            padx=30,
            pady=12,
            cursor='hand2',
            activebackground=self.lighten_color(self.colors['accent']),
            activeforeground='white',
            bd=0,
            width=20
        )
        export_btn.pack(side=tk.LEFT, padx=(0, 15))

        # Add hover effects for export button
        export_btn.bind("<Enter>", lambda e: export_btn.config(bg=self.lighten_color(self.colors['accent'])))
        export_btn.bind("<Leave>", lambda e: export_btn.config(bg=self.colors['accent']))

        # Close button - RIGHT side with Multi-Head styling
        close_btn = tk.Button(
            button_container,
            text="✖️ CLOSE",
            command=result_dialog.destroy,
            bg=self.colors['success'],
            fg='white',
            font=('Segoe UI', 14, 'bold'),
            relief=tk.FLAT,
            padx=30,
            pady=12,
            cursor='hand2',
            activebackground=self.lighten_color(self.colors['success']),
            activeforeground='white',
            bd=0,
            width=15
        )
        close_btn.pack(side=tk.RIGHT, padx=(15, 0))

        # Add hover effects for close button
        close_btn.bind("<Enter>", lambda e: close_btn.config(bg=self.lighten_color(self.colors['success'])))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg=self.colors['success']))

        # Add keyboard shortcuts
        result_dialog.bind('<Return>', lambda e: result_dialog.destroy())  # Enter to close
        result_dialog.bind('<Escape>', lambda e: result_dialog.destroy())  # Escape to close
        result_dialog.bind('<Control-s>',
                           lambda e: self.export_multi_head_report(real_percentage, fake_percentage,
                                                                   total_real_frames,
                                                                   total_fake_frames,
                                                                   avg_confidence))  # Ctrl+S to save

        # Center the dialog on screen
        result_dialog.update_idletasks()
        x = (result_dialog.winfo_screenwidth() - result_dialog.winfo_width()) // 2
        y = (result_dialog.winfo_screenheight() - result_dialog.winfo_height()) // 2
        result_dialog.geometry(f"+{x}+{y}")

        # Focus on the dialog
        result_dialog.focus_set()

    def update_status(self, message):
        """Update status bar with animation"""
        self.status_label.config(text=message)

        # Add processing animation
        if "progress" in message.lower() or "analyzing" in message.lower():
            self.animate_processing()

    def animate_processing(self):
        """Animate processing indicator"""
        animations = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

        def update_animation(index=0):
            if self.is_analyzing:
                self.processing_label.config(text=f"{animations[index % len(animations)]} Processing...")
                self.root.after(100, lambda: update_animation(index + 1))
            else:
                self.processing_label.config(text="")

        update_animation()


def main():
    """Main function to run the Multi-Head GUI application"""
    root = tk.Tk()

    # Set application icon (if available)
    try:
        root.iconbitmap('icon.ico')  # Add your icon file
    except:
        pass

    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    app = DeepfakeDetectionGUI(root)

    # Handle window closing
    def on_closing():
        if app.is_analyzing or app.is_loading_video:
            if messagebox.askokcancel("Quit", "Multi-Head analysis in progress. Do you want to quit?"):
                app.is_analyzing = False
                app.is_loading_video = False
                root.quit()
        else:
            root.quit()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()