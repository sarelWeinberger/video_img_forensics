import os
import sys
import json
import base64
from io import BytesIO
from flask import Flask, request, jsonify
import numpy as np
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Mock implementation of the manipulated score model
# In a real implementation, this would load the actual model from the GitHub repository
class MockManipulatedScoreModel:
    def __init__(self):
        logger.info("Initializing MockManipulatedScoreModel")
        # In a real implementation, this would load the model weights and configuration
        
    def predict(self, image):
        """
        Generate a manipulation score and heatmap for the input image.
        
        Args:
            image: PIL Image object
            
        Returns:
            dict: Dictionary containing the manipulation score and heatmap
        """
        logger.info(f"Predicting manipulation score for image of size {image.size}")
        
        # Create a mock heatmap (in a real implementation, this would be the model's output)
        width, height = image.size
        
        # Check if image is too small and resize if necessary
        min_size = 100  # Minimum size for processing
        if width < min_size or height < min_size:
            logger.info(f"Image is too small, resizing to minimum dimensions")
            # Calculate new dimensions while maintaining aspect ratio
            if width < height:
                new_width = min_size
                new_height = int(height * (min_size / width))
            else:
                new_height = min_size
                new_width = int(width * (min_size / height))
            
            # Resize the image
            image = image.resize((new_width, new_height), Image.LANCZOS)
            width, height = image.size
            logger.info(f"Resized image to {width}x{height}")
        
        # Create a mock heatmap
        heatmap = np.zeros((height, width), dtype=np.float32)
        
        # Add some random "manipulated" regions for demonstration
        # In a real implementation, this would be the actual model prediction
        for _ in range(3):
            # Ensure we don't try to create regions larger than the image
            region_size = min(30, min(width, height) // 2)
            x = np.random.randint(0, max(1, width - region_size))
            y = np.random.randint(0, max(1, height - region_size))
            size = np.random.randint(max(1, region_size // 2), region_size)
            intensity = np.random.uniform(0.5, 1.0)
            
            for i in range(max(0, y), min(height, y + size)):
                for j in range(max(0, x), min(width, x + size)):
                    dist = np.sqrt((i - y - size/2)**2 + (j - x - size/2)**2)
                    if dist < size/2:
                        heatmap[i, j] = max(heatmap[i, j], intensity * (1 - dist/(size/2)))
        
        # Convert heatmap to RGB image
        heatmap_rgb = np.zeros((height, width, 3), dtype=np.uint8)
        for i in range(height):
            for j in range(width):
                if heatmap[i, j] > 0:
                    # Red channel for manipulated regions
                    heatmap_rgb[i, j, 0] = int(255 * heatmap[i, j])
                    # Green and blue channels for visualization
                    heatmap_rgb[i, j, 1] = int(70 * (1 - heatmap[i, j]))
                    heatmap_rgb[i, j, 2] = int(70 * (1 - heatmap[i, j]))
                else:
                    # Black for non-manipulated regions
                    heatmap_rgb[i, j] = [0, 0, 0]
        
        # Calculate overall manipulation score (0-100)
        manipulation_score = float(np.mean(heatmap) * 100)
        
        # Create PIL image from heatmap
        heatmap_image = Image.fromarray(heatmap_rgb)
        
        # Save heatmap to BytesIO object
        heatmap_bytes = BytesIO()
        heatmap_image.save(heatmap_bytes, format='PNG')
        heatmap_bytes.seek(0)
        
        # Encode heatmap as base64
        heatmap_base64 = base64.b64encode(heatmap_bytes.read()).decode('utf-8')
        
        return {
            'manipulation_score': manipulation_score,
            'heatmap_base64': heatmap_base64,
            'min_value': 0.0,
            'max_value': 1.0
        }

# Initialize the model
model = None

# Function to initialize model
def initialize_model():
    global model
    try:
        # In a real implementation, this would load the actual model from the GitHub repository
        model = MockManipulatedScoreModel()
        logger.info("Model initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing model: {e}")
        sys.exit(1)

@app.route('/predict', methods=['POST'])
def predict():
    """
    Endpoint for predicting manipulation score and generating heatmap.
    
    Expects:
        - image: Base64 encoded image or file upload
        
    Returns:
        JSON with manipulation score and heatmap
    """
    try:
        # Check if image is provided as base64 string
        if 'image_base64' in request.json:
            image_data = base64.b64decode(request.json['image_base64'])
            image = Image.open(BytesIO(image_data))
        # Check if image is provided as file upload
        elif 'image' in request.files:
            image_file = request.files['image']
            image = Image.open(image_file)
        # Check if image path is provided
        elif 'image_path' in request.json:
            image_path = request.json['image_path']
            image = Image.open(image_path)
        else:
            return jsonify({'error': 'No image provided'}), 400
        
        # Convert image to RGB if it's not already
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Get prediction from model
        result = model.predict(image)
        
        # Save heatmap to file if output_path is provided
        if 'output_path' in request.json:
            output_path = request.json['output_path']
            heatmap_data = base64.b64decode(result['heatmap_base64'])
            heatmap_image = Image.open(BytesIO(heatmap_data))
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            heatmap_image.save(output_path)
            result['heatmap_path'] = output_path
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Get port from command line arguments or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    
    # Initialize model before starting the server
    initialize_model()
    
    # Start Flask server
    app.run(host='0.0.0.0', port=port)