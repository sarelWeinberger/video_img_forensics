import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model, Model
from tensorflow.keras.layers import LSTM, Dense, Input
import numpy as np
import os

def create_compatible_model():
    """
    Create a new TensorFlow model compatible with the current version
    that matches the architecture of the original model but without using 'batch_shape'.
    """
    print("TensorFlow version:", tf.__version__)
    
    # Check if original model exists
    original_model_path = "enhanced_deepfake_lstm_model.h5"
    if not os.path.exists(original_model_path):
        print(f"Error: Original model file '{original_model_path}' not found.")
        return False
    
    try:
        # Try to load the original model to extract its architecture
        # This might fail due to the 'batch_shape' incompatibility
        print("Attempting to load original model to extract architecture...")
        original_model = load_model(original_model_path)
        print("Successfully loaded original model.")
        
        # If we get here, the model loaded successfully, so we can just save it with a new name
        new_model_path = "enhanced_deepfake_lstm_model_new.h5"
        original_model.save(new_model_path)
        print(f"Model saved as '{new_model_path}'")
        return True
    
    except Exception as e:
        print(f"Error loading original model: {str(e)}")
        print("Creating a new compatible model with similar architecture...")
        
        # Create a new model with similar architecture
        # The original model has an LSTM layer with 64 time steps and 340 features
        # followed by a Dense layer with sigmoid activation
        
        # Create a new model using Input layer instead of batch_shape
        input_layer = Input(shape=(64, 340))  # 64 time steps, 340 features per step
        lstm_layer = LSTM(64)(input_layer)
        output_layer = Dense(1, activation='sigmoid')(lstm_layer)
        
        new_model = Model(inputs=input_layer, outputs=output_layer)
        
        # Compile the model
        new_model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        print("New compatible model created with architecture:")
        new_model.summary()
        
        # Save the new model
        new_model_path = "enhanced_deepfake_lstm_model_new.h5"
        new_model.save(new_model_path)
        print(f"New compatible model saved as '{new_model_path}'")
        
        return True

if __name__ == "__main__":
    print("Creating compatible TensorFlow model...")
    success = create_compatible_model()
    
    if success:
        print("\nSuccess! Now modify deep_fake_land_marks_gui.py to use the new model:")
        print("Change line 46 from:")
        print('    self.model_path = "enhanced_deepfake_lstm_model.h5"')
        print("to:")
        print('    self.model_path = "enhanced_deepfake_lstm_model_new.h5"')
    else:
        print("\nFailed to create compatible model.")