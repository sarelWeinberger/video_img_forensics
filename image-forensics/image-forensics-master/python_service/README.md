# Manipulated Score Python Service

This service provides a REST API for the Manipulated Score model, which detects image manipulations using deep learning.

## Requirements

- Python 3.7 or higher
- Dependencies listed in `requirements.txt`
- GPU support recommended for optimal performance

## Installation

1. Install the correct version of Werkzeug to avoid dependency conflicts:
   ```bash
   pip install werkzeug==2.0.1
   ```

   This is critical because newer versions of Werkzeug are incompatible with Flask 2.0.1.

2. Install other dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. If you want to use a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

   Note: If you encounter errors creating the virtual environment, you may need to install the python3-venv package:
   ```bash
   sudo apt install python3.8-venv
   ```

## Usage

### Starting the Service

#### Method 1: Using the start_service.sh Script

1. Make the script executable:
   ```bash
   chmod +x start_service.sh
   ```

2. Run the script:
   ```bash
   ./start_service.sh
   ```

   This will start the service on the default port (5000).

3. To specify a custom port:
   ```bash
   ./start_service.sh 8000
   ```

4. To use a virtual environment:
   ```bash
   ./start_service.sh 5000 venv
   ```

The script will:
- Install the correct version of Werkzeug (2.0.1)
- Install other dependencies
- Check if the port is already in use
- Start the Python service

#### Method 2: Starting Manually

1. Make sure no other services are using port 5000:
   ```bash
   netstat -tuln | grep 5000
   ```

2. Install the correct version of Werkzeug:
   ```bash
   pip install werkzeug==2.0.1
   ```

3. Install other dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the service on the default port (5000):
   ```bash
   python3 manipulated_score_service.py
   ```

   Or specify a custom port:
   ```bash
   python3 manipulated_score_service.py 8000
   ```

5. Verify the service is running:
   ```bash
   curl -v http://localhost:5000/predict
   ```

   You should get a 404 response, which is normal since we're not sending any data.

### API Endpoints

#### Predict Manipulation

**Endpoint:** `POST /predict`

**Request Options:**

1. Image as base64 string:
   ```json
   {
     "image_base64": "base64_encoded_image_data"
   }
   ```

2. Image file upload:
   ```
   curl -X POST -F "image=@/path/to/image.jpg" http://localhost:5000/predict
   ```

3. Image path on server:
   ```json
   {
     "image_path": "/path/to/image.jpg"
   }
   ```

4. Save heatmap to file (optional):
   ```json
   {
     "image_path": "/path/to/image.jpg",
     "output_path": "/path/to/save/heatmap.png"
   }
   ```

**Response:**
```json
{
  "manipulation_score": 15.7,
  "heatmap_base64": "base64_encoded_heatmap_image",
  "min_value": 0.0,
  "max_value": 1.0,
  "heatmap_path": "/path/to/save/heatmap.png"  // Only if output_path was provided
}
```

## Integration with Java Service

The Java service communicates with this Python service via HTTP requests. The Java service sends the image path to the Python service, which processes the image and returns the manipulation score and heatmap.

**Important**: The Python service must be started before the Java service for the Manipulated Score Analysis to work properly.

## Troubleshooting

### Common Issues

1. **Dependency Conflicts**:
   ```
   ImportError: cannot import name 'url_quote' from 'werkzeug.urls'
   ```
   
   **Solution**: Install the correct version of Werkzeug:
   ```bash
   pip install werkzeug==2.0.1
   ```

2. **Port Already in Use**:
   ```
   OSError: [Errno 98] Address already in use
   ```
   
   **Solution**: Find and stop the process using port 5000, or use a different port:
   ```bash
   netstat -tuln | grep 5000
   kill <PID>
   ```
   
   Or start the service on a different port:
   ```bash
   python3 manipulated_score_service.py 5001
   ```

3. **Virtual Environment Issues**:
   ```
   The virtual environment was not created successfully because ensurepip is not available.
   ```
   
   **Solution**: Install the python3-venv package:
   ```bash
   sudo apt install python3.8-venv
   ```

4. **Flask `before_first_request` Error**:
   ```
   AttributeError: 'Flask' object has no attribute 'before_first_request'. Did you mean: '_got_first_request'?
   ```
   
   **Solution**: This error occurs because the `before_first_request` decorator has been removed in newer versions of Flask. The fix is to remove the decorator and keep the direct function call in the main block:
   ```python
   # Remove this line
   @app.before_first_request
   def initialize_model():
       # function implementation...
   
   # Keep the direct call in the main block
   if __name__ == '__main__':
       initialize_model()
       app.run(host='0.0.0.0', port=port)
   ```
   
   This change has been implemented in the current version of the service.

## Notes

- This implementation uses a mock model for demonstration purposes. In a production environment, you would replace the `MockManipulatedScoreModel` class with the actual model from the GitHub repository.
- For production use, consider adding authentication and HTTPS to secure the API.
- The service automatically creates output directories if they don't exist.
- Always start this Python service before starting the Java service.