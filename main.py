import cv2
import time
from drone_controller import DroneController
try:
    from gesture_detector import GestureDetector
except ImportError as e:
    print(f"Error importing gesture_detector: {e}")
    print("Ensure mediapipe and opencv are installed.")
    exit(1)

def main():
    print("Initializing Hand Gesture Drone Controller...")
    
    # Initialize Camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # Initialize Gesture Detector and Drone Controller
    detector = GestureDetector()
    drone = DroneController()
    
    print("\nControls:")
    print("  FIST          -> TAKEOFF")
    print("  OPEN HAND     -> LAND")
    print("  INDEX UP      -> MOVE FORWARD")
    print("  PEACE (V)     -> MOVE BACKWARD")
    print("  THUMB LEFT    -> ROTATE LEFT")
    print("  THUMB RIGHT   -> ROTATE RIGHT")
    print("  (Any other)   -> HOVER")
    print("\nPress 'q' to exit.")

    last_command_time = 0
    command_cooldown = 0.5  # Seconds between commands to prevent flooding
    current_command = "HOVER"

    while True:
        success, img = cap.read()
        if not success:
            break

        # Flip image for mirror effect
        img = cv2.flip(img, 1)
        
        # Detect Gesture
        gesture, hand_landmarks, all_hands = detector.detect(img)
        
        # Draw Landmarks
        if all_hands:
            for hand_lms in all_hands:
                detector.mp_draw.draw_landmarks(img, hand_lms, detector.mp_hands.HAND_CONNECTIONS)

        # Map Gesture to Command
        command = "HOVER" # Default safe state
        
        if gesture == "FIST":
            command = "TAKEOFF"
        elif gesture == "OPEN_HAND":
            command = "LAND"
        elif gesture == "INDEX_UP":
            command = "MOVE_FORWARD"
        elif gesture == "INDEX_MIDDLE_UP":
            command = "MOVE_BACKWARD"
        elif gesture == "THUMB_LEFT":
            command = "ROTATE_LEFT"
        elif gesture == "THUMB_RIGHT":
            command = "ROTATE_RIGHT"
        
        # Execute Command (with crude rate limiting for repetitive commands, though execute handles it fine)
        # We'll send it every frame or map it? 
        # Sending every frame might flood logs, but good for continuous movement in simulation.
        # drone.execute handles logic.
        
        # Only print change or every X seconds?
        # Let's just execute. The MockDrone prints are fine, logic might need debouncing for TAKE OFF/LAND.
        
        # Execute
        drone.execute(command)

        # UI Overlay
        cv2.putText(img, f"Gesture: {gesture}", (10, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 3)
        cv2.putText(img, f"Command: {command}", (10, 90), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 3)
        
        cv2.imshow("Hand Gesture Controller", img)
        
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    drone.emergency_stop()

if __name__ == "__main__":
    main()
