package gr.iti.mklab.reveal.util;


import org.apache.commons.configuration.ConfigurationException;
import org.apache.commons.configuration.PropertiesConfiguration;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

/**
 * Created by kandreadou on 2/2/15.
 */
public class Configuration {

    public static String INDEX_SERVICE_HOST;
    public static String MONGO_HOST;
    public static boolean ADD_SOCIAL_MEDIA;
    public static String MANIPULATION_REPORT_PATH;
    public static boolean PUBLISH_RABBITMQ;
    public static int NUM_TOTAL_THREADS;
    public static int NUM_GHOST_THREADS;
    public static long FORENSIC_PROCESS_TIMEOUT;
    public static int MAX_GHOST_IMAGE_SMALL_DIM;
    public static String HTTP_HOST;
    public static String MONGO_USER;
    public static String MONGO_PASS;
    public static String MONGO_URI;
    
    // MongoDB properties for the new MongoDB integration
    public static String MONGODB_HOST;
    public static int MONGODB_PORT;
    public static String MONGODB_DATABASE;
    public static String MONGODB_COLLECTION_REPORTS;

    public static void load(InputStream stream) throws ConfigurationException, IOException {
        Properties conf = new Properties();
        conf.load(stream);
    
        INDEX_SERVICE_HOST = conf.getProperty("indexServiceHost");
        MONGO_HOST = conf.getProperty("mongoHost");
        ADD_SOCIAL_MEDIA = Boolean.valueOf(conf.getProperty("getSocialMedia"));
        MANIPULATION_REPORT_PATH = conf.getProperty("manipulationReportPath");
        PUBLISH_RABBITMQ = Boolean.parseBoolean(conf.getProperty("publish"));
        NUM_TOTAL_THREADS=Integer.parseInt(conf.getProperty("numTotalThreads"));
        NUM_GHOST_THREADS=Integer.parseInt(conf.getProperty("numGhostThreads"));
        FORENSIC_PROCESS_TIMEOUT=Long.parseLong(conf.getProperty("ForensicProcessTimeout"));
        MAX_GHOST_IMAGE_SMALL_DIM=Integer.parseInt(conf.getProperty("MaxGhostImageSmallDimension"));
        HTTP_HOST=conf.getProperty("httpHost");
        MONGO_USER=conf.getProperty("mongouser");
        MONGO_PASS=conf.getProperty("mongopass");
        
        if (MONGO_USER != null && !MONGO_USER.isEmpty() && MONGO_PASS != null && !MONGO_PASS.isEmpty()) {
            MONGO_URI="mongodb://"+MONGO_USER+":"+MONGO_PASS+"@"+MONGO_HOST+"/";
        } else {
            MONGO_URI="mongodb://"+MONGO_HOST+"/";
        }
        
        // Initialize the new MongoDB properties
        MONGODB_HOST = conf.getProperty("mongodb.host", "localhost");
        MONGODB_PORT = Integer.parseInt(conf.getProperty("mongodb.port", "27017"));
        MONGODB_DATABASE = conf.getProperty("mongodb.database", "image_forensics");
        MONGODB_COLLECTION_REPORTS = conf.getProperty("mongodb.collection.reports", "forensic_reports");
    }
}
