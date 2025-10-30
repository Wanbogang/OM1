import cv2
import base64
import time
import threading
from opencv_perception_agent import OpenCVPerceptionAgent

class VideoProcessor:
    def __init__(self):
        self.perception_agent = OpenCVPerceptionAgent()
        print("VideoProcessor initialized.")

    def process_video_stream(self, video_path=0):
        """
        Processes video from a file (video_path) or webcam (0).
        Yields detection results for each frame.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error: Could not open video stream.")
            return

        print("Starting video processing... Press 'q' to quit.")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Video stream ended.")
                break

            # 1. Convert frame to base64 for processing by the agent
            _, buffer = cv2.imencode('.jpg', frame)
            frame_b64 = base64.b64encode(buffer).decode('utf-8')

            # 2. Process the frame with the perception agent
            start_time = time.time()
            detection_result = self.perception_agent.detect_disease_base64(frame_b64)
            end_time = time.time()

            # 3. Add processing time information
            detection_result['processing_time_ms'] = (end_time - start_time) * 1000
            
            # 4. Yield the result (in a real app, this would be sent via WebSocket)
            yield detection_result

            # 5. (Optional) Display results on the video frame
            if detection_result.get('detections'):
                for det in detection_result['detections']:
                    x, y, w, h = det['bounding_box']
                    label = det['disease_type']
                    confidence = det['confidence']
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, f"{label}: {confidence:.2f}", (x, y - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            cv2.imshow('SmartFarm Real-time Detection', frame)

            # Exit if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    # For direct testing, run this file
    processor = VideoProcessor()
    for result in processor.process_video_stream(video_path=0):
        print(result)
