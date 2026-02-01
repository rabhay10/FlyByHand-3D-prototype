import cv2
import mediapipe as mp
import math
from collections import deque, Counter

class GestureDetector:
    def __init__(self, max_hands=1, detection_confidence=0.7, tracking_confidence=0.5):
        # Use mediapipe.solutions.hands directly from mp
        self.hands_detector = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )
        self.drawing_utils = mp.solutions.drawing_utils
        self.hands_module = mp.solutions.hands  # HAND_CONNECTIONS lives here
        
        # Gesture smoothing
        self.history_size = 5
        self.gesture_history = deque(maxlen=self.history_size)

    def find_hands(self, image, draw=True):
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.hands_detector.process(img_rgb)
        if draw and results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.drawing_utils.draw_landmarks(
                    image, hand_landmarks, self.hands_module.HAND_CONNECTIONS
                )
        return results

    def get_landmark_positions(self, image, hand_no=0):
        lm_list = []
        results = self.find_hands(image, draw=False)
        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[hand_no]
            h, w, _ = image.shape
            for id, lm in enumerate(hand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                lm_list.append((id, cx, cy))
        return lm_list

    def fingers_up(self, image, hand_no=0):
        lm_list = self.get_landmark_positions(image, hand_no)
        fingers = []
        if not lm_list:
            return [0,0,0,0,0]
        # Thumb
        fingers.append(1 if lm_list[4][1] > lm_list[3][1] else 0)
        # Fingers
        for tip_id in [8,12,16,20]:
            fingers.append(1 if lm_list[tip_id][2] < lm_list[tip_id-2][2] else 0)
        return fingers

    def detect(self, img):
        """
        Detects hand gestures in the provided image.
        Returns:
            gesture (str): The detected gesture name.
            hand_landmarks (list): List of landmarks for the detected hand.
            results (object): MediaPipe results object.
        """
        results = self.find_hands(img)
        gesture = "UNKNOWN"
        lm_list = []

        if results.multi_hand_landmarks:
            lm_list = self.get_landmark_positions(img, hand_no=0)
            if lm_list:
                fingers = self.fingers_up(img, hand_no=0)
                finger_count = sum(fingers)
                
                # Hand Orientation (Wrist vs Middle Finger MCP)
                # 0: Wrist, 9: Middle Finger MCP
                wrist_y = lm_list[0][2]
                middle_mcp_y = lm_list[9][2]
                
                # Basic definitions
                is_fist = (finger_count <= 0) # Strict fist
                is_open = (finger_count >= 4)
                
                # 1. FIST -> TAKEOFF / LAND
                if is_fist:
                    gesture = "FIST"
                
                # 2. OPEN PALM (Hover / Tilt)
                elif is_open:
                    start = lm_list[0] # Wrist
                    end = lm_list[12] # Middle tip
                    dy = start[2] - end[2]
                    dx = end[1] - start[1]
                    angle = math.degrees(math.atan2(dy, dx))
                    
                    if angle > 110:
                        gesture = "PALM_LEFT"
                    elif angle < 70:
                        gesture = "PALM_RIGHT"
                    else:
                        gesture = "OPEN_PALM"

                # 3. PEACE (Backward) - Check before Index/Thumb
                elif fingers == [0, 1, 1, 0, 0] or fingers == [1, 1, 1, 0, 0]:
                    gesture = "PEACE"

                # 4. INDEX / POINT (Forward)
                # Allow [1,1,0,0,0] (Thumb+Index) to count as Point IF index is clearly primary
                elif fingers == [0, 1, 0, 0, 0] or fingers == [1, 1, 0, 0, 0]:
                    # If thumb AND index are up, check which is higher/dominant?
                    # Usually "Gun" gesture -> Point forward
                    gesture = "POINT_INDEX"
                else:
                    gesture = "OTHER"

        # Apply smoothing
        if gesture != "UNKNOWN":
            self.gesture_history.append(gesture)
        
        if len(self.gesture_history) >= 3:
            # Return the most frequent gesture in history for stability
            counts = Counter(self.gesture_history)
            stable_gesture = counts.most_common(1)[0][0]
            # Only switch if we have clear majority or it's been several frames
            if counts[stable_gesture] >= 3:
                gesture = stable_gesture
        
        # Return a list of landmarks for checking in main (to match main's expectance of iterating)
        all_landmarks = results.multi_hand_landmarks if results.multi_hand_landmarks else []
        return gesture, lm_list, all_landmarks

    def get_hand_center(self, img):
        """
        Returns the normalized center (x, y) of the hand relative to the image center.
        Range: -1.0 (Left/Top) to 1.0 (Right/Bottom)
        """
        lm_list = self.get_landmark_positions(img, hand_no=0)
        if not lm_list:
            return None
        
        # Use simple average of 0 (wrist), 5 (index), 17 (pinky) for stable center
        x_avg = (lm_list[0][1] + lm_list[5][1] + lm_list[17][1]) / 3
        y_avg = (lm_list[0][2] + lm_list[5][2] + lm_list[17][2]) / 3
        
        h, w, _ = img.shape
        
        # Normalize to -1 to 1 range
        # Center of image is (0,0)
        norm_x = (x_avg - w/2) / (w/2)
        norm_y = (y_avg - h/2) / (h/2)
        
        return (norm_x, norm_y)
