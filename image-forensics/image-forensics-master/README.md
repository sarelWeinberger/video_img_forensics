# Image Forensics Analysis Framework

This is an integrated framework for image forensic analysis, designed to detect and visualize potential manipulations in digital images. The system consists of a Java backend service that performs the forensic analysis and a React frontend that provides a user-friendly interface for uploading images and viewing the results.

## System Components

### Java Backend Service

The Java service implements multiple forensic analysis algorithms:

1. **Error Level Analysis (ELA)** - Highlights differences in compression levels by resaving the image at a known quality and calculating the difference
2. **Double JPEG Quantization (DQ)** - Detects areas that have been compressed multiple times with different quality settings
3. **Noise Analysis** - Examines the natural noise patterns present in all digital images to detect inconsistencies
4. **Ghost Analysis** - Reveals traces of content that has been removed or altered in an image
5. **Blocking Artifacts Analysis** - Detects JPEG compression artifacts that appear as visible blocks in the image
6. **Median Noise Analysis** - Applies a median filter to the image and examines the residual noise patterns
7. **Grids Analysis** - Examines the alignment of JPEG compression blocks across the image
8. **Grids Inversed Analysis** - Provides an alternative visualization of JPEG grid inconsistencies

### React Frontend

The React frontend provides:

- A user-friendly interface for uploading images or providing URLs
- Detailed visualization of all forensic analyses with heat maps
- Comprehensive descriptions of each analysis technique
- Metadata extraction and display
- Responsive design for various screen sizes

## Setup and Installation

### Prerequisites

- Java 8 (JDK 1.8)
- MongoDB
- Maven
- Node.js and npm

### Java Backend Setup

1. Configure MongoDB:
   - Start MongoDB service
   - Default connection is localhost:27017

2. Configure the application:
   - Edit `java_service/src/main/resources/remote.properties` to set:
     - `manipulationReportPath`: Path where images and analysis results will be stored
     - `httpHost`: URL for the Java service (default: http://localhost:8080/)

3. Build and run the Java service:
   ```bash
   cd java_service
   mvn clean package tomcat7:run
   ```

4. The service will be available at http://localhost:8080/

### React Frontend Setup

1. Install dependencies:
   ```bash
   cd image-forensics-react
   npm install
   ```

2. Configure the API endpoint:
   - Edit `src/config.js` to set the API URL (default: http://localhost:8080/mmapi)

3. Start the development server:
   ```bash
   npm start
   ```

4. The frontend will be available at http://localhost:3000/

## Usage

1. Open the React frontend in your browser
2. Upload an image or provide a URL
3. Wait for the analysis to complete
4. View the results in the various tabs:
   - Error Level Analysis
   - Double Quantization
   - Noise Analysis
   - Ghost Analysis
   - Blocking Artifacts
   - Median Noise
   - Grids Analysis
   - Grids Inversed
   - Metadata

## API Endpoints

- **Upload an image**: `POST /mmapi/media/verificationreport/uploadfile`
- **Add image by URL**: `GET /mmapi/media/verificationreport/addurl?url={url}`
- **Generate report**: `GET /mmapi/media/verificationreport/generatereport?hash={hash}`
- **Get report**: `GET /mmapi/media/verificationreport/getreport?hash={hash}`
- **Get base64 report**: `GET /mmapi/media/verificationreport/getreportbase64?hash={hash}`

## Troubleshooting

- **Image loading issues**: Ensure the image directory has proper read and execute permissions
- **MongoDB connection errors**: Verify MongoDB is running and accessible
- **CORS issues**: Check that the CORSFilter is properly configured in the Java service

## Citations

Please cite the following paper in your publications if you use the Java implementations:

```
@inproceedings{zamp16,
  author = "Markos Zampoglou and Symeon Papadopoulos and Yiannis Kompatsiaris and Ruben Bouwmeester and Jochen Spangenberg",
  booktitle = "Social Media In the NewsRoom, {#SMNews16@CWSM}, Tenth International AAAI Conference on Web and Social Media workshops",
  title = "Web and Social Media Image Forensics for News Professionals",
  year = "2016",
}
```

If you use the Matlab implementations, use the following citation:

```
@article{zampAcc,
  author = "Markos Zampoglou and Symeon Papadopoulos and Yiannis Kompatsiaris",
  title = "A Large-Scale Evaluation of Splicing Localization Algorithms for Web Images",
  journal = "Multimedia Tools and Applications",
  doi = "10.1007/s11042-016-3795-2"
  pages= "Accepted for publication",
}
```

In either case, you must also cite the original algorithm publication. The README file within each Matlab algorithm subfolder contains the corresponding citation.

## License

This project is licensed under the terms specified in the original repository.

## Acknowledgments

Original project by Markos Zampoglou <markzampoglou@iti.gr> and the MKLab-ITI team.

React frontend and additional improvements added in 2025.