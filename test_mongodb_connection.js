// Simple script to test MongoDB connection
const { MongoClient } = require('mongodb');

// Connection URL
const url = 'mongodb://localhost:27017';
const client = new MongoClient(url);

// Database Name
const dbName = 'image_forensics';

async function main() {
  try {
    // Connect to the MongoDB server
    await client.connect();
    console.log('Connected successfully to MongoDB server');
    
    // Get the database
    const db = client.db(dbName);
    
    // Create a collection if it doesn't exist
    const collection = db.collection('forensic_reports');
    
    // Insert a test document
    const testDoc = {
      imageHash: 'test-hash',
      filename: 'test-image.jpg',
      manipulationScore: 75.5,
      detectedRegions: [
        { x: 100, y: 100, width: 200, height: 150, confidence: 0.85 }
      ],
      metadata: {
        analyzer: 'test-script',
        timestamp: new Date()
      },
      createdAt: new Date(),
      updatedAt: new Date()
    };
    
    const result = await collection.insertOne(testDoc);
    console.log(`Inserted test document with ID: ${result.insertedId}`);
    
    // Find the document we just inserted
    const foundDoc = await collection.findOne({ imageHash: 'test-hash' });
    console.log('Found document:');
    console.log(JSON.stringify(foundDoc, null, 2));
    
    // Count documents in the collection
    const count = await collection.countDocuments();
    console.log(`Total documents in collection: ${count}`);
    
  } catch (err) {
    console.error('Error occurred:', err);
  } finally {
    // Close the connection
    await client.close();
    console.log('MongoDB connection closed');
  }
}

main().catch(console.error);