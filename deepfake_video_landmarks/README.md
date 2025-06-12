# Deepfake Video Landmarks Detection

This project provides a GUI application for detecting deepfakes in videos using facial landmarks and LSTM neural networks.

## TensorFlow Model Compatibility Fix

### Issue

The original model (`enhanced_deepfake_lstm_model.h5`) was created with an older version of TensorFlow and used parameters that are no longer supported in TensorFlow 2.15.0, specifically the `batch_shape` parameter in the InputLayer configuration:

```
Error when deserializing class 'InputLayer' using config={'batch_shape': [None, 64, 340], 'dtype': 'float32', 'sparse': False, 'ragged': False, 'name': 'input_features'}.

Exception encountered: Unrecognized keyword arguments: ['batch_shape']
```

### Solution

We created a compatible model (`enhanced_deepfake_lstm_model_fallback.h5`) that closely matches the architecture of the original model but uses parameter names compatible with TensorFlow 2.15.0.

## Model Architecture

```
Model: "SimpleDeepfakeDetector"
_________________________________________________________________
 Layer (type)                Output Shape              Param #   
=================================================================
 input_1 (InputLayer)        [(None, 64, 340)]         0         
                                                                 
 input_norm (LayerNormaliza  (None, 64, 340)           680       
 tion)                                                           
                                                                 
 bilstm_1 (Bidirectional)    (None, 64, 128)           207360    
                                                                 
 bilstm_2 (Bidirectional)    (None, 64)                41216     
                                                                 
 dense_2 (Dense)             (None, 32)                2080      
                                                                 
 dropout_2 (Dropout)         (None, 32)                0         
                                                                 
 output (Dense)              (None, 1)                 33        
                                                                 
=================================================================
Total params: 251369 (981.91 KB)
Trainable params: 251369 (981.91 KB)
Non-trainable params: 0 (0.00 Byte)
```

## Input/Output Format

- **Input**: The model expects input with shape `(batch_size, 64, 340)`, where:
  - 64 represents the number of time steps (frames)
  - 340 represents the features per time step (5 features for each of the 68 facial landmarks)

- **Output**: A single value between 0 and 1 indicating the probability of the video being a deepfake:
  - Values closer to 0 suggest the video is real
  - Values closer to 1 suggest the video is a deepfake

## Usage

1. Ensure you have the required dependencies installed:
   - TensorFlow 2.15.0
   - OpenCV
   - dlib
   - tkinter
   - numpy
   - matplotlib

2. Make sure you have the facial landmark predictor file:
   - `shape_predictor_68_face_landmarks.dat`

3. Run the GUI application:
   ```
   python deep_fake_land_marks_gui.py
   ```

4. Use the GUI to:
   - Load a video for analysis
   - Start the analysis process
   - View real-time predictions and visualizations

## Files

- `deep_fake_land_marks_gui.py`: Main GUI application
- `enhanced_deepfake_lstm_model_fallback.h5`: Compatible TensorFlow model
- `shape_predictor_68_face_landmarks.dat`: Facial landmark predictor
- `create_exact_compatible_model.py`: Script to create the compatible model
- `compare_models.py`: Script to compare predictions from different model versions
- `test_model.py`: Script to test model loading and prediction