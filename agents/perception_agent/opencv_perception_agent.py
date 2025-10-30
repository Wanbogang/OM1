import cv2
import numpy as np
import base64
import logging
from prisma import Prisma

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OpenCVPerceptionAgent:
    def __init__(self):
        self.db = Prisma()
        logging.info("OpenCVPerceptionAgent initialized.")

    def process_image(self, image):
        """Main processing pipeline for disease detection."""
        try:
            # 1. Preprocessing
            processed_image = self.preprocess(image)
            
            # 2. Disease Detection
            detections = self.detect_disease(processed_image)
            
            # 3. Plant Health Analysis
            health_analysis = self.analyze_plant_health(processed_image)
            
            # 4. Compile Results
            result = {
                'detections': detections,
                'plant_health_coverage': health_analysis,
                'summary': self.generate_summary(detections, health_analysis)
            }
            
            return result
            
        except Exception as e:
            logging.error(f"Error in image processing: {e}")
            return {'error': str(e)}

    def preprocess(self, image):
        """Image preprocessing pipeline."""
        # Convert to HSV color space for better color segmentation
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(hsv, (5, 5), 0)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        lab = cv2.cvtColor(blurred, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return enhanced

    def detect_disease(self, image):
        """Detect diseases using color and shape analysis."""
        detections = []
        
        # Define color ranges for different diseases
        disease_ranges = {
            'leaf_blight': {
                'lower': np.array([10, 50, 50]),
                'upper': np.array([30, 255, 255])
            },
            'pest_damage': {
                'lower': np.array([0, 100, 100]),
                'upper': np.array([10, 255, 255])
            },
            'fungal_infection': {
                'lower': np.array([20, 100, 100]),
                'upper': np.array([40, 255, 255])
            },
            'bacterial_spot': {
                'lower': np.array([35, 50, 50]),
                'upper': np.array([85, 255, 255])
            },
            'viral_mosaic': {
                'lower': np.array([40, 40, 40]),
                'upper': np.array([80, 255, 255])
            }
        }
        
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        for disease_name, color_range in disease_ranges.items():
            # Create mask for disease color range
            mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
            
            # Apply morphological operations to clean up the mask
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Filter contours by area
                area = cv2.contourArea(contour)
                if area > 100:  # Minimum area threshold
                    # Get bounding box
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Calculate confidence based on area and shape
                    confidence = self.calculate_confidence(contour, area)
                    
                    # Determine severity
                    severity = self.determine_severity(area, image.shape[:2])
                    
                    detections.append({
                        'disease_type': disease_name,
                        'confidence': confidence,
                        'severity': severity,
                        'bounding_box': [x, y, w, h]
                    })
        
        return detections

    def calculate_confidence(self, contour, area):
        """Calculate confidence score based on multiple factors."""
        # Factor 1: Area (larger areas have higher confidence)
        area_score = min(area / 1000.0, 1.0)
        
        # Factor 2: Shape (more circular shapes have higher confidence)
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            return 0.0
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        shape_score = circularity
        
        # Factor 3: Aspect ratio
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h
        aspect_score = 1.0 - abs(1.0 - aspect_ratio)
        
        # Combine scores
        confidence = (area_score * 0.5 + shape_score * 0.3 + aspect_score * 0.2)
        return min(confidence, 0.98)  # Cap at 98%

    def determine_severity(self, area, image_shape):
        """Determine severity based on affected area."""
        image_area = image_shape[0] * image_shape[1]
        affected_percentage = (area / image_area) * 100
        
        if affected_percentage < 5:
            return 'low'
        elif affected_percentage < 15:
            return 'medium'
        else:
            return 'high'

    def analyze_plant_health(self, image):
        """Analyze overall plant health."""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define healthy green color range
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        
        # Create mask for healthy areas
        healthy_mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # Calculate percentages
        total_pixels = image.shape[0] * image.shape[1]
        healthy_pixels = cv2.countNonZero(healthy_mask)
        healthy_percentage = (healthy_pixels / total_pixels) * 100
        
        return {
            'healthy_percentage': healthy_percentage,
            'unhealthy_percentage': 100 - healthy_percentage
        }

    def generate_summary(self, detections, health_analysis):
        """Generate a summary of the analysis."""
        if not detections:
            return {
                'status': 'healthy',
                'message': 'No diseases detected. Plant appears healthy.',
                'recommendations': ['Continue regular monitoring', 'Maintain proper watering and nutrition']
            }
        
        # Count disease types
        disease_counts = {}
        for detection in detections:
            disease = detection['disease_type']
            disease_counts[disease] = disease_counts.get(disease, 0) + 1
        
        # Get most severe disease
        most_severe = max(detections, key=lambda x: x['confidence'])
        
        return {
            'status': 'disease_detected',
            'diseases_found': list(disease_counts.keys()),
            'primary_disease': most_severe['disease_type'],
            'confidence': most_severe['confidence'],
            'severity': most_severe['severity'],
            'recommendations': self.get_recommendations(most_severe['disease_type'])
        }

    def get_recommendations(self, disease_type):
        """Get treatment recommendations for detected disease."""
        recommendations = {
            'leaf_blight': [
                'Apply appropriate fungicide',
                'Remove affected leaves',
                'Improve air circulation'
            ],
            'pest_damage': [
                'Apply organic or chemical pesticides',
                'Remove pests manually if possible',
                'Use beneficial insects'
            ],
            'fungal_infection': [
                'Apply fungicide treatment',
                'Reduce humidity levels',
                'Remove infected plant parts'
            ],
            'bacterial_spot': [
                'Apply copper-based bactericide',
                'Avoid overhead watering',
                'Remove infected plants'
            ],
            'viral_mosaic': [
                'Remove infected plants immediately',
                'Control aphids and other vectors',
                'Use virus-resistant varieties'
            ]
        }
        return recommendations.get(disease_type, ['Consult with agricultural expert'])

    # --- Base64 Processing ---
    def base64_to_image(self, base64_string):
        """Convert base64 string to OpenCV image."""
        try:
            # Remove header if present
            if 'base64,' in base64_string:
                base64_string = base64_string.split('base64,')[1]
            
            # Decode
            img_data = base64.b64decode(base64_string)
            nparr = np.frombuffer(img_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Could not decode image from base64 string")
                
            return image
        except Exception as e:
            logging.error(f"Error converting base64 to image: {e}")
            raise

    def detect_disease_base64(self, image_b64):
        """Process image from base64 string."""
        try:
            image = self.base64_to_image(image_b64)
            result_json = self.process_image(image)
            return result_json
        except Exception as e:
            logging.error(f"Error in base64 processing: {e}")
            return {'error': str(e)}

    # --- Database Interaction ---
    async def save_detection_to_db(self, detection_result):
        """Saves detection results to the database."""
        try:
            await self.db.connect()
            
            for det in detection_result.get('detections', []):
                await self.db.detectionanalytics.create(
                    data={
                        'disease_type': det['disease_type'],
                        'confidence': det['confidence'],
                        'severity': det['severity'],
                        'coordinates': str(det['bounding_box']),
                        'plant_health': detection_result.get('plant_health_coverage', {}).get('healthy_percentage', 0.0),
                        'processing_time_ms': detection_result.get('processing_time_ms')
                    }
                )
            print(f"✅ Saved {len(detection_result.get('detections', []))} detection(s) to DB.")
        except Exception as e:
            print(f"❌ Error saving to DB: {e}")
        finally:
            await self.db.disconnect()
