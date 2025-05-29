import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, Row, Col, Alert, Spinner, Button, Tabs, Tab } from 'react-bootstrap';
import { getReport } from '../services/api';
import '../styles/HeatMap.css';

const ReportDetail = () => {
  // Helper function to fix image URLs
  const fixImageUrl = (url) => {
    if (!url) return '';
    // The proxy will handle the localhost:8080 part
    return url;
  };
  const { hash } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        
        // Check localStorage for the report
        const storedReports = JSON.parse(localStorage.getItem('forensicReports') || '[]');
        const existingReport = storedReports.find(r => r.hash === hash);
        
        if (existingReport) {
          console.log('Found report in localStorage:', existingReport);
        } else {
          console.log('Report not found in storage, fetching from API...');
        }
        
        // Fetch the report data from the API
        const data = await getReport(hash);
        
        if (!data) {
          // If the API doesn't return data but we have a stored report, we can still show some information
          if (existingReport) {
            const reportInfo = existingReport;
            setError('Report data is not fully available yet, but we found some basic information.');
            setReport({
              id: hash,
              sourceURL: reportInfo.url,
              displayImage: reportInfo.fileUrl || reportInfo.url,
              status: "Processing",
              // Add placeholder data for the reports
              elaReport: { completed: false },
              dqReport: { completed: false },
              ghostReport: { completed: false, maps: [] },
              metadataStringReport: JSON.stringify({ completed: false }),
              metadataObjectReport: { completed: false },
              thumbnailReport: { numberOfThumbnails: 0, thumbnailList: [] }
            });
          } else {
            setError('Report not found. The report may still be processing or the hash is invalid.');
          }
          setLoading(false);
          return;
        }
        
        setReport(data);
        
        // Store in localStorage if not already there
        
        // Also store in localStorage for the ReportList component as a fallback
        if (!existingReport && data.sourceURL) {
          const newReport = {
            hash,
            url: data.sourceURL,
            date: new Date().toISOString()
          };
          localStorage.setItem('forensicReports', JSON.stringify([newReport, ...storedReports]));
        }
      } catch (err) {
        setError('Failed to load report. This is likely due to the mock API implementation.');
        console.error('Error fetching report:', err);
        
        // Check if we have a stored report to show basic information
        const storedReports = JSON.parse(localStorage.getItem('forensicReports') || '[]');
        const existingReport = storedReports.find(r => r.hash === hash);
        
        if (existingReport) {
          const reportInfo = existingReport;
          setReport({
            id: hash,
            sourceURL: reportInfo.url,
            displayImage: reportInfo.fileUrl || reportInfo.url,
            status: "Error",
            // Add placeholder data for the reports
            elaReport: { completed: false },
            dqReport: { completed: false },
            ghostReport: { completed: false, maps: [] },
            metadataStringReport: JSON.stringify({ completed: false }),
            metadataObjectReport: { completed: false },
            thumbnailReport: { numberOfThumbnails: 0, thumbnailList: [] }
          });
        }
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [hash]);

  if (loading) {
    return (
      <div className="text-center mt-5">
        <Spinner animation="border" role="status">
          <span className="sr-only">Loading...</span>
        </Spinner>
      </div>
    );
  }

  if (error) {
    return <Alert variant="danger">{error}</Alert>;
  }

  if (!report) {
    return <Alert variant="warning">Report not found</Alert>;
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Forensic Analysis Report</h2>
        <Button as={Link} to="/reports" variant="outline-secondary">Back to Reports</Button>
      </div>
      
      <Card className="mb-4">
        <Card.Body>
          <Row>
            <Col md={6}>
              <h5>Image Information</h5>
              <p><strong>Source URL:</strong> <a href={report.sourceURL} target="_blank" rel="noopener noreferrer">{report.sourceURL}</a></p>
              <p><strong>Hash:</strong> {hash}</p>
              <p><strong>Status:</strong> {report.status}</p>
            </Col>
            <Col md={6}>
              {report.displayImage && (
                <img
                  src={fixImageUrl(report.displayImage)}
                  alt="Original"
                  className="img-fluid"
                  style={{ maxHeight: '300px' }}
                />
              )}
            </Col>
          </Row>
        </Card.Body>
      </Card>
      
      <Tabs defaultActiveKey="ela" id="analysis-tabs" className="mb-3">
        <Tab eventKey="ela" title="Error Level Analysis">
          <Card>
            <Card.Body>
              <h5>Error Level Analysis (ELA)</h5>
              <p className="heat-map-description">ELA highlights differences in compression levels by resaving the image at a known quality and calculating the difference. Manipulated regions may appear as areas with different error levels compared to the rest of the image. Bright areas often indicate recent edits or manipulations.</p>
              {report.elaReport && report.elaReport.completed ? (
                <div className="heat-map-container">
                  <img src={fixImageUrl(report.elaReport.map)} alt="ELA Analysis" className="analysis-image" />
                  <div className="heat-map-info">
                    <span className="heat-map-info-item"><strong>Min Value:</strong> {report.elaReport.minvalue}</span>
                    <span className="heat-map-info-item"><strong>Max Value:</strong> {report.elaReport.maxValue}</span>
                  </div>
                </div>
              ) : (
                <Alert variant="warning">ELA analysis not available</Alert>
              )}
            </Card.Body>
          </Card>
        </Tab>
        
        <Tab eventKey="dq" title="Double Quantization">
          <Card>
            <Card.Body>
              <h5>Double JPEG Quantization (DQ)</h5>
              <p className="heat-map-description">DQ analysis detects areas that have been compressed multiple times with different quality settings. When an image is edited and resaved, the newly modified regions will have different compression artifacts than the original areas. Inconsistent quantization patterns can reveal spliced content or localized edits.</p>
              {report.dqReport && report.dqReport.completed ? (
                <div className="heat-map-container">
                  <img src={fixImageUrl(report.dqReport.map)} alt="DQ Analysis" className="analysis-image" />
                  <div className="heat-map-info">
                    <span className="heat-map-info-item"><strong>Min Value:</strong> {report.dqReport.minvalue}</span>
                    <span className="heat-map-info-item"><strong>Max Value:</strong> {report.dqReport.maxValue}</span>
                  </div>
                </div>
              ) : (
                <Alert variant="warning">DQ analysis not available</Alert>
              )}
            </Card.Body>
          </Card>
        </Tab>
        
        <Tab eventKey="noise" title="Noise Analysis">
          <Card>
            <Card.Body>
              <h5>Noise Analysis</h5>
              <p className="heat-map-description">Noise analysis examines the natural noise patterns present in all digital images. When content is manipulated, the noise characteristics often change. This analysis highlights areas with inconsistent noise patterns that may indicate splicing, cloning, or other manipulations. Different cameras and editing software leave distinctive noise signatures.</p>
              {report.dwNoiseReport && report.dwNoiseReport.completed ? (
                <div className="heat-map-container">
                  <img src={fixImageUrl(report.dwNoiseReport.map)} alt="Noise Analysis" className="analysis-image" />
                  <div className="heat-map-info">
                    <span className="heat-map-info-item"><strong>Min Value:</strong> {report.dwNoiseReport.minValue}</span>
                    <span className="heat-map-info-item"><strong>Max Value:</strong> {report.dwNoiseReport.maxvalue}</span>
                  </div>
                </div>
              ) : (
                <Alert variant="warning">Noise analysis not available</Alert>
              )}
            </Card.Body>
          </Card>
        </Tab>
        
        <Tab eventKey="ghost" title="Ghost Analysis">
          <Card>
            <Card.Body>
              <h5>Ghost Analysis</h5>
              <p className="heat-map-description">Ghost analysis can reveal traces of content that has been removed or altered in an image. By analyzing compression artifacts at different quality levels, this technique can detect "ghosts" of previous content that remain in the image data. It's particularly effective at finding areas where objects have been removed through cloning, healing, or content-aware fill tools.</p>
              {report.ghostReport && report.ghostReport.completed && report.ghostReport.maps.length > 0 ? (
                <div>
                  {report.ghostReport.maps.map((map, index) => (
                    <div key={index} className="heat-map-container">
                      <h6>Ghost Map {index + 1}</h6>
                      <img src={fixImageUrl(map)} alt={`Ghost Analysis ${index + 1}`} className="analysis-image" />
                      <div className="heat-map-info">
                        <span className="heat-map-info-item"><strong>Quality:</strong> {report.ghostReport.qualities[index]}</span>
                        <span className="heat-map-info-item"><strong>Difference:</strong> {report.ghostReport.differences[index]}</span>
                        <span className="heat-map-info-item"><strong>Min Value:</strong> {report.ghostReport.minValues[index]}</span>
                        <span className="heat-map-info-item"><strong>Max Value:</strong> {report.ghostReport.maxValues[index]}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <Alert variant="warning">Ghost analysis not available</Alert>
              )}
            </Card.Body>
          </Card>
        </Tab>
        
        <Tab eventKey="blocking" title="Blocking Artifacts">
          <Card>
            <Card.Body>
              <h5>Blocking Artifacts Analysis</h5>
              <p className="heat-map-description">Blocking analysis detects JPEG compression artifacts that appear as visible blocks in the image. JPEG compression divides images into 8x8 pixel blocks, which can become visible at low quality settings. This analysis highlights inconsistencies in blocking patterns that may indicate manipulation. Areas with different blocking characteristics often reveal spliced content from different sources.</p>
              {report.blockingReport && report.blockingReport.completed ? (
                <div className="heat-map-container">
                  <img src={fixImageUrl(report.blockingReport.map)} alt="Blocking Analysis" className="analysis-image" />
                  <div className="heat-map-info">
                    <span className="heat-map-info-item"><strong>Min Value:</strong> {report.blockingReport.minValue}</span>
                    <span className="heat-map-info-item"><strong>Max Value:</strong> {report.blockingReport.maxValue}</span>
                  </div>
                </div>
              ) : (
                <Alert variant="warning">Blocking analysis not available</Alert>
              )}
            </Card.Body>
          </Card>
        </Tab>
        
        <Tab eventKey="median" title="Median Noise">
          <Card>
            <Card.Body>
              <h5>Median Noise Analysis</h5>
              <p className="heat-map-description">Median noise analysis applies a median filter to the image and examines the residual noise patterns. This technique is effective at detecting localized inconsistencies in noise that may indicate manipulation. Areas that have been smoothed, cloned, or artificially generated often show different median noise characteristics compared to authentic regions of the image.</p>
              {report.medianNoiseReport && report.medianNoiseReport.completed ? (
                <div className="heat-map-container">
                  <img src={fixImageUrl(report.medianNoiseReport.map)} alt="Median Noise Analysis" className="analysis-image" />
                  <div className="heat-map-info">
                    <span className="heat-map-info-item"><strong>Min Value:</strong> {report.medianNoiseReport.minValue}</span>
                    <span className="heat-map-info-item"><strong>Max Value:</strong> {report.medianNoiseReport.maxvalue}</span>
                  </div>
                </div>
              ) : (
                <Alert variant="warning">Median noise analysis not available</Alert>
              )}
            </Card.Body>
          </Card>
        </Tab>
        
        <Tab eventKey="grids" title="Grids Analysis">
          <Card>
            <Card.Body>
              <h5>Grids Analysis</h5>
              <p className="heat-map-description">Grids analysis examines the alignment of JPEG compression blocks across the image. When content is copied from one image to another, the 8x8 pixel grid patterns may not align perfectly with the destination image's grid. This analysis highlights grid misalignments that can reveal spliced content, even when other visual evidence has been carefully concealed.</p>
              {report.gridsReport && report.gridsReport.completed ? (
                <div className="heat-map-container">
                  <img src={fixImageUrl(report.gridsReport.map)} alt="Grids Analysis" className="analysis-image" />
                  <div className="heat-map-info">
                    <span className="heat-map-info-item"><strong>Min Value:</strong> {report.gridsReport.minValue}</span>
                    <span className="heat-map-info-item"><strong>Max Value:</strong> {report.gridsReport.maxValue}</span>
                  </div>
                </div>
              ) : (
                <Alert variant="warning">Grids analysis not available</Alert>
              )}
            </Card.Body>
          </Card>
        </Tab>
        
        <Tab eventKey="gridsInversed" title="Grids Inversed">
          <Card>
            <Card.Body>
              <h5>Grids Inversed Analysis</h5>
              <p className="heat-map-description">Grids inversed analysis provides an alternative visualization of JPEG grid inconsistencies. This technique inverts the grid pattern analysis to highlight different aspects of potential manipulation. When used in conjunction with the standard Grids Analysis, it can reveal subtle artifacts that might be missed in a single view. Areas with unusual patterns in both analyses are particularly suspicious.</p>
              {report.gridsInversedReport && report.gridsInversedReport.completed ? (
                <div className="heat-map-container">
                  <img src={fixImageUrl(report.gridsInversedReport.map)} alt="Grids Inversed Analysis" className="analysis-image" />
                  <div className="heat-map-info">
                    <span className="heat-map-info-item"><strong>Min Value:</strong> {report.gridsInversedReport.minValue}</span>
                    <span className="heat-map-info-item"><strong>Max Value:</strong> {report.gridsInversedReport.maxValue}</span>
                  </div>
                </div>
              ) : (
                <Alert variant="warning">Grids inversed analysis not available</Alert>
              )}
            </Card.Body>
          </Card>
        </Tab>
        
        <Tab eventKey="metadata" title="Metadata">
          <Card>
            <Card.Body>
              <h5>Image Metadata</h5>
              <p className="heat-map-description">Metadata provides valuable information about the image's origin and processing history. This includes camera make and model, capture settings (aperture, shutter speed, ISO), GPS coordinates if available, software used for editing, and timestamps. Inconsistencies in metadata can reveal manipulation, while missing metadata may indicate it was deliberately stripped to hide evidence of editing.</p>
              {report.metadataObjectReport ? (
                <div>
                  <pre className="bg-light p-3" style={{ maxHeight: '400px', overflow: 'auto' }}>
                    {JSON.stringify(report.metadataObjectReport, null, 2)}
                  </pre>
                </div>
              ) : (
                <Alert variant="warning">Metadata not available</Alert>
              )}
            </Card.Body>
          </Card>
        </Tab>
      </Tabs>
    </div>
  );
};

export default ReportDetail;