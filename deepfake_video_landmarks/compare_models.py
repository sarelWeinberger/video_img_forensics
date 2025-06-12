import tensorflow as tf
from tensorflow.keras.models import load_model
import numpy as np
import os
import h5py
import json

def compare_models():
    """
    Compare predictions from different model versions using the same input data
    """
    print("TensorFlow version:", tf.__version__)
    
    # Check if model files exist
    simple_model_path = "enhanced_deepfake_lstm_model_new.h5"
    fallback_model_path = "enhanced_deepfake_lstm_model_fallback.h5"
    
    if not os.path.exists(simple_model_path):
        print(f"Error: Simple model file '{simple_model_path}' not found.")
        return False
    
    if not os.path.exists(fallback_model_path):
        print(f"Error: Fallback model file '{fallback_model_path}' not found.")
        return False
    
    try:
        # Load the models
        print(f"Loading simple model from '{simple_model_path}'...")
        simple_model = load_model(simple_model_path)
        print("Simple model loaded successfully!")
        
        print(f"Loading fallback model from '{fallback_model_path}'...")
        fallback_model = load_model(fallback_model_path)
        print("Fallback model loaded successfully!")
        
        # Print model summaries
        print("\nSimple model summary:")
        simple_model.summary()
        
        print("\nFallback model summary:")
        fallback_model.summary()
        
        # Create test data
        print("\nCreating test data for comparison...")
        # Create 5 different random test inputs
        num_samples = 5
        test_inputs = []
        
        for i in range(num_samples):
            # Create random input data matching the expected shape (64, 340)
            test_input = np.random.random((1, 64, 340))
            test_inputs.append(test_input)
        
        # Make predictions with both models
        print("\nMaking predictions with both models...")
        
        print("\nTest case | Simple Model | Fallback Model | Difference")
        print("---------|--------------|----------------|------------")
        
        for i, test_input in enumerate(test_inputs):
            # Get predictions
            simple_pred = simple_model.predict(test_input, verbose=0)[0][0]
            fallback_pred = fallback_model.predict(test_input, verbose=0)[0][0]
            
            # Calculate difference
            diff = abs(simple_pred - fallback_pred)
            
            # Print results
            print(f"Test {i+1}   | {simple_pred:.6f}    | {fallback_pred:.6f}     | {diff:.6f}")
        
        print("\nComparison completed!")
        return True
        
    except Exception as e:
        print(f"Error comparing models: {str(e)}")
        return False

if __name__ == "__main__":
    print("Comparing model predictions...")
    success = compare_models()
    
    if success:
        print("\nModel comparison completed successfully!")
        print("\nRecommendation:")
        print("- If the differences between models are small (< 0.1), the fallback model")
        print("  should give results very close to the original model.")
        print("- If the differences are large (> 0.3), you might need to further refine")
        print("  the model architecture or consider retraining.")
    else:
        print("\nFailed to compare models.")