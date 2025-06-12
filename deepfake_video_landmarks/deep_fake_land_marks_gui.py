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
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'   # Reduce TensorFlow logging noise

# Now import TensorFlow after setting environment variables
import tensorflow as tf
from tensorflow.keras.models import load_model


class DeepfakeDetectionGUI:
    """
    Enhanced Professional GUI for deepfake detection analysis with dual video display
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Deepfake Detection Analyzer v2.1")
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
        self.model_path = "enhanced_deepfake_lstm_model_fallback.h5"

        # Analysis parameters
        self.chunk_size = 64
        self.num_landmarks = 68
        self.features_per_landmark = 5
        self.feature_dim = self.num_landmarks * self.features_per_landmark

        # Data storage
        self.prediction_history = deque(maxlen=200)
        self.confidence_history = deque(maxlen=200)
        self.frame_features = []
        self.current_frame = None
        self.current_frame_processed = None
        self.frame_index = 0
        self.total_video_frames = 0
        self.video_fps = 30

        # Threading for smooth display
        self.frame_queue = Queue(maxsize=10)  # Increased buffer for smoother playback
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
            text="🎯 ENHANCED DEEPFAKE DETECTION ANALYZER",
            font=('Segoe UI', 26, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['bg']
        )
        title_label.pack()

        subtitle_label = tk.Label(
            title_frame,
            text="v2.1 • Dual Video Display • Real-time Analysis • Enhanced LSTM Model",
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
            text="🔄 Loading Enhanced Model...",
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
            text="📹 DUAL VIDEO ANALYSIS",
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
            text="🎬 Original Video\nNo Processing Applied\n\nLoad a video to begin analysis",
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
            text="🔍 Analysis View\nLandmarks & Face Detection\n\nProcessed frames will appear here",
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
            text="Analysis Progress:",
            font=('Segoe UI', 10, 'bold'),
            fg=self.colors['text_dim'],
            bg=self.colors['card']
        ).pack(side=tk.LEFT)

        self.progress_var = tk.DoubleVar()
        # Now this will work because setup_styles() was called first
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
            text="PREDICTION: AWAITING ANALYSIS",
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
            text="Confidence Level: How certain the AI model is about its prediction\n• 90-100%: Very High Certainty • 70-89%: High Certainty\n• 50-69%: Moderate Certainty • Below 50%: Low Certainty",
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
            height=6,
            bg=self.colors['bg'],
            fg=self.colors['text'],
            font=('Consolas', 10),
            relief=tk.FLAT,
            bd=0,
            wrap=tk.WORD,
            insertbackground=self.colors['accent']
        )
        self.stats_text.pack(fill=tk.X, padx=15, pady=(0, 15))

    def setup_charts(self):
        """Setup enhanced analysis charts with better spacing"""
        self.fig.clear()

        # Set the figure background
        self.fig.patch.set_facecolor(self.colors['card'])

        # Create subplots with equal heights but MORE vertical space between them
        gs = self.fig.add_gridspec(3, 1, height_ratios=[1, 1, 1], hspace=0.8)

        # Top plot - taller for confidence over time
        self.ax1 = self.fig.add_subplot(gs[0])
        self.ax1.set_title('Confidence Score Over Time', color=self.colors['text'],
                           fontsize=12, fontweight='bold', pad=20)
        self.ax1.set_facecolor(self.colors['bg'])
        self.ax1.tick_params(colors=self.colors['text_dim'], labelsize=9)
        self.ax1.grid(True, alpha=0.3, color=self.colors['text_dim'])

        # Middle plot - timeline without legend
        self.ax2 = self.fig.add_subplot(gs[1])
        self.ax2.set_title('Temporal Authenticity Analysis', color=self.colors['text'],
                           fontsize=12, fontweight='bold', pad=20)
        self.ax2.set_facecolor(self.colors['bg'])
        self.ax2.tick_params(colors=self.colors['text_dim'], labelsize=9)

        # Bottom plot - horizontal bar chart
        self.ax3 = self.fig.add_subplot(gs[2])
        self.ax3.set_title('Frame Analysis Percentage', color=self.colors['text'],
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
            text="🔄 Initializing Enhanced Deepfake Analyzer...",
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
        """Safely load a TensorFlow model with extensive error handling"""
        # Clear any existing TensorFlow session and free memory
        tf.keras.backend.clear_session()
        gc.collect()
        
        try:
            # First try the simplest approach
            self.update_status(f"🔄 Loading model: {os.path.basename(model_path)}...")
            
            # Use a separate function to isolate model loading
            def load_model_isolated():
                with tf.keras.utils.custom_object_scope({}):
                    model = load_model(model_path, compile=False)
                model.compile(
                    optimizer='adam',
                    loss='binary_crossentropy',
                    metrics=['accuracy']
                )
                return model
            
            # Load the model
            self.model = load_model_isolated()
            
            # Test the model with a simple prediction to ensure it works
            test_data = np.zeros((1, 64, 340)).astype(np.float32)
            _ = self.model.predict(test_data, verbose=0)
            
            self.update_status("✅ Model loaded and verified successfully")
            return True
            
        except Exception as e:
            self.update_status(f"❌ Error loading model: {str(e)}")
            return False
    
    def auto_load_model(self):
        """Automatically load the enhanced deepfake model if it exists"""
        if os.path.exists(self.model_path):
            try:
                self.update_status("🔄 Auto-loading Enhanced Deepfake Model...")
                
                # Use our safe model loading function
                model_loaded = self.safe_load_model(self.model_path)
                
                if not model_loaded:
                    raise Exception("Failed to load model safely")

                # Initialize face detection
                self.face_detector = dlib.get_frontal_face_detector()

                # Try to load landmark predictor
                if os.path.exists("shape_predictor_68_face_landmarks.dat"):
                    self.landmark_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

                    self.model_status.config(
                        text="✅ Enhanced Model Loaded",
                        fg=self.colors['real']
                    )
                    self.update_status("🟢 Enhanced Deepfake Model loaded successfully - Ready for analysis!")
                else:
                    self.model_status.config(
                        text="⚠️ Model Loaded - Missing Landmarks",
                        fg=self.colors['uncertain']
                    )
                    self.update_status("⚠️ Model loaded but landmark predictor missing")
                    messagebox.showwarning(
                        "Landmark Predictor Missing",
                        "Enhanced model loaded successfully!\n\n"
                        "However, 'shape_predictor_68_face_landmarks.dat' is missing.\n"
                        "Please download it from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2\n\n"
                        "Extract and place it in the same directory as this script."
                    )

            except Exception as e:
                self.model_status.config(
                    text="❌ Failed to Load Enhanced Model",
                    fg=self.colors['fake']
                )
                self.update_status(f"❌ Failed to auto-load enhanced model: {str(e)}")
                messagebox.showerror(
                    "Model Loading Error",
                    f"Failed to load enhanced_deepfake_lstm_model.h5:\n\n{str(e)}\n\n"
                    "You can try loading a different model using 'Load Different Model' button."
                )
        else:
            self.model_status.config(
                text="❌ Enhanced Model Not Found",
                fg=self.colors['fake']
            )
            self.update_status("❌ enhanced_deepfake_lstm_model.h5 not found in current directory")
            messagebox.showinfo(
                "Enhanced Model Not Found",
                "Could not find 'enhanced_deepfake_lstm_model.h5' in the current directory.\n\n"
                "Please ensure the model file is in the same folder as this script,\n"
                "or use 'Load Different Model' to browse for your model file."
            )

    def load_model(self):
        """Load a different deepfake detection model"""
        file_path = filedialog.askopenfilename(
            title="Select Alternative Deepfake Detection Model",
            filetypes=[("Keras Model", "*.h5"), ("Keras Model", "*.keras"), ("All files", "*.*")]
        )

        if file_path:
            try:
                self.update_status("Loading alternative model...")
                
                # Use our safe model loading function
                model_loaded = self.safe_load_model(file_path)
                
                if not model_loaded:
                    raise Exception("Failed to load model safely")

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

                self.model_status.config(text="✅ Alternative Model Loaded", fg=self.colors['real'])
                self.update_status(f"🟢 Alternative model loaded: {os.path.basename(file_path)}")

                if self.video_loaded_successfully:
                    self.analyze_btn.config(state=tk.NORMAL)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load model: {str(e)}")
                self.update_status("❌ Failed to load alternative model")

    def load_video(self):
        """Load video file for analysis with smooth loading progress"""
        file_path = filedialog.askopenfilename(
            title="Select Video for Analysis",
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
            self.update_status(f"📹 Loading video: {os.path.basename(file_path)}...")

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
        self.frame_features.clear()
        self.frame_index = 0

        # Clear queues
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except:
                break

        self.update_status(
            f"✅ Video loaded successfully: {os.path.basename(file_path)} ({self.total_video_frames:,} frames, {self.video_fps:.1f} fps)")

        # Show video info in status
        duration_seconds = self.total_video_frames / self.video_fps if self.video_fps > 0 else 0
        duration_minutes = duration_seconds / 60

        messagebox.showinfo(
            "Video Loaded Successfully",
            f"✅ Video loaded and ready for analysis!\n\n"
            f"📊 Video Information:\n"
            f"• Total Frames: {self.total_video_frames:,}\n"
            f"• Frame Rate: {self.video_fps:.1f} fps\n"
            f"• Duration: {duration_minutes:.1f} minutes\n"
            f"• File: {os.path.basename(file_path)}\n\n"
            f"🎯 You can now click 'START ANALYSIS' to begin!"
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
            messagebox.showwarning("Missing Components", "Please load both model and video first.")
            return

        self.is_analyzing = True
        self.analyze_btn.config(text="⏹ STOP ANALYSIS", bg=self.colors['fake'])
        self.update_status("🔍 Analysis in progress...")

        # Start analysis thread
        self.analysis_thread = threading.Thread(target=self.analyze_video, daemon=True)
        self.analysis_thread.start()

        # Start display thread for smooth video playback
        self.display_thread = threading.Thread(target=self.display_video, daemon=True)
        self.display_thread.start()

    def stop_analysis(self):
        """Stop the video analysis"""
        self.is_analyzing = False
        self.analyze_btn.config(text="🔍 START ANALYSIS", bg=self.colors['real'])
        self.update_status("⏸ Analysis stopped")
        
        # Clean up resources
        gc.collect()

    def analyze_video(self):
        """Main video analysis loop with improved performance"""
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

                # Make prediction when we have enough frames
                if len(features_buffer) >= self.chunk_size:
                    # Make prediction with enhanced safety
                    try:
                        # Create a copy of the data to avoid memory issues
                        chunk = np.array(features_buffer[-self.chunk_size:], copy=True)
                        
                        # Reshape with explicit dimensions
                        input_data = chunk.reshape(1, self.chunk_size, -1).astype(np.float32)
                        
                        # Use a timeout mechanism for prediction
                        def make_prediction():
                            return self.model.predict(input_data, verbose=0)[0][0]
                        
                        # Run prediction in a separate thread with timeout
                        prediction_thread = threading.Thread(target=lambda: make_prediction())
                        prediction_thread.daemon = True
                        prediction_thread.start()
                        prediction_thread.join(timeout=2.0)  # 2 second timeout
                        
                        if prediction_thread.is_alive():
                            # If prediction takes too long, skip this frame
                            self.update_status("⚠️ Prediction timeout, skipping frame")
                            continue
                        
                        # Get the prediction result
                        prediction = make_prediction()
                        
                    except Exception as pred_error:
                        self.update_status(f"⚠️ Prediction error: {str(pred_error)}")
                        # Force garbage collection to free memory
                        gc.collect()
                        continue

                    self.prediction_history.append(prediction)
                    self.confidence_history.append(abs(prediction - 0.5) * 2)

                    # Update displays (throttled)
                    if frame_count % 3 == 0:  # Update every 3rd frame for smoothness
                        self.root.after(0, self.update_prediction_display, prediction)
                        self.root.after(0, self.update_charts)

                # Update progress
                frame_count += 1
                if frame_count % 5 == 0:  # Update progress every 5th frame
                    progress = (frame_count / total_frames) * 100
                    self.root.after(0, self.update_progress, progress, frame_count, total_frames)

                # Control analysis speed (smoother frame processing)
                time.sleep(1 / min(90, fps * 2.5))  # Increased FPS for smoother analysis

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Analysis Error", f"Error during analysis: {str(e)}"))
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
        """Add analysis overlay to frame (landmarks, face detection)"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_detector(gray)

            if len(faces) > 0:
                largest_face = max(faces, key=lambda rect: rect.width() * rect.height())

                # Draw face rectangle with modern styling
                x, y, w, h = largest_face.left(), largest_face.top(), largest_face.width(), largest_face.height()
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 136), 3)

                # Add face detection label
                cv2.putText(frame, 'FACE DETECTED', (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 136), 2)

                # Draw landmarks if predictor is available
                if self.landmark_predictor:
                    landmarks = self.landmark_predictor(gray, largest_face)

                    # Draw landmarks with different colors for different facial parts
                    for i in range(self.num_landmarks):
                        x_pt = landmarks.part(i).x
                        y_pt = landmarks.part(i).y

                        # Color coding for different facial features
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

            # Add analysis info overlay
            cv2.rectangle(frame, (10, 10), (300, 80), (0, 0, 0), -1)
            cv2.rectangle(frame, (10, 10), (300, 80), (0, 255, 136), 2)
            cv2.putText(frame, 'DEEPFAKE ANALYSIS', (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 136), 2)
            cv2.putText(frame, f'Faces: {len(faces)}', (20, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f'Landmarks: {self.num_landmarks if self.landmark_predictor else 0}', (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        except Exception as e:
            pass  # Return frame as-is if processing fails

        return frame

    def update_dual_video_display(self, original_frame, processed_frame):
        """Update both video displays with larger size"""
        try:
            # Larger display size for better visibility
            display_size = (480, 360)  # Increased from (320, 240)

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

        self.prediction_label.config(text=f"{icon} PREDICTION: {pred_text}", fg=color)
        self.confidence_label.config(text=f"Confidence: {confidence:.1f}%")

    def update_charts(self):
        """Update analysis charts with enhanced styling"""
        if not self.prediction_history:
            return

        # Clear axes
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        # Confidence over time with gradient
        confidence_data = list(self.confidence_history)
        if confidence_data:
            self.ax1.plot(confidence_data, color=self.colors['accent'], linewidth=2.5, alpha=0.8)
            self.ax1.fill_between(range(len(confidence_data)), confidence_data, alpha=0.3, color=self.colors['accent'])

        self.ax1.set_title('Confidence Score Over Time', color=self.colors['text'], fontsize=11, fontweight='bold',
                           pad=10)
        self.ax1.set_facecolor(self.colors['bg'])
        self.ax1.tick_params(colors=self.colors['text_dim'], labelsize=8)
        self.ax1.set_ylim(0, 1)
        self.ax1.grid(True, alpha=0.2, color=self.colors['text_dim'])

        # Simple and Clean Timeline Visualization - Much easier to understand
        predictions = list(self.prediction_history)
        if len(predictions) > 5:
            # Show recent timeline (last 100 predictions for clarity)
            timeline_length = min(len(predictions), 100)
            recent_predictions = predictions[-timeline_length:]
            recent_confidences = list(self.confidence_history)[-timeline_length:]

            # Create simple line plot with filled areas
            x_values = range(len(recent_predictions))

            # Clear the axis
            self.ax2.clear()

            # Plot the prediction line
            self.ax2.plot(x_values, recent_predictions, color=self.colors['accent'],
                          linewidth=3, alpha=0.8, label='Predictions')

            # Fill areas based on prediction
            # Green area for REAL predictions (above 0.5)
            real_mask = np.array(recent_predictions) > 0.5
            if np.any(real_mask):
                self.ax2.fill_between(x_values, recent_predictions, 0.5,
                                      where=real_mask, color=self.colors['real'],
                                      alpha=0.3, label='REAL Regions')

            # Red area for FAKE predictions (below 0.5)
            fake_mask = np.array(recent_predictions) < 0.5
            if np.any(fake_mask):
                self.ax2.fill_between(x_values, recent_predictions, 0.5,
                                      where=fake_mask, color=self.colors['fake'],
                                      alpha=0.3, label='FAKE Regions')

            # Add threshold line
            self.ax2.axhline(y=0.5, color=self.colors['text_dim'],
                             linestyle='--', alpha=0.7, linewidth=2,
                             label='Decision Threshold')

            # Add confidence indicators as scatter points on high confidence areas
            high_conf_indices = [i for i, conf in enumerate(recent_confidences) if conf > 0.8]
            if high_conf_indices:
                high_conf_predictions = [recent_predictions[i] for i in high_conf_indices]
                self.ax2.scatter(high_conf_indices, high_conf_predictions,
                                 color='white', s=40, marker='o',
                                 edgecolors='black', linewidth=1,
                                 label='High Confidence', zorder=5)

            # Customize the plot
            self.ax2.set_ylim(0, 1)
            self.ax2.set_xlim(0, len(recent_predictions))
            self.ax2.set_xlabel('Recent Frames →', color=self.colors['text_dim'], fontsize=10)
            self.ax2.set_ylabel('Prediction Score', color=self.colors['text_dim'], fontsize=10)

            # Add clear labels
            self.ax2.text(0.02, 0.95, 'REAL', transform=self.ax2.transAxes,
                          fontsize=12, fontweight='bold', color=self.colors['real'],
                          bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors['real'], alpha=0.2))

            self.ax2.text(0.02, 0.05, 'FAKE', transform=self.ax2.transAxes,
                          fontsize=12, fontweight='bold', color=self.colors['fake'],
                          bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors['fake'], alpha=0.2))

            # Add legend
            legend = self.ax2.legend(loc='upper right', fontsize=8,
                                     facecolor=self.colors['bg'], edgecolor=self.colors['text_dim'])
            # Set legend text color to white
            for text in legend.get_texts():
                text.set_color('white')

            # Add grid for better readability
            self.ax2.grid(True, alpha=0.3, color=self.colors['text_dim'])

        else:
            # Not enough data yet
            self.ax2.text(0.5, 0.5, 'Analyzing...\nNeed more frames for timeline',
                          transform=self.ax2.transAxes, ha='center', va='center',
                          fontsize=14, color=self.colors['text_dim'])

        self.ax2.set_title('📈 Simple Timeline (Green=Real, Red=Fake)', color=self.colors['text'],
                           fontsize=12, fontweight='bold', pad=15)
        self.ax2.set_facecolor(self.colors['bg'])
        self.ax2.tick_params(colors=self.colors['text_dim'], labelsize=8)

        # HORIZONTAL BAR CHART - Real vs Fake Percentages
        if self.prediction_history:
            # Calculate percentages
            total_frames = len(predictions)
            real_frames = sum(1 for p in predictions if p > 0.5)
            fake_frames = total_frames - real_frames

            real_percentage = (real_frames / total_frames) * 100
            fake_percentage = (fake_frames / total_frames) * 100

            # Clear the axis
            self.ax3.clear()

            # Create horizontal bar chart
            categories = ['REAL', 'FAKE']
            percentages = [real_percentage, fake_percentage]
            colors = [self.colors['real'], self.colors['fake']]

            # Create the bars
            bars = self.ax3.barh(categories, percentages, color=colors, alpha=0.8, height=0.6)

            # Add percentage labels on the bars with category names
            for i, (bar, percentage, category) in enumerate(zip(bars, percentages, categories)):
                width = bar.get_width()
                # Position text in the middle of the bar if percentage > 10%, otherwise outside
                if percentage > 10:
                    x_pos = width / 2
                    ha = 'center'
                    color = 'white'
                    fontweight = 'bold'
                    text = f'{category}: {percentage:.1f}%'
                else:
                    x_pos = width + 1
                    ha = 'left'
                    color = self.colors['text']
                    fontweight = 'normal'
                    text = f'{category}: {percentage:.1f}%'

                self.ax3.text(x_pos, bar.get_y() + bar.get_height() / 2,
                              text,
                              ha=ha, va='center',
                              color=color, fontsize=12, fontweight=fontweight)

            # Add frame counts as additional labels
            for i, (bar, category) in enumerate(zip(bars, categories)):
                frame_count = real_frames if category == 'REAL' else fake_frames
                self.ax3.text(-2, bar.get_y() + bar.get_height() / 2,
                              f'{frame_count:,} frames',
                              ha='right', va='center',
                              color=self.colors['text_dim'], fontsize=10)

            # Customize the chart
            self.ax3.set_xlim(0, 100)
            self.ax3.set_xlabel('Percentage (%)', color=self.colors['text_dim'], fontsize=10)
            self.ax3.tick_params(colors=self.colors['text_dim'], labelsize=10)

            # Remove y-axis ticks and labels
            self.ax3.set_yticks([])
            self.ax3.tick_params(left=False)

            # Add grid for better readability
            self.ax3.grid(True, alpha=0.3, color=self.colors['text_dim'], axis='x')

            # Add a subtle background
            self.ax3.set_facecolor(self.colors['bg'])

            # Add total frames text
            self.ax3.text(50, -0.8, f'Total Analyzed: {total_frames:,} frames',
                          ha='center', va='center',
                          color=self.colors['text_dim'], fontsize=9,
                          transform=self.ax3.transData)

        else:
            # No data yet - show empty chart
            self.ax3.clear()
            self.ax3.text(0.5, 0.5, 'Bar Chart Ready\nAwaiting Analysis...',
                          transform=self.ax3.transAxes, ha='center', va='center',
                          fontsize=12, color=self.colors['text_dim'])
            self.ax3.set_xlim(0, 100)
            self.ax3.set_xlabel('Percentage (%)', color=self.colors['text_dim'], fontsize=10)
            self.ax3.set_ylabel('Classification', color=self.colors['text_dim'], fontsize=10)
            self.ax3.tick_params(colors=self.colors['text_dim'], labelsize=10)
            self.ax3.set_facecolor(self.colors['bg'])



        self.ax3.set_title('📊 Frame Classification Percentage', color=self.colors['text'],
                           fontsize=12, fontweight='bold', pad=15)

        plt.tight_layout(pad=1.5)
        self.canvas.draw()

        # Update statistics
        self.update_statistics()

    def update_statistics(self):
        """Update statistics display with enhanced formatting including chunk analysis"""
        if not self.prediction_history:
            return

        predictions = list(self.prediction_history)
        confidences = list(self.confidence_history)

        real_count = sum(1 for p in predictions if p > 0.5)
        fake_count = len(predictions) - real_count
        avg_confidence = np.mean(confidences) if confidences else 0
        max_confidence = np.max(confidences) if confidences else 0
        min_confidence = np.min(confidences) if confidences else 0

        # Calculate chunk statistics
        num_chunks = len(predictions) // self.chunk_size if len(predictions) >= self.chunk_size else 0
        real_chunks = 0
        fake_chunks = 0

        if num_chunks > 0:
            for i in range(num_chunks):
                chunk_start = i * self.chunk_size
                chunk_end = chunk_start + self.chunk_size
                chunk_predictions = predictions[chunk_start:chunk_end]

                chunk_real_count = sum(1 for p in chunk_predictions if p > 0.5)
                if chunk_real_count > self.chunk_size // 2:
                    real_chunks += 1
                else:
                    fake_chunks += 1

        # Calculate trend
        if len(predictions) >= 10:
            recent_trend = np.mean(predictions[-10:]) - np.mean(predictions[-20:-10]) if len(predictions) >= 20 else 0
            trend_text = "📈 Trending REAL" if recent_trend > 0.1 else "📉 Trending FAKE" if recent_trend < -0.1 else "➡️ Stable"
        else:
            trend_text = "➡️ Analyzing..."

        stats_text = f"""
╔══════════════════════════════════════════════════════════════╗
║                        ANALYSIS SUMMARY                      ║
╠══════════════════════════════════════════════════════════════╣
║ FRAME ANALYSIS                                               ║
║ Total Frames Analyzed: {len(predictions):>6}                             ║
║ Real Predictions:      {real_count:>6} ({real_count / len(predictions) * 100:>5.1f}%)                ║
║ Fake Predictions:      {fake_count:>6} ({fake_count / len(predictions) * 100:>5.1f}%)                ║
║                                                              ║
║ CHUNK ANALYSIS ({self.chunk_size} frames per chunk)                           ║
║ Total Chunks:          {num_chunks:>6}                             ║
║ Real Chunks:           {real_chunks:>6} ({real_chunks / max(1, num_chunks) * 100:>5.1f}%)                ║
║ Fake Chunks:           {fake_chunks:>6} ({fake_chunks / max(1, num_chunks) * 100:>5.1f}%)                ║
║                                                              ║
║ CONFIDENCE METRICS                                           ║
║ Average Confidence:    {avg_confidence * 100:>5.1f}%                          ║
║ Peak Confidence:       {max_confidence * 100:>5.1f}%                          ║
║ Lowest Confidence:     {min_confidence * 100:>5.1f}%                          ║
║                                                              ║
║ CURRENT STATUS                                               ║
║ Trend:                 {trend_text:<20}                    ║
║ Latest Prediction:     {'REAL' if predictions[-1] > 0.5 else 'FAKE':<6} ({confidences[-1] * 100:>5.1f}%)              ║
╚══════════════════════════════════════════════════════════════╝
        """

        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, stats_text)

    def update_progress(self, progress, current_frame, total_frames):
        """Update progress bar and frame counter"""
        self.progress_var.set(progress)
        self.frame_label.config(text=f"Frame: {current_frame:,}/{total_frames:,}")

    def analysis_complete(self):
        """Handle analysis completion with enhanced results"""
        self.is_analyzing = False
        self.analyze_btn.config(text="🔍 START ANALYSIS", bg=self.colors['real'])
        self.update_status("✅ Analysis completed successfully")
        
        # Clean up resources
        gc.collect()

        # Show enhanced final results with custom dialog
        if self.prediction_history:
            self.show_beautiful_results_dialog()

    def show_beautiful_results_dialog(self):
        """Show a beautiful, informative results dialog"""
        predictions = list(self.prediction_history)
        confidences = list(self.confidence_history)

        # Calculate accurate statistics
        total_frames = len(predictions)
        real_frames = sum(1 for p in predictions if p > 0.5)
        fake_frames = total_frames - real_frames
        uncertain_frames = sum(1 for p in predictions if 0.3 <= p <= 0.7)

        real_pct = (real_frames / total_frames) * 100
        fake_pct = (fake_frames / total_frames) * 100
        uncertain_pct = (uncertain_frames / total_frames) * 100

        # Overall verdict based on majority
        if real_pct > fake_pct:
            overall_verdict = "AUTHENTIC"
            verdict_confidence = real_pct
            verdict_icon = "✅"
            verdict_color = self.colors['real']
        else:
            overall_verdict = "DEEPFAKE DETECTED"
            verdict_confidence = fake_pct
            verdict_icon = "⚠️"
            verdict_color = self.colors['fake']

        # Calculate confidence metrics
        avg_confidence = np.mean(confidences) * 100 if confidences else 0
        max_confidence = np.max(confidences) * 100 if confidences else 0
        min_confidence = np.min(confidences) * 100 if confidences else 0

        # Determine reliability
        if avg_confidence > 85:
            reliability = "VERY HIGH"
            reliability_icon = "🟢"
        elif avg_confidence > 70:
            reliability = "HIGH"
            reliability_icon = "🟡"
        elif avg_confidence > 50:
            reliability = "MODERATE"
            reliability_icon = "🟠"
        else:
            reliability = "LOW"
            reliability_icon = "🔴"

        # Calculate video information
        video_name = os.path.basename(self.current_video) if self.current_video else "Unknown"
        video_duration = (self.total_video_frames / self.video_fps) if self.video_fps > 0 else 0
        duration_minutes = int(video_duration // 60)
        duration_seconds = int(video_duration % 60)

        # Calculate suspicious segments
        suspicious_segments = []
        window_size = 20  # Look for consecutive fake predictions

        for i in range(len(predictions) - window_size):
            window = predictions[i:i + window_size]
            fake_ratio = sum(1 for p in window if p < 0.5) / window_size

            if fake_ratio > 0.7:  # 70% fake predictions in window
                start_time = (i / len(predictions)) * video_duration if video_duration > 0 else 0
                suspicious_segments.append(f"{int(start_time // 60):02d}:{int(start_time % 60):02d}")

        # Remove duplicates and limit to top 5
        suspicious_segments = list(dict.fromkeys(suspicious_segments))[:5]

        # Create custom dialog
        result_dialog = tk.Toplevel(self.root)
        result_dialog.title("🔍 Deepfake Analysis Results")
        result_dialog.geometry("700x800")
        result_dialog.configure(bg=self.colors['bg'])
        result_dialog.resizable(False, False)

        # Center the dialog
        result_dialog.transient(self.root)
        result_dialog.grab_set()

        # Main container
        main_frame = tk.Frame(result_dialog, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors['card'], relief=tk.FLAT, bd=0)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        header_inner = tk.Frame(header_frame, bg=self.colors['card'])
        header_inner.pack(pady=20)

        # Title with icon
        title_label = tk.Label(
            header_inner,
            text=f"{verdict_icon} ANALYSIS COMPLETE",
            font=('Segoe UI', 24, 'bold'),
            fg=verdict_color,
            bg=self.colors['card']
        )
        title_label.pack()

        subtitle_label = tk.Label(
            header_inner,
            text=f"Deep Learning Video Forensics Report",
            font=('Segoe UI', 12),
            fg=self.colors['text_dim'],
            bg=self.colors['card']
        )
        subtitle_label.pack(pady=(5, 0))

        # Main verdict section
        verdict_frame = tk.Frame(main_frame, bg=self.colors['card_light'], relief=tk.FLAT, bd=0)
        verdict_frame.pack(fill=tk.X, pady=(0, 15))

        verdict_inner = tk.Frame(verdict_frame, bg=self.colors['card_light'])
        verdict_inner.pack(pady=20)

        verdict_label = tk.Label(
            verdict_inner,
            text=f"VERDICT: {overall_verdict}",
            font=('Segoe UI', 20, 'bold'),
            fg=verdict_color,
            bg=self.colors['card_light']
        )
        verdict_label.pack()

        confidence_label = tk.Label(
            verdict_inner,
            text=f"Confidence: {verdict_confidence:.1f}%",
            font=('Segoe UI', 14),
            fg=self.colors['text'],
            bg=self.colors['card_light']
        )
        confidence_label.pack(pady=(5, 0))

        # Video information section
        video_info_frame = tk.Frame(main_frame, bg=self.colors['card'], relief=tk.FLAT, bd=0)
        video_info_frame.pack(fill=tk.X, pady=(0, 15))

        video_info_inner = tk.Frame(video_info_frame, bg=self.colors['card'])
        video_info_inner.pack(pady=15, padx=20)

        tk.Label(
            video_info_inner,
            text="📹 VIDEO INFORMATION",
            font=('Segoe UI', 14, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['card']
        ).pack(anchor=tk.W)

        video_details = tk.Text(
            video_info_inner,
            height=4,
            bg=self.colors['bg'],
            fg=self.colors['text'],
            font=('Consolas', 10),
            relief=tk.FLAT,
            bd=0,
            wrap=tk.WORD
        )
        video_details.pack(fill=tk.X, pady=(10, 0))

        video_info_text = f"""File: {video_name}
Duration: {duration_minutes:02d}:{duration_seconds:02d} ({video_duration:.1f} seconds)
Total Frames: {self.total_video_frames:,} | Frame Rate: {self.video_fps:.1f} fps
Frames Analyzed: {total_frames:,} | Analysis Coverage: {(total_frames / max(1, self.total_video_frames)) * 100:.1f}%"""

        video_details.insert(tk.END, video_info_text)
        video_details.config(state=tk.DISABLED)

        # Detailed analysis section
        analysis_frame = tk.Frame(main_frame, bg=self.colors['card'], relief=tk.FLAT, bd=0)
        analysis_frame.pack(fill=tk.X, pady=(0, 15))

        analysis_inner = tk.Frame(analysis_frame, bg=self.colors['card'])
        analysis_inner.pack(pady=15, padx=20)

        tk.Label(
            analysis_inner,
            text="📊 DETAILED ANALYSIS",
            font=('Segoe UI', 14, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['card']
        ).pack(anchor=tk.W)

        analysis_details = tk.Text(
            analysis_inner,
            height=8,
            bg=self.colors['bg'],
            fg=self.colors['text'],
            font=('Consolas', 10),
            relief=tk.FLAT,
            bd=0,
            wrap=tk.WORD
        )
        analysis_details.pack(fill=tk.X, pady=(10, 0))

        analysis_text = f"""FRAME CLASSIFICATION:
├─ Authentic Frames: {real_frames:,} ({real_pct:.1f}%)
├─ Manipulated Frames: {fake_frames:,} ({fake_pct:.1f}%)
└─ Uncertain Frames: {uncertain_frames:,} ({uncertain_pct:.1f}%)

CONFIDENCE METRICS:
├─ Average Confidence: {avg_confidence:.1f}%
├─ Peak Confidence: {max_confidence:.1f}%
└─ Minimum Confidence: {min_confidence:.1f}%

TEMPORAL ANALYSIS:
├─ Suspicious Time Segments: {len(suspicious_segments)} detected
└─ Pattern Consistency: {'High' if len(suspicious_segments) < 3 else 'Variable'}"""

        analysis_details.insert(tk.END, analysis_text)
        analysis_details.config(state=tk.DISABLED)

        # Suspicious segments section (if any)
        if suspicious_segments:
            segments_frame = tk.Frame(main_frame, bg=self.colors['card'], relief=tk.FLAT, bd=0)
            segments_frame.pack(fill=tk.X, pady=(0, 15))

            segments_inner = tk.Frame(segments_frame, bg=self.colors['card'])
            segments_inner.pack(pady=15, padx=20)

            tk.Label(
                segments_inner,
                text="⚠️ SUSPICIOUS TIME SEGMENTS",
                font=('Segoe UI', 14, 'bold'),
                fg=self.colors['warning'],
                bg=self.colors['card']
            ).pack(anchor=tk.W)

            segments_text = tk.Label(
                segments_inner,
                text=f"Review these time periods: {', '.join(suspicious_segments)}",
                font=('Segoe UI', 11),
                fg=self.colors['text'],
                bg=self.colors['card'],
                wraplength=600,
                justify=tk.LEFT
            )
            segments_text.pack(anchor=tk.W, pady=(10, 0))

        # Action buttons
        button_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, pady=(20, 0))

        # Export button
        export_btn = self.create_modern_button(
            button_frame, "📄 Export Report",
            lambda: self.export_analysis_report(predictions, confidences, video_name, video_duration),
            self.colors['accent']
        )
        export_btn.pack(side=tk.LEFT)

        # Close button
        close_btn = self.create_modern_button(
            button_frame, "✅ Close", result_dialog.destroy, self.colors['success']
        )
        close_btn.pack(side=tk.RIGHT)

        # Center the dialog on screen
        result_dialog.update_idletasks()
        x = (result_dialog.winfo_screenwidth() - result_dialog.winfo_width()) // 2
        y = (result_dialog.winfo_screenheight() - result_dialog.winfo_height()) // 2
        result_dialog.geometry(f"+{x}+{y}")

    def export_analysis_report(self, predictions, confidences, video_name, video_duration):
        """Export detailed analysis report to text file"""
        try:
            from datetime import datetime

            # Generate report filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"deepfake_analysis_{timestamp}.txt"

            # Calculate all statistics
            total_frames = len(predictions)
            real_frames = sum(1 for p in predictions if p > 0.5)
            fake_frames = total_frames - real_frames
            real_pct = (real_frames / total_frames) * 100
            fake_pct = (fake_frames / total_frames) * 100
            avg_confidence = np.mean(confidences) * 100 if confidences else 0

            verdict = "AUTHENTIC" if real_pct > fake_pct else "DEEPFAKE DETECTED"

            # Create detailed report
            report_content = f"""
DEEPFAKE DETECTION ANALYSIS REPORT
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{'=' * 60}

VIDEO INFORMATION:
- File: {video_name}
- Duration: {video_duration:.2f} seconds
- Total Frames: {self.total_video_frames:,}
- Frames Analyzed: {total_frames:,}
- Frame Rate: {self.video_fps:.1f} fps

ANALYSIS RESULTS:
- Final Verdict: {verdict}
- Confidence: {max(real_pct, fake_pct):.1f}%
- Authentic Frames: {real_frames:,} ({real_pct:.2f}%)
- Manipulated Frames: {fake_frames:,} ({fake_pct:.2f}%)
- Average Confidence: {avg_confidence:.2f}%

TECHNICAL DETAILS:
- Model: Enhanced LSTM Deepfake Detector
- Analysis Method: Facial Landmark + Color Features
- Chunk Size: {self.chunk_size} frames
- Feature Dimensions: {self.feature_dim}
- Processing Quality: High

FRAME-BY-FRAME PREDICTIONS:
{chr(10).join([f"Frame {i + 1}: {'REAL' if p > 0.5 else 'FAKE'} (Confidence: {abs(p - 0.5) * 200:.1f}%)" for i, p in enumerate(predictions[:50])])}
{'...(showing first 50 frames)' if len(predictions) > 50 else ''}

END OF REPORT
"""

            # Save report
            with open(report_filename, 'w') as f:
                f.write(report_content)

            messagebox.showinfo(
                "Report Exported",
                f"Analysis report saved successfully!\n\nFile: {report_filename}\n\nThe report contains detailed frame-by-frame analysis and can be used for forensic documentation."
            )

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report:\n{str(e)}")

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
    """Main function to run the enhanced GUI application"""
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
            if messagebox.askokcancel("Quit", "Operation in progress. Do you want to quit?"):
                app.is_analyzing = False
                app.is_loading_video = False
                root.quit()
        else:
            root.quit()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()