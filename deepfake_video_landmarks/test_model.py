import tensorflow as tf
import numpy as np
import os
import gc
import sys

def test_model():
    """
    Test if the model can be loaded and make predictions with enhanced error handling
    """
    print("TensorFlow version:", tf.__version__)
    print("Python version:", sys.version)
    
    # Configure TensorFlow to prevent memory issues
    physical_devices = tf.config.list_physical_devices('GPU')
    if physical_devices:
        print(f"Found {len(physical_devices)} GPU(s)")
        try:
            # Limit GPU memory growth
            for device in physical_devices:
                tf.config.experimental.set_memory_growth(device, True)
            print("GPU memory growth set to True")
        except Exception as e:
            print(f"Error configuring GPU: {str(e)}")
    else:
        print("No GPU found, using CPU")
        
    # Set TensorFlow log level to reduce noise
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    
    # Check if model exists
    model_path = "enhanced_deepfake_lstm_model_fallback.h5"
    if not os.path.exists(model_path):
        print(f"Error: Model file '{model_path}' not found.")
        return False
    
    try:
        # Import here to ensure TensorFlow is properly configured first
        from tensorflow.keras.models import load_model
        
        # Load the model with custom object scope to handle any custom layers
        print(f"Loading model from '{model_path}'...")
        with tf.keras.utils.custom_object_scope({}):
            model = load_model(model_path, compile=False)
        
        # Compile the model manually
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        print("Model loaded and compiled successfully!")
        
        # Print model summary
        print("Model summary:")
        model.summary()
        
        # Create random input data matching the expected shape
        # The model expects input shape (batch_size, 64, 340)
        print("Creating random test data...")
        test_data = np.random.random((1, 64, 340)).astype(np.float32)
        
        # Make a prediction with error handling
        print("Making prediction...")
        try:
            # Use a try-except block specifically for prediction
            prediction = model.predict(test_data, verbose=1, batch_size=1)
            print(f"Prediction result: {prediction}")
            print("Test completed successfully!")
            
            # Clean up to prevent memory leaks
            del model
            gc.collect()
            tf.keras.backend.clear_session()
            
            return True
        except Exception as e:
            print(f"Error during prediction: {str(e)}")
            return False
        
    except Exception as e:
        print(f"Error loading or testing model: {str(e)}")
        # Clean up resources
        gc.collect()
        tf.keras.backend.clear_session()
        return False

if __name__ == "__main__":
    print("Testing model functionality...")
    success = test_model()
    
    if success:
        print("\nModel works correctly for predictions!")
    else:
        print("\nFailed to test model.")
