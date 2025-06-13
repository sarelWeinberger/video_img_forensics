# Java Web Service for Image Forensic Analysis

This Java web service provides a comprehensive set of image forensic analysis tools to detect and visualize potential manipulations in digital images.

## Features

- **Multiple Forensic Algorithms**:
  - Error Level Analysis (ELA)
  - Double JPEG Quantization (DQ)
  - Noise Analysis
  - Ghost Analysis
  - Blocking Artifacts Analysis
  - Median Noise Analysis
  - Grids Analysis
  - Grids Inversed Analysis
  - Manipulated Score Analysis (using deep learning)
  - Metadata Extraction

- **RESTful API** for easy integration with other applications
- **MongoDB** for storing analysis results
- **Spring MVC** architecture for robust web service implementation

## Requirements

- Java 8 (JDK 1.8)
- MongoDB
- Maven
- Sufficient disk space for storing images and analysis results
- Python 3.7 or higher (for the Manipulated Score Analysis)

## Configuration

1. Edit `src/main/resources/remote.properties` to configure:
   - `manipulationReportPath`: Path where images and analysis results will be stored
   - `httpHost`: URL for the Java service (default: http://localhost:8080/)
   - `mongoHost`: MongoDB host (default: 127.0.0.1)
   - `numGhostThreads`: Number of threads for ghost analysis (default: 8)
   - `numTotalThreads`: Total number of threads for analysis (default: 8)
   - `MaxGhostImageSmallDimension`: Maximum dimension for ghost analysis (default: 768)
   - `ForensicProcessTimeout`: Timeout for forensic processes in milliseconds (default: 360000)

## Building and Running

### Complete Running Process

1. **Ensure MongoDB is running**:
   ```bash
   systemctl status mongodb
   ```
   
   If it's not running, start it:
   ```bash
   sudo systemctl start mongodb
   ```

2. **Start the Python service first** (required for Manipulated Score Analysis):
   ```bash
   cd ../python_service
   pip install werkzeug==2.0.1  # Install correct version to avoid dependency conflicts
   pip install -r requirements.txt
   python3 manipulated_score_service.py
   ```
   
   Verify it's running:
   ```bash
   curl -v http://localhost:5000/predict
   ```

3. **Check for existing Java processes** that might be using port 8080:
   ```bash
   ps aux | grep java
   ```
   
   If there are existing processes, stop them:
   ```bash
   kill <PID>
   ```

4. **Build and run the Java service**:
   ```bash
   # Build the project
   mvn clean package
   
   # Run with embedded Tomcat
   mvn tomcat7:run
   ```
   
   Verify it's running:
   ```bash
   curl -v http://localhost:8080/mmapi/media/verificationreport/getreport?hash=test
   ```

### Deploying to a Servlet Container

1. Build the WAR file:
   ```bash
   mvn clean package
   ```

2. Deploy the WAR file to your servlet container (e.g., Tomcat, Jetty):
   ```bash
   cp target/image-forensics.war {path_to_tomcat}/webapps/
   ```

3. Start your servlet container if it's not already running.

4. Remember to start the Python service before starting the servlet container.

## API Endpoints

### Upload an Image

```
POST /mmapi/media/verificationreport/uploadfile
Content-Type: multipart/form-data

Form parameter: file
```

Returns: MD5 hash of the uploaded image

### Add Image by URL

```
GET /mmapi/media/verificationreport/addurl?url={url}
```

Returns: MD5 hash of the downloaded image

### Generate Report

```
GET /mmapi/media/verificationreport/generatereport?hash={hash}
```

Returns: Status message (e.g., "COMPLETEDSUCCESSFULLY", "PROCESSINGALREADYCOMPLETE")

### Get Report

```
GET /mmapi/media/verificationreport/getreport?hash={hash}
```

Returns: JSON object containing all forensic analysis results

### Get Base64 Report

```
GET /mmapi/media/verificationreport/getreportbase64?hash={hash}
```

Returns: JSON object containing all forensic analysis results with base64-encoded images

## Troubleshooting

### Common Issues

1. **"Address already in use" Error**:
   ```
   SEVERE: Failed to initialize end point associated with ProtocolHandler ["http-bio-8080"]
   java.net.BindException: Address already in use (Bind failed) <null>:8080
   ```
   
   **Solution**: Another process is using port 8080. Find and stop it:
   ```bash
   ps aux | grep java
   kill <PID>
   ```

2. **404 Not Found for All Endpoints**:
   - Ensure the Java service is properly started
   - Check if multiple instances of the Java service are running and causing conflicts
   - Verify that the Spring MVC configuration is correct

3. **404 Not Found for Images**:
   - Ensure the `manipulationReportPath` in `remote.properties` is correct
   - Check that the directory has proper read and execute permissions
   - Verify that the `<mvc:resources>` mapping in `mvc-dispatcher-servlet.xml` is correct

4. **MongoDB Connection Errors**:
   - Verify MongoDB is running: `systemctl status mongodb` or `mongod --version`
   - Check MongoDB connection settings in `remote.properties`
   - Verify MongoDB is accessible: `mongo --eval "db.adminCommand('listDatabases')"`
   - After running the Java service, you should see a database called "ForensicDatabase":
     ```bash
     mongo --eval "db.adminCommand('listDatabases')"
     ```
   - You can check the collections in the database:
     ```bash
     mongo ForensicDatabase --eval "db.getCollectionNames()"
     ```
   - The "ForensicReport" collection stores the results of the forensic analysis:
     ```bash
     mongo ForensicDatabase --eval "db.ForensicReport.find().limit(1).pretty()"
     ```

5. **CORS Issues**:
   - Ensure the `CORSFilter` is properly configured in `web.xml`
   - Check that the allowed origins match your frontend application

6. **Out of Memory Errors**:
   - Increase Java heap size: `export MAVEN_OPTS="-Xmx2g"`
   - Reduce `MaxGhostImageSmallDimension` in `remote.properties`
   - Decrease the number of threads in `remote.properties`

7. **Slow Analysis**:
   - Increase the number of threads in `remote.properties`
   - Ensure your system has sufficient CPU resources
   - Consider using a more powerful machine for large images

8. **Manipulated Score Analysis Not Working**:
   - Ensure the Python service is running on port 5000
   - Check the logs for any connection errors to the Python service
   - Verify that the `PYTHON_SERVICE_URL` in `ManipulatedScoreExtractor.java` is correct

## Example Usage

### Java Client Example

```java
// Initialize service
String mongodbIP = "127.0.0.1";
String outputPath = "/path/to/output/";

// Download and analyze image
String hash = ReportManagement.downloadURL("http://example.com/image.jpg", outputPath, mongodbIP);
ReportManagement.createReport(hash, mongodbIP, outputPath);
ForensicReport report = ReportManagement.getReport(hash, mongodbIP);
```

### cURL Examples

```bash
# Upload an image
curl -X POST -F "file=@/path/to/image.jpg" http://localhost:8080/mmapi/media/verificationreport/uploadfile

# Add image by URL
curl "http://localhost:8080/mmapi/media/verificationreport/addurl?url=http://example.com/image.jpg"

# Generate report
curl "http://localhost:8080/mmapi/media/verificationreport/generatereport?hash=092178c6e7bbc857e0fbdfb0c409035b"

# Get report
curl "http://localhost:8080/mmapi/media/verificationreport/getreport?hash=092178c6e7bbc857e0fbdfb0c409035b"
```

## Python Service for Manipulated Score Analysis

The Manipulated Score Analysis uses a Python service that runs separately from the Java service. This service uses deep learning to detect image manipulations and generate a heatmap with confidence scores.

### Setting Up the Python Service

1. Navigate to the `python_service` directory:
   ```bash
   cd ../python_service
   ```

2. Install the correct version of Werkzeug to avoid dependency conflicts:
   ```bash
   pip install werkzeug==2.0.1
   ```

3. Install other dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the Python service directly:
   ```bash
   python3 manipulated_score_service.py
   ```

   Or specify a custom port:
   ```bash
   python3 manipulated_score_service.py 8000
   ```

5. Verify the Python service is running:
   ```bash
   curl -v http://localhost:5000/predict
   ```

6. The Python service must be started before the Java service for the Manipulated Score Analysis to work properly.

### Configuration

The Java service is configured to communicate with the Python service at http://localhost:5000/. If you need to change this, update the `PYTHON_SERVICE_URL` in `ManipulatedScoreExtractor.java`.

## Security Considerations

This service is designed for research and educational purposes. When deploying in a production environment, consider:

1. Implementing proper authentication and authorization
2. Setting up HTTPS
3. Limiting file upload sizes
4. Implementing rate limiting
5. Regularly updating dependencies

## License

This project is licensed under the terms specified in the original repository.

## Acknowledgments

Original project by Markos Zampoglou <markzampoglou@iti.gr> and the MKLab-ITI team.