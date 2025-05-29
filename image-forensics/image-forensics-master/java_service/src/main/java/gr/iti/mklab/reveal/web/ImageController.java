package gr.iti.mklab.reveal.web;

import gr.iti.mklab.reveal.util.Configuration;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.ResponseBody;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import javax.annotation.PostConstruct;

@Controller
@RequestMapping("/images")
public class ImageController {

    private String imagesPath;
    
    @PostConstruct
    public void init() {
        try {
            // Load the configuration once when the controller is initialized
            Configuration.load(getClass().getResourceAsStream("/remote.properties"));
            imagesPath = Configuration.MANIPULATION_REPORT_PATH;
        } catch (Exception e) {
            // Default path if configuration fails
            imagesPath = "/home/azureuser/image-forensics/images/";
            System.err.println("Error loading configuration: " + e.getMessage());
        }
    }

    /**
     * Serves image files from the configured images directory
     * @param hash The hash of the image
     * @param filename The filename of the image
     * @return The image file as a byte array
     * @throws IOException If the file cannot be read
     */
    @RequestMapping(value = "/{hash}/{filename:.+}", method = RequestMethod.GET, produces = {MediaType.IMAGE_JPEG_VALUE, MediaType.IMAGE_PNG_VALUE})
    @ResponseBody
    public byte[] getImage(@PathVariable("hash") String hash, @PathVariable("filename") String filename) throws IOException {
        // Construct the path to the image file
        Path imagePath = Paths.get(imagesPath, hash, filename);
        File imageFile = imagePath.toFile();
        
        // Check if the file exists
        if (!imageFile.exists()) {
            throw new IOException("Image file not found: " + imagePath);
        }
        
        // Read the file and return it as a byte array
        return Files.readAllBytes(imagePath);
    }
}