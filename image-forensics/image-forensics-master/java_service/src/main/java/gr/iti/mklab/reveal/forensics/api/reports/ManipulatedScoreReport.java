package gr.iti.mklab.reveal.forensics.api.reports;

import org.mongodb.morphia.annotations.Embedded;

/**
 * Report class for the Manipulated Score analysis.
 * This analysis uses a deep learning model to detect image manipulations.
 * 
 * @author Roo
 */
@Embedded
public class ManipulatedScoreReport {
    public boolean completed = false;
    public String map = "";
    public float manipulationScore = 0.0f;
    public float minValue = 0.0f;
    public float maxValue = 0.0f;
}