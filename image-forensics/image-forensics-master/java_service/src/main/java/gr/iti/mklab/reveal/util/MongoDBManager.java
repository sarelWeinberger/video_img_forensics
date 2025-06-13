package gr.iti.mklab.reveal.util;

import com.mongodb.MongoClient;
import com.mongodb.MongoClientOptions;
import com.mongodb.ServerAddress;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * MongoDB connection manager for the Image Forensics application.
 * Provides methods to connect to MongoDB and access collections.
 */
public class MongoDBManager {
    private static final Logger logger = LoggerFactory.getLogger(MongoDBManager.class);
    
    private static MongoDBManager instance;
    private MongoClient mongoClient;
    private MongoDatabase database;
    
    /**
     * Private constructor to enforce singleton pattern
     */
    private MongoDBManager() {
        try {
            // Create MongoDB client with connection options
            MongoClientOptions options = MongoClientOptions.builder()
                    .connectTimeout(10000)
                    .socketTimeout(60000)
                    .build();
            
            // Connect to MongoDB server
            System.out.println("Connecting to MongoDB at " + Configuration.MONGODB_HOST + ":" + Configuration.MONGODB_PORT);
            System.out.println("Database name: " + Configuration.MONGODB_DATABASE);
            
            // Always use explicit host and port to avoid issues
            // Force using 127.0.0.1 and 27017 as we know MongoDB is running there
            String host = "127.0.0.1";
            int port = 27017;
            
            System.out.println("Using host: " + host + ", port: " + port);
            
            mongoClient = new MongoClient(
                    new ServerAddress(host, port),
                    options
            );
            
            // Get database with fallback
            String dbName = Configuration.MONGODB_DATABASE != null ? Configuration.MONGODB_DATABASE : "image_forensics";
            System.out.println("Using database name: " + dbName);
            database = mongoClient.getDatabase(dbName);
            
            logger.info("Connected to MongoDB at {}:{}, database: {}", 
                    host, 
                    port, 
                    dbName);
        } catch (Exception e) {
            logger.error("Failed to connect to MongoDB: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to connect to MongoDB", e);
        }
    }
    
    /**
     * Get the singleton instance of MongoDBManager
     * @return The MongoDBManager instance
     */
    public static synchronized MongoDBManager getInstance() {
        if (instance == null) {
            instance = new MongoDBManager();
        }
        return instance;
    }
    
    /**
     * Get the reports collection
     * @return The reports collection
     */
    public MongoCollection<Document> getReportsCollection() {
        String collectionName = Configuration.MONGODB_COLLECTION_REPORTS != null ? 
                Configuration.MONGODB_COLLECTION_REPORTS : "forensic_reports";
        System.out.println("Using collection name: " + collectionName);
        return database.getCollection(collectionName);
    }
    
    /**
     * Get a collection by name
     * @param collectionName The name of the collection
     * @return The collection
     */
    public MongoCollection<Document> getCollection(String collectionName) {
        return database.getCollection(collectionName);
    }
    
    /**
     * Close the MongoDB connection
     */
    public void close() {
        if (mongoClient != null) {
            mongoClient.close();
            logger.info("MongoDB connection closed");
        }
    }
}