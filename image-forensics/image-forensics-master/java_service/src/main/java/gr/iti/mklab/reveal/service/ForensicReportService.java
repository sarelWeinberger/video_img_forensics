package gr.iti.mklab.reveal.service;

import gr.iti.mklab.reveal.util.MongoDBManager;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.Filters;
import com.mongodb.client.result.UpdateResult;
import org.bson.Document;
import org.bson.types.ObjectId;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

/**
 * Service for managing forensic reports in MongoDB
 */
@Service
public class ForensicReportService {
    private static final Logger logger = LoggerFactory.getLogger(ForensicReportService.class);
    
    private final MongoCollection<Document> reportsCollection;
    
    /**
     * Constructor that initializes the MongoDB connection
     */
    public ForensicReportService() {
        this.reportsCollection = MongoDBManager.getInstance().getReportsCollection();
        logger.info("ForensicReportService initialized with collection: {}", 
                reportsCollection.getNamespace().getCollectionName());
    }
    
    /**
     * Create a new forensic report
     * 
     * @param imageHash The hash of the analyzed image
     * @param filename The filename of the analyzed image
     * @param manipulationScore The manipulation detection score (0-100)
     * @param detectedRegions List of detected manipulation regions
     * @param metadata Additional metadata about the analysis
     * @return The ID of the created report
     */
    public String createReport(String imageHash, String filename, 
                              double manipulationScore, 
                              List<Document> detectedRegions, 
                              Document metadata) {
        try {
            Document report = new Document()
                    .append("imageHash", imageHash)
                    .append("filename", filename)
                    .append("manipulationScore", manipulationScore)
                    .append("detectedRegions", detectedRegions != null ? detectedRegions : new ArrayList<>())
                    .append("metadata", metadata != null ? metadata : new Document())
                    .append("createdAt", new Date())
                    .append("updatedAt", new Date());
            
            reportsCollection.insertOne(report);
            ObjectId id = report.getObjectId("_id");
            
            logger.info("Created forensic report with ID: {}", id);
            return id.toString();
        } catch (Exception e) {
            logger.error("Error creating forensic report: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to create forensic report", e);
        }
    }
    
    /**
     * Get a forensic report by ID
     * 
     * @param reportId The ID of the report to retrieve
     * @return The report document or null if not found
     */
    public Document getReportById(String reportId) {
        try {
            ObjectId objectId = new ObjectId(reportId);
            Document report = reportsCollection.find(Filters.eq("_id", objectId)).first();
            
            if (report != null) {
                logger.info("Retrieved forensic report with ID: {}", reportId);
            } else {
                logger.warn("Forensic report with ID {} not found", reportId);
            }
            
            return report;
        } catch (Exception e) {
            logger.error("Error retrieving forensic report: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to retrieve forensic report", e);
        }
    }
    
    /**
     * Get all forensic reports for a specific image hash
     * 
     * @param imageHash The hash of the image
     * @return List of report documents
     */
    public List<Document> getReportsByImageHash(String imageHash) {
        try {
            List<Document> reports = new ArrayList<>();
            reportsCollection.find(Filters.eq("imageHash", imageHash))
                    .into(reports);
            
            logger.info("Retrieved {} forensic reports for image hash: {}", reports.size(), imageHash);
            return reports;
        } catch (Exception e) {
            logger.error("Error retrieving forensic reports by image hash: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to retrieve forensic reports by image hash", e);
        }
    }
    
    /**
     * Update a forensic report
     * 
     * @param reportId The ID of the report to update
     * @param updates The updates to apply to the report
     * @return True if the report was updated, false otherwise
     */
    public boolean updateReport(String reportId, Document updates) {
        try {
            ObjectId objectId = new ObjectId(reportId);
            
            // Remove _id field if present in updates
            updates.remove("_id");
            
            // Add updatedAt field
            updates.append("updatedAt", new Date());
            
            // Create a document for the $set operation
            Document setDocument = new Document();
            for (String key : updates.keySet()) {
                setDocument.append(key, updates.get(key));
            }
            
            UpdateResult result = reportsCollection.updateOne(
                    Filters.eq("_id", objectId),
                    new Document("$set", setDocument));
            
            boolean updated = result.getModifiedCount() > 0;
            if (updated) {
                logger.info("Updated forensic report with ID: {}", reportId);
            } else {
                logger.warn("Forensic report with ID {} not found or not modified", reportId);
            }
            
            return updated;
        } catch (Exception e) {
            logger.error("Error updating forensic report: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to update forensic report", e);
        }
    }
    
    /**
     * Delete a forensic report
     * 
     * @param reportId The ID of the report to delete
     * @return True if the report was deleted, false otherwise
     */
    public boolean deleteReport(String reportId) {
        try {
            ObjectId objectId = new ObjectId(reportId);
            long deletedCount = reportsCollection.deleteOne(Filters.eq("_id", objectId)).getDeletedCount();
            
            boolean deleted = deletedCount > 0;
            if (deleted) {
                logger.info("Deleted forensic report with ID: {}", reportId);
            } else {
                logger.warn("Forensic report with ID {} not found or not deleted", reportId);
            }
            
            return deleted;
        } catch (Exception e) {
            logger.error("Error deleting forensic report: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to delete forensic report", e);
        }
    }
}