# MongoDB Setup and Usage

This document provides instructions on how to use MongoDB with the Image Forensics application.

## MongoDB Installation

MongoDB has been installed on this system. The MongoDB server is running on the default port (27017).

## Starting MongoDB

MongoDB should start automatically when the system boots. If it doesn't, you can start it manually using the provided script:

```bash
./start_mongodb.sh
```

## MongoDB Configuration

The MongoDB configuration for the Image Forensics application is stored in the following files:

- `image-forensics/image-forensics-master/java_service/src/main/resources/remote.properties`: Contains the MongoDB connection settings.
- `image-forensics/image-forensics-master/java_service/src/main/java/gr/iti/mklab/reveal/util/Configuration.java`: Loads the MongoDB configuration from the properties file.
- `image-forensics/image-forensics-master/java_service/src/main/java/gr/iti/mklab/reveal/util/MongoDBManager.java`: Manages the MongoDB connection.

## MongoDB Database and Collections

The application uses the following MongoDB database and collections:

- Database: `image_forensics`
- Collection: `forensic_reports`

## Testing MongoDB Connection

You can test the MongoDB connection using the following command:

```bash
mongosh --eval "db.getSiblingDB('image_forensics').forensic_reports.find()"
```

## MongoDB REST API

The application provides a REST API for accessing the MongoDB database. The API endpoints are:

- `POST /api/reports`: Create a new forensic report
- `GET /api/reports/{id}`: Get a forensic report by ID
- `GET /api/reports/image/{imageHash}`: Get all forensic reports for an image
- `PUT /api/reports/{id}`: Update a forensic report
- `DELETE /api/reports/{id}`: Delete a forensic report
- `GET /api/reports/test-mongodb`: Test MongoDB connection

## Troubleshooting

If you encounter issues with MongoDB, check the following:

1. Make sure MongoDB is running:
   ```bash
   ps aux | grep mongod
   ```

2. Check if MongoDB is listening on port 27017:
   ```bash
   netstat -tuln | grep 27017
   ```

3. Check the MongoDB logs:
   ```bash
   cat /var/log/mongodb.log
   ```

4. Restart MongoDB:
   ```bash
   sudo systemctl restart mongod
   ```
   or
   ```bash
   ./start_mongodb.sh