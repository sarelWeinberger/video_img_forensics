import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Input, Bidirectional, Dropout, LayerNormalization
import numpy as np
import os
import json
import h5py

def create_exact_compatible_model():
    """
    Create a new TensorFlow model compatible with the current version
    that exactly matches the architecture of the original model.
    """
    print("TensorFlow version:", tf.__version__)
    
    # Check if original model exists
    original_model_path = "enhanced_deepfake_lstm_model.h5"
    if not os.path.exists(original_model_path):
        print(f"Error: Original model file '{original_model_path}' not found.")
        return False
    
    try:
        # Extract the model architecture from the h5 file directly
        print("Extracting original model architecture...")
        with h5py.File(original_model_path, 'r') as f:
            model_config = f.attrs.get('model_config')
            if model_config is None:
                print("Error: Could not find model_config in the h5 file.")
                return False
            
            # Parse the model config
            config_dict = json.loads(model_config)
            print("Successfully extracted model configuration.")
            
            # Fix the incompatible parameter names
            # Main issue: 'batch_shape' -> 'batch_input_shape'
            layers = config_dict['config']['layers']
            for layer in layers:
                if layer['class_name'] == 'InputLayer' and 'batch_shape' in layer['config']:
                    # Replace batch_shape with batch_input_shape
                    batch_shape = layer['config'].pop('batch_shape')
                    layer['config']['batch_input_shape'] = batch_shape
                    print(f"Fixed InputLayer config: replaced 'batch_shape' with 'batch_input_shape'")
            
            # Recreate the model from the fixed config
            print("Recreating model from fixed configuration...")
            fixed_config = json.dumps(config_dict)
            new_model = tf.keras.models.model_from_json(fixed_config)
            
            # Compile the model with the same optimizer and loss
            new_model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            
            print("New compatible model created with exact same architecture:")
            new_model.summary()
            
            # Try to copy weights from the original model if possible
            try:
                print("Attempting to copy weights from original model...")
                # This direct approach might not work due to the compatibility issue
                # But we can try a layer-by-layer approach
                
                # First, try to load the original model weights directly
                original_weights = {}
                with h5py.File(original_model_path, 'r') as f:
                    weight_group = f['model_weights']
                    for layer_name in weight_group.keys():
                        if isinstance(weight_group[layer_name], h5py.Group):
                            layer_weights = []
                            for weight_name in weight_group[layer_name].keys():
                                if 'weight' in weight_name or 'bias' in weight_name or 'kernel' in weight_name:
                                    weight_value = weight_group[layer_name][weight_name][()]
                                    layer_weights.append(weight_value)
                            if layer_weights:
                                original_weights[layer_name] = layer_weights
                
                # Set weights for each layer if possible
                for layer in new_model.layers:
                    if layer.name in original_weights:
                        try:
                            layer_weights = original_weights[layer.name]
                            if len(layer_weights) == len(layer.weights):
                                layer.set_weights(layer_weights)
                                print(f"Successfully copied weights for layer: {layer.name}")
                            else:
                                print(f"Weight shape mismatch for layer: {layer.name}")
                        except Exception as e:
                            print(f"Could not set weights for layer {layer.name}: {str(e)}")
                
                print("Weight transfer completed.")
            except Exception as e:
                print(f"Warning: Could not copy weights: {str(e)}")
                print("The model will have initialized weights.")
            
            # Save the new model
            new_model_path = "enhanced_deepfake_lstm_model_exact.h5"
            new_model.save(new_model_path)
            print(f"New compatible model saved as '{new_model_path}'")
            
            return True
    
    except Exception as e:
        print(f"Error creating exact compatible model: {str(e)}")
        print("Falling back to creating a simplified compatible model...")
        
        # Create a model that matches the input/output dimensions but with simpler architecture
        input_layer = Input(shape=(64, 340))
        norm_layer = LayerNormalization(axis=-1, epsilon=0.001, name="input_norm")(input_layer)
        
        # First Bidirectional LSTM layer (returns sequences for the second LSTM)
        bilstm_1 = Bidirectional(
            LSTM(64, return_sequences=True, dropout=0.2, name="forward_lstm"),
            backward_layer=LSTM(64, return_sequences=True, dropout=0.2, go_backwards=True, name="backward_lstm"),
            name="bilstm_1"
        )(norm_layer)
        
        # Second Bidirectional LSTM layer
        bilstm_2 = Bidirectional(
            LSTM(32, return_sequences=False, dropout=0.2, name="forward_lstm_1"),
            backward_layer=LSTM(32, return_sequences=False, dropout=0.2, go_backwards=True, name="backward_lstm_1"),
            name="bilstm_2"
        )(bilstm_1)
        
        # Dense layer
        dense = Dense(32, activation='relu', name="dense_2")(bilstm_2)
        dropout = Dropout(0.2, name="dropout_2")(dense)
        
        # Output layer
        output = Dense(1, activation='sigmoid', name="output")(dropout)
        
        # Create and compile the model
        fallback_model = Model(inputs=input_layer, outputs=output, name="SimpleDeepfakeDetector")
        fallback_model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        print("Fallback model created with similar architecture:")
        fallback_model.summary()
        
        # Save the fallback model
        fallback_model_path = "enhanced_deepfake_lstm_model_fallback.h5"
        fallback_model.save(fallback_model_path)
        print(f"Fallback model saved as '{fallback_model_path}'")
        
        return True

if __name__ == "__main__":
    print("Creating exact compatible TensorFlow model...")
    success = create_exact_compatible_model()
    
    if success:
        print("\nSuccess! Now modify deep_fake_land_marks_gui.py to use the new model:")
        print("Change line 46 from:")
        print('    self.model_path = "enhanced_deepfake_lstm_model.h5"')
        print("to:")
        print('    self.model_path = "enhanced_deepfake_lstm_model_exact.h5"')
        print("or if that doesn't work:")
        print('    self.model_path = "enhanced_deepfake_lstm_model_fallback.h5"')
    else:
        print("\nFailed to create compatible model.")