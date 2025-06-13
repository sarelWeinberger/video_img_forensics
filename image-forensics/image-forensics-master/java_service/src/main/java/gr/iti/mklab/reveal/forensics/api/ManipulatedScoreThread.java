package gr.iti.mklab.reveal.forensics.api;

import gr.iti.mklab.reveal.forensics.api.reports.ManipulatedScoreReport;
import gr.iti.mklab.reveal.forensics.maps.manipulatedscore.ManipulatedScoreExtractor;

import java.io.File;
import java.io.IOException;
import java.util.concurrent.Callable;

/**
 * Thread class for the Manipulated Score analysis.
 * This class is used by the ReportManagement class to run the analysis in a separate thread.
 * 
 * @author Roo
 */
public class ManipulatedScoreThread implements Callable {
    private String sourceFile;
    private File outputFile;
    
    /**
     * Constructor for the ManipulatedScoreThread class.
     * 
     * @param sourceFile Path to the source image
     * @param outputFile File to save the heatmap image
     */
    public ManipulatedScoreThread(String sourceFile, File outputFile) {
        this.sourceFile = sourceFile;
        this.outputFile = outputFile;
    }
    
    @Override
    public Object call() throws Exception {
        return manipulatedScoreCalculation();
    }
    
    /**
     * Performs the manipulated score analysis.
     * 
     * @return ManipulatedScoreReport containing the analysis results
     * @throws IOException If an error occurs during analysis
     */
    public ManipulatedScoreReport manipulatedScoreCalculation() throws IOException {
        System.out.println("Starting Manipulated Score analysis...");
        ManipulatedScoreExtractor manipulatedScoreExtractor = new ManipulatedScoreExtractor(sourceFile, outputFile.getCanonicalPath());
        ManipulatedScoreReport manipulatedScoreReport = manipulatedScoreExtractor.report;
        manipulatedScoreReport.completed = true;
        manipulatedScoreReport.map = outputFile.getCanonicalPath();
        System.out.println("Manipulated Score analysis completed.");
        return manipulatedScoreReport;
    }
}