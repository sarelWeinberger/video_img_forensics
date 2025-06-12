import tensorflow as tf
from tensorflow.keras.models import load_model
import numpy as np
import os

def test_model():
    """
    Test if the model can be loaded and make predictions
    """
    print("TensorFlow version:", tf.__version__)
    
    # Check if model exists
    model_path = "enhanced_deepfake_lstm_model_new.h5"
    if not os.path.exists(model_path):
        print(f"Error: Model file '{model_path}' not found.")
        return False
    
    try:
        # Load the model
        print(f"Loading model from '{model_path}'...")
        model = load_model(model_path)
        print("Model loaded successfully!")
        
        # Print model summary
        print("Model summary:")
        model.summary()
        
        # Create random input data matching the expected shape
        # The model expects input shape (batch_size, 64, 340)
        print("Creating random test data...")
        test_data = np.random.random((1, 64, 340))
        
        # Make a prediction
        print("Making prediction...")
        prediction = model.predict(test_data, verbose=1)
        
        print(f"Prediction result: {prediction}")
        print("Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error testing model: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing model functionality...")
    success = test_model()
    
    if success:
        print("\nModel works correctly for predictions!")
    else:
        print("\nFailed to test model.")