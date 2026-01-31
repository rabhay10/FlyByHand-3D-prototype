import time
import cv2
import numpy as np

class DroneController:
    def __init__(self):
        self.mock = False
        self.drone = None
        try:
            import antigravity_sdk
            self.drone = antigravity_sdk.Drone()
            self.drone.connect()
            print("Connected to Antigravity Drone SDK.")
        except ImportError:
            print("Antigravity SDK not found. Using Mock Drone with Virtual Simulation.")
            self.mock = True
            self.drone = MockDrone()
            self.drone.connect()

    def execute(self, command):
        if not command:
            return
            
        # Execute command on the underlying drone instance (real or mock)
        if command == "TAKEOFF":
            self.drone.takeoff()
        elif command == "LAND":
            self.drone.land()
        elif command == "MOVE_FORWARD":
            self.drone.move_forward()
        elif command == "MOVE_BACKWARD":
            self.drone.move_backward()
        elif command == "ROTATE_LEFT":
            self.drone.rotate_left()
        elif command == "ROTATE_RIGHT":
            self.drone.rotate_right()
        elif command == "HOVER" or command == "STOP":
            self.drone.hover()
            
    def emergency_stop(self):
        print("EMERGENCY STOP / HOVER")
        if self.drone:
            self.drone.hover()


class MockDrone:
    def __init__(self):
        # Virtual drone position and canvas
        self.x, self.y = 300, 300
        self.active = False # Drone on ground initially
        self.canvas_size = 600
        self.canvas = np.zeros((self.canvas_size, self.canvas_size, 3), dtype=np.uint8)
        self.window_name = "Virtual Drone Simulation"
        self.headless = False
        try:
            # Initialize window
            cv2.namedWindow(self.window_name)
        except cv2.error as e:
            print(f"[WARNING] OpenCV GUI not available: {e}")
            print("[INFO] Running in HEADLESS mode. Virtual drone will be console-only.")
            self.headless = True

    def _update_canvas(self, command):
        # Only move if active (flying) or if the command is takeoff
        if self.active:
            if command == "MOVE_FORWARD":
                self.y -= 20
            elif command == "MOVE_BACKWARD":
                self.y += 20
            elif command == "ROTATE_LEFT":
                self.x -= 20
            elif command == "ROTATE_RIGHT":
                self.x += 20
        
        # Keep drone inside canvas
        self.x = max(20, min(self.canvas_size - 20, self.x))
        self.y = max(20, min(self.canvas_size - 20, self.y))

        if self.headless:
            return

        # Update visuals
        self.canvas[:] = (30, 30, 30) # Dark gray background
        
        # Draw "Ground" grid if on ground, or "Sky" if flying? 
        # Simple Circle for drone
        color = (0, 255, 0) if self.active else (0, 0, 255) # Green if flying, Red if grounded
        cv2.circle(self.canvas, (self.x, self.y), 20, color, -1)
        
        # Draw Direction indicator (front of drone) - assuming UP is "Forward" basics
        cv2.line(self.canvas, (self.x, self.y), (self.x, self.y - 30), (255, 255, 0), 2)

        # Status Text
        status_text = f"Status: {'FLYING' if self.active else 'GROUNDED'}"
        cmd_text = f"Last Cmd: {command}"
        
        cv2.putText(self.canvas, status_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(self.canvas, cmd_text, (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        if not self.headless:
            cv2.imshow(self.window_name, self.canvas)
            cv2.waitKey(1)

    def connect(self):
        print("[MOCK] Connecting to drone...")
        time.sleep(0.5)
        print("[MOCK] Connected!")
        self._update_canvas("CONNECT")

    def takeoff(self):
        if not self.active:
            print("[MOCK] 🚁 TAKEOFF")
            self.active = True
            self._update_canvas("TAKEOFF")
        else:
            print("[MOCK] Already flying")

    def land(self):
        if self.active:
            print("[MOCK] 🛬 LAND")
            self.active = False
            self._update_canvas("LAND")
        else:
            print("[MOCK] Already on ground")

    def move_forward(self):
        print("[MOCK] ⬆️ Moving FORWARD")
        self._update_canvas("MOVE_FORWARD")

    def move_backward(self):
        print("[MOCK] ⬇️ Moving BACKWARD")
        self._update_canvas("MOVE_BACKWARD")

    def rotate_left(self):
        print("[MOCK] ⬅️ Rotating LEFT")
        self._update_canvas("ROTATE_LEFT")

    def rotate_right(self):
        print("[MOCK] ➡️ Rotating RIGHT")
        self._update_canvas("ROTATE_RIGHT")

    def hover(self):
        print("[MOCK] 🛑 HOVERING")
        self._update_canvas("HOVER")
