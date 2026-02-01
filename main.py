import cv2
import time
import numpy as np
import math
from virtual_drone import VirtualDrone

try:
    from gesture_detector import GestureDetector
except ImportError as e:
    print(f"Error importing gesture_detector: {e}")
    print("Ensure mediapipe and opencv are installed.")
    exit(1)

def main():
    print("Initializing Hand Gesture Drone Controller (3D)...")
    
    # Initialize Camera (Robust selection)
    cap = None
    for idx in [0, 1, 2]:
        print(f"Attempting to open camera index {idx}...")
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            # Check if we can actually read a frame
            ret, _ = cap.read()
            if ret:
                print(f"Successfully opened camera {idx}")
                break
            cap.release()
    
    if cap is None or not cap.isOpened():
        print("Error: Could not open any webcam. Please check permissions or connection.")
        return
    # Initialize Gesture Detector and Drone Controller
    detector = GestureDetector()
    drone = VirtualDrone()
    
    print("\nControls:")
    print("  FIST (Closed)  -> TAKEOFF / MOVE UP")
    print("  OPEN PALM      -> MOVE DOWN / LAND")
    print("  POINT INDEX    -> MOVE FORWARD")
    print("  PEACE (V)      -> MOVE BACKWARD")
    print("  (Other)        -> HOVER")
    print("\nPress 'q' to exit.")

    last_time = time.time()
    
    while True:
        # Time Management
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        success, img = cap.read()
        if not success:
            break

        # Flip image for mirror effect
        img = cv2.flip(img, 1)
        
        # Detect Gesture
        gesture, hand_landmarks, all_hands = detector.detect(img)
        
        # Draw Landmarks (Feedback)
        if all_hands:
            for hand_lms in all_hands:
                detector.drawing_utils.draw_landmarks(img, hand_lms, detector.hands_module.HAND_CONNECTIONS)

        # Control Logic
        inputs = {} # pitch, roll, yaw, throttle
        
        # Logic: FIST = UP, OPEN_PALM = DOWN/LAND
        # To Takeoff, user shows FIST
        
        if gesture == "FIST":
            if not drone.active:
                drone.active = True
                drone.pos[1] = 10 # Jump start
            
            inputs['throttle'] = 1.0 # UP
            
        elif gesture == "OPEN_PALM" or gesture == "OPEN_HAND":
             inputs['throttle'] = -1.0 # DOWN
             # If close to ground, it will land (physics handles ground clamp)
             # To disarm fully, maybe if it sits on ground for a while?
             # For now, just pushing down is fine.
             
        elif gesture == "POINT_INDEX":
            inputs['pitch'] = 0.8 # Forward
            
        elif gesture == "PEACE":
            inputs['pitch'] = -0.8 # Backward
            
        # Implicit Hover for others (PALM LEFT/RIGHT removed commands, act as hover now)

        # Update Physics
        drone.update(dt, inputs)
        
        # Draw 3D Simulation
        sim_img = drone.draw_3d()
        
        # UI Overlay on Camera (Professional FPV HUD)
        h, w, _ = img.shape
        hud_col = (0, 255, 0) # Classic Green HUD
        alpha = 0.6
        overlay = img.copy()

        # --- 1. Artificial Horizon (Center) ---
        cx, cy = w // 2, h // 2
        # Use drone velocity/orientation to tilt horizon (mocked since we don't have true attitude here)
        tilt = -drone.vel[0] * 0.5 
        pitch_off = drone.vel[2] * 0.5
        
        # Horizon Line
        p1 = (int(cx - 100 * math.cos(math.radians(tilt))), int(cy + pitch_off - 100 * math.sin(math.radians(tilt))))
        p2 = (int(cx + 100 * math.cos(math.radians(tilt))), int(cy + pitch_off + 100 * math.sin(math.radians(tilt))))
        cv2.line(overlay, p1, p2, hud_col, 1)
        # Center Crosshair
        cv2.line(overlay, (cx - 20, cy), (cx - 5, cy), hud_col, 2)
        cv2.line(overlay, (cx + 5, cy), (cx + 20, cy), hud_col, 2)
        cv2.line(overlay, (cx, cy - 5), (cx, cy + 5), hud_col, 2)

        # --- 2. Side Tapes (Speed & Altitude) ---
        # Speed Tape (Left)
        cv2.rectangle(overlay, (40, cy-100), (80, cy+100), hud_col, 1)
        speed = np.linalg.norm(drone.vel)
        cv2.putText(overlay, f"{speed:.1f}", (45, cy+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, hud_col, 1)
        cv2.putText(overlay, "SPD", (45, cy-110), cv2.FONT_HERSHEY_SIMPLEX, 0.4, hud_col, 1)

        # Altitude Tape (Right)
        cv2.rectangle(overlay, (w-80, cy-100), (w-40, cy+100), hud_col, 1)
        alt = drone.pos[1]
        cv2.putText(overlay, f"{alt:.1f}", (w-75, cy+5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, hud_col, 1)
        cv2.putText(overlay, "ALT", (w-75, cy-110), cv2.FONT_HERSHEY_SIMPLEX, 0.4, hud_col, 1)

        # --- 3. Status Information (Top) ---
        # System Status
        status_text = "MODE: STABILIZE" if drone.active else "MODE: DISARMED"
        cv2.putText(overlay, status_text, (w//2 - 60, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, hud_col, 2)
        
        # Battery (Mock)
        cv2.rectangle(overlay, (w-100, 30), (w-40, 50), hud_col, 1)
        cv2.rectangle(overlay, (w-98, 32), (w-60, 48), hud_col, -1)
        cv2.putText(overlay, "82%", (w-140, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, hud_col, 1)

        # --- 4. Gesture Feedback (Bottom) ---
        if gesture != "UNKNOWN" and gesture != "OTHER":
            # Glow effect for command
            cv2.rectangle(overlay, (w//2-80, h-60), (w//2+80, h-20), (0, 100, 0), -1)
            cv2.putText(overlay, f"CMD: {gesture}", (w//2-70, h-35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Merge Overlay
        # Realistic Jitter: Add subtle shake to the HUD when high speed/active
        if drone.active:
            jitter_x = int(np.random.normal(0, 1) * (speed / 10.0))
            jitter_y = int(np.random.normal(0, 1) * (speed / 10.0))
            # Shift the overlay slightly
            M = np.float32([[1, 0, jitter_x], [0, 1, jitter_y]])
            overlay = cv2.warpAffine(overlay, M, (w, h))

        # Combine views side-by-side for guaranteed visibility
        # Both should be 640x480
        combined_img = np.hstack((img, sim_img))
        
        # Add a professional border/divider
        cv2.line(combined_img, (w, 0), (w, h), (50, 50, 50), 2)
        
        cv2.imshow("Drone Control Center (FPV + 3D)", combined_img)
        
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
