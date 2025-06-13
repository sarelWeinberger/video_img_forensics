package gr.iti.mklab.reveal.web;

import gr.iti.mklab.reveal.service.ForensicReportService;
import org.bson.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * REST controller for forensic report operations
 */
@Controller
@RequestMapping("/api/reports")
public class ForensicReportController {
    private static final Logger logger = LoggerFactory.getLogger(ForensicReportController.class);
    
    private final ForensicReportService reportService;
    
    @Autowired
    public ForensicReportController(ForensicReportService reportService) {
        this.reportService = reportService;
        logger.info("ForensicReportController initialized");
    }
    
    /**
     * Create a new forensic report
     * 
     * @param requestBody The report data
     * @return The created report ID
     */
    @RequestMapping(method = RequestMethod.POST, produces = MediaType.APPLICATION_JSON_VALUE)
    @ResponseBody
    public ResponseEntity<Map<String, Object>> createReport(@RequestBody Map<String, Object> requestBody) {
        try {
            String imageHash = (String) requestBody.get("imageHash");
            String filename = (String) requestBody.get("filename");
            Double manipulationScore = Double.parseDouble(requestBody.get("manipulationScore").toString());
            
            // Convert detected regions to Document objects
            List<Document> detectedRegions = new ArrayList<>();
            if (requestBody.containsKey("detectedRegions")) {
                List<Map<String, Object>> regions = (List<Map<String, Object>>) requestBody.get("detectedRegions");
                for (Map<String, Object> region : regions) {
                    detectedRegions.add(new Document(region));
                }
            }
            
            // Convert metadata to Document
            Document metadata = null;
            if (requestBody.containsKey("metadata")) {
                metadata = new Document((Map<String, Object>) requestBody.get("metadata"));
            }
            
            String reportId = reportService.createReport(imageHash, filename, manipulationScore, detectedRegions, metadata);
            
            Map<String, Object> response = new HashMap<>();
            response.put("id", reportId);
            response.put("success", true);
            
            return ResponseEntity.status(HttpStatus.CREATED).body(response);
        } catch (Exception e) {
            logger.error("Error creating report: {}", e.getMessage(), e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
    
    /**
     * Get a forensic report by ID
     * 
     * @param id The report ID
     * @return The report data
     */
    @RequestMapping(value = "/{id}", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    @ResponseBody
    public ResponseEntity<Map<String, Object>> getReport(@PathVariable("id") String id) {
        try {
            Document report = reportService.getReportById(id);
            
            if (report == null) {
                Map<String, Object> response = new HashMap<>();
                response.put("success", false);
                response.put("error", "Report not found");
                
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
            }
            
            // Convert Document to Map
            Map<String, Object> reportMap = report;
            reportMap.put("success", true);
            
            return ResponseEntity.ok(reportMap);
        } catch (Exception e) {
            logger.error("Error retrieving report: {}", e.getMessage(), e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
    
    /**
     * Get all forensic reports for an image
     * 
     * @param imageHash The image hash
     * @return List of reports
     */
    @RequestMapping(value = "/image/{imageHash}", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    @ResponseBody
    public ResponseEntity<Map<String, Object>> getReportsByImageHash(@PathVariable("imageHash") String imageHash) {
        try {
            List<Document> reports = reportService.getReportsByImageHash(imageHash);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("reports", reports);
            response.put("count", reports.size());
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Error retrieving reports by image hash: {}", e.getMessage(), e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
    
    /**
     * Update a forensic report
     * 
     * @param id The report ID
     * @param requestBody The updated report data
     * @return Success status
     */
    @RequestMapping(value = "/{id}", method = RequestMethod.PUT, produces = MediaType.APPLICATION_JSON_VALUE)
    @ResponseBody
    public ResponseEntity<Map<String, Object>> updateReport(@PathVariable("id") String id, @RequestBody Map<String, Object> requestBody) {
        try {
            Document updates = new Document(requestBody);
            boolean updated = reportService.updateReport(id, updates);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", updated);
            
            if (!updated) {
                response.put("error", "Report not found or not modified");
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
            }
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Error updating report: {}", e.getMessage(), e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
    
    /**
     * Delete a forensic report
     * 
     * @param id The report ID
     * @return Success status
     */
    @RequestMapping(value = "/{id}", method = RequestMethod.DELETE, produces = MediaType.APPLICATION_JSON_VALUE)
    @ResponseBody
    public ResponseEntity<Map<String, Object>> deleteReport(@PathVariable("id") String id) {
        try {
            boolean deleted = reportService.deleteReport(id);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", deleted);
            
            if (!deleted) {
                response.put("error", "Report not found or not deleted");
                return ResponseEntity.status(HttpStatus.NOT_FOUND).body(response);
            }
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Error deleting report: {}", e.getMessage(), e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
    
    /**
     * Test endpoint to check if MongoDB is connected
     * 
     * @return MongoDB connection status
     */
    @RequestMapping(value = "/test-mongodb", method = RequestMethod.GET, produces = MediaType.APPLICATION_JSON_VALUE)
    @ResponseBody
    public ResponseEntity<Map<String, Object>> testMongoDB() {
        Map<String, Object> response = new HashMap<>();
        
        try {
            // Try to access the reports collection
            long count = reportService.getReportsByImageHash("test").size();
            
            response.put("success", true);
            response.put("message", "MongoDB connection successful");
            response.put("reportsCount", count);
            
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("MongoDB connection test failed: {}", e.getMessage(), e);
            
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
}