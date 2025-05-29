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
  - Metadata Extraction

- **RESTful API** for easy integration with other applications
- **MongoDB** for storing analysis results
- **Spring MVC** architecture for robust web service implementation

## Requirements

- Java 8 (JDK 1.8)
- MongoDB
- Maven
- Sufficient disk space for storing images and analysis results

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

### Using Maven

```bash
# Build the project
mvn clean package

# Run with embedded Tomcat
mvn tomcat7:run
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

1. **404 Not Found for Images**:
   - Ensure the `manipulationReportPath` in `remote.properties` is correct
   - Check that the directory has proper read and execute permissions
   - Verify that the `<mvc:resources>` mapping in `mvc-dispatcher-servlet.xml` is correct

2. **MongoDB Connection Errors**:
   - Verify MongoDB is running: `systemctl status mongodb` or `mongod --version`
   - Check MongoDB connection settings in `remote.properties`

3. **CORS Issues**:
   - Ensure the `CORSFilter` is properly configured in `web.xml`
   - Check that the allowed origins match your frontend application

4. **Out of Memory Errors**:
   - Increase Java heap size: `export MAVEN_OPTS="-Xmx2g"`
   - Reduce `MaxGhostImageSmallDimension` in `remote.properties`
   - Decrease the number of threads in `remote.properties`

5. **Slow Analysis**:
   - Increase the number of threads in `remote.properties`
   - Ensure your system has sufficient CPU resources
   - Consider using a more powerful machine for large images

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