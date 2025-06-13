package gr.iti.mklab.reveal.forensics.maps.manipulatedscore;

import gr.iti.mklab.reveal.forensics.api.reports.ManipulatedScoreReport;
import gr.iti.mklab.reveal.util.Configuration;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.io.ByteArrayInputStream;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.InputStream;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/**
 * Extractor class for the Manipulated Score analysis.
 * This class communicates with the Python service to get the manipulation score and heatmap.
 * 
 * @author Roo
 */
public class ManipulatedScoreExtractor {
    
    private static final String PYTHON_SERVICE_URL = "http://localhost:5000/predict";
    
    public ManipulatedScoreReport report = new ManipulatedScoreReport();
    
    /**
     * Constructor that analyzes the image and generates the manipulation score and heatmap.
     * 
     * @param sourceImagePath Path to the source image
     * @param outputImagePath Path to save the heatmap image
     * @throws IOException If an error occurs during analysis
     */
    public ManipulatedScoreExtractor(String sourceImagePath, String outputImagePath) throws IOException {
        analyzeImage(sourceImagePath, outputImagePath);
    }
    
    /**
     * Analyzes the image using the Python service and generates the manipulation score and heatmap.
     * 
     * @param sourceImagePath Path to the source image
     * @param outputImagePath Path to save the heatmap image
     * @throws IOException If an error occurs during analysis
     */
    private void analyzeImage(String sourceImagePath, String outputImagePath) throws IOException {
        try {
            // Create the output directory if it doesn't exist
            File outputDir = new File(outputImagePath).getParentFile();
            if (!outputDir.exists()) {
                outputDir.mkdirs();
            }
            
            // Create connection to the Python service
            URL url = new URL(PYTHON_SERVICE_URL);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("POST");
            connection.setRequestProperty("Content-Type", "application/json");
            connection.setDoOutput(true);
            
            // Create the request JSON
            JsonObject requestJson = new JsonObject();
            requestJson.addProperty("image_path", sourceImagePath);
            requestJson.addProperty("output_path", outputImagePath);
            
            // Send the request
            try (OutputStream os = connection.getOutputStream();
                 OutputStreamWriter osw = new OutputStreamWriter(os, StandardCharsets.UTF_8)) {
                osw.write(requestJson.toString());
                osw.flush();
            }
            
            // Get the response
            StringBuilder response = new StringBuilder();
            try (BufferedReader br = new BufferedReader(
                    new InputStreamReader(connection.getInputStream(), StandardCharsets.UTF_8))) {
                String responseLine;
                while ((responseLine = br.readLine()) != null) {
                    response.append(responseLine.trim());
                }
            }
            
            // Parse the response
            JsonParser parser = new JsonParser();
            JsonObject responseJson = parser.parse(response.toString()).getAsJsonObject();
            
            // Set the report values
            report.completed = true;
            report.map = outputImagePath;
            report.manipulationScore = responseJson.get("manipulation_score").getAsFloat();
            report.minValue = responseJson.get("min_value").getAsFloat();
            report.maxValue = responseJson.get("max_value").getAsFloat();
            
            // If the heatmap wasn't saved to a file, save it from the base64 data
            if (!new File(outputImagePath).exists() && responseJson.has("heatmap_base64")) {
                String heatmapBase64 = responseJson.get("heatmap_base64").getAsString();
                byte[] heatmapBytes = Base64.getDecoder().decode(heatmapBase64);
                try (InputStream is = new ByteArrayInputStream(heatmapBytes)) {
                    BufferedImage heatmapImage = ImageIO.read(is);
                    ImageIO.write(heatmapImage, "png", new File(outputImagePath));
                }
            }
        } catch (Exception e) {
            System.err.println("Error analyzing image with ManipulatedScoreExtractor: " + e.getMessage());
            e.printStackTrace();
            
            // Create a default report with error status
            report.completed = false;
            report.map = "";
            report.manipulationScore = 0.0f;
            report.minValue = 0.0f;
            report.maxValue = 0.0f;
        }
    }
}