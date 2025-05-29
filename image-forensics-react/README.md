# Image Forensics React Frontend

A modern React-based frontend for the Image Forensics Analysis Framework. This application provides a user-friendly interface for uploading images, initiating forensic analysis, and visualizing the results through interactive heat maps and detailed reports.

## Features

- **User-friendly Interface**: Clean, intuitive design for easy navigation
- **Image Upload**: Support for both file uploads and URL submissions
- **Comprehensive Visualization**: Interactive heat maps for all forensic analyses
- **Detailed Descriptions**: Informative explanations of each analysis technique
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Progress indicators for long-running analyses

## Forensic Analysis Visualizations

The application provides visualizations for multiple forensic techniques:

1. **Error Level Analysis (ELA)**: Highlights differences in compression levels
2. **Double JPEG Quantization (DQ)**: Detects areas compressed multiple times
3. **Noise Analysis**: Examines noise patterns for inconsistencies
4. **Ghost Analysis**: Reveals traces of removed content
5. **Blocking Artifacts**: Detects JPEG compression artifacts
6. **Median Noise**: Analyzes residual noise patterns
7. **Grids Analysis**: Examines JPEG block grid alignment
8. **Grids Inversed**: Alternative visualization of grid inconsistencies
9. **Metadata**: Extracts and displays image metadata

## Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)
- Running instance of the Java backend service

## Installation

1. Clone the repository (if not already done):
   ```bash
   git clone https://github.com/your-repo/image-forensics.git
   cd image-forensics-react
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure the application:
   - Edit `src/config.js` to set the API URL (default: http://localhost:8080/mmapi)

4. Start the development server:
   ```bash
   npm start
   ```

5. The application will be available at http://localhost:3000/

## Building for Production

To create a production build:

```bash
npm run build
```

The build artifacts will be stored in the `build/` directory.

## Project Structure

```
image-forensics-react/
├── public/                  # Static files
├── src/                     # Source code
│   ├── components/          # React components
│   │   ├── ImageUpload.js   # Image upload component
│   │   ├── ReportDetail.js  # Forensic report visualization
│   │   └── ...
│   ├── services/            # API services
│   │   ├── api.js           # API wrapper
│   │   └── realApi.js       # Implementation of API calls
│   ├── styles/              # CSS styles
│   │   └── HeatMap.css      # Styles for heat map visualizations
│   ├── App.js               # Main application component
│   ├── config.js            # Application configuration
│   └── index.js             # Application entry point
└── package.json             # Project dependencies and scripts
```

## Usage

1. Open the application in your browser
2. Upload an image using the file upload or URL input
3. Wait for the analysis to complete (this may take a few minutes for large images)
4. Navigate through the tabs to view different forensic analyses
5. Hover over heat maps to see details and examine areas of interest
6. View metadata information for additional context

## Customization

### Styling

The application uses Bootstrap for styling. You can customize the appearance by:

1. Editing the CSS files in the `src/styles/` directory
2. Modifying Bootstrap variables in `src/index.scss` (if using SCSS)
3. Adding custom CSS classes to components

### Adding New Analyses

To add a new analysis visualization:

1. Update the `ReportDetail.js` component to include a new tab
2. Add the corresponding visualization logic
3. Update the API service to fetch the new analysis data
4. Add appropriate styling for the new visualization

## Troubleshooting

### Common Issues

1. **API Connection Errors**:
   - Verify the Java backend is running
   - Check the API URL in `src/config.js`
   - Ensure CORS is properly configured on the backend

2. **Image Loading Issues**:
   - Check browser console for specific errors
   - Verify the image paths in the API responses
   - Ensure the proxy configuration in `setupProxy.js` is correct

3. **Performance Issues**:
   - Large images may cause slow rendering
   - Consider implementing lazy loading for heat maps
   - Use compressed images when possible

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the terms specified in the original repository.

## Acknowledgments

- Original Image Forensics framework by Markos Zampoglou and the MKLab-ITI team
- Built with React, Bootstrap, and other open-source libraries