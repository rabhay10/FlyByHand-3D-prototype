import mediapipe as mp
import math

class GestureDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils

    def detect(self, image):
        """
        Processes the image and returns the gesture name and landmarks.
        """
        image_rgb = image  # Assumes image is already RGB
        results = self.hands.process(image_rgb)
        
        gesture = "None"
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Only process the first hand detected
                gesture = self._analyze_landmarks(hand_landmarks)
                return gesture, hand_landmarks, results.multi_hand_landmarks
        
        return "None", None, None

    def _analyze_landmarks(self, landmarks):
        """
        Analyzes landmarks to determine specific gestures.
        """
        lms = landmarks.landmark
        
        # Fingers state (up/down)
        index_up = lms[8].y < lms[6].y
        middle_up = lms[12].y < lms[10].y
        ring_up = lms[16].y < lms[14].y
        pinky_up = lms[20].y < lms[18].y

        raised_fingers = [index_up, middle_up, ring_up, pinky_up]
        num_raised = sum(raised_fingers)

        # FIST
        if num_raised == 0:
            return "FIST"

        # OPEN HAND
        if num_raised == 4:
            if self._is_thumb_extended(lms):
                return "OPEN_HAND"
            return "OPEN_HAND"

        # INDEX UP
        if index_up and not middle_up and not ring_up and not pinky_up:
            return "INDEX_UP"

        # INDEX + MIDDLE UP (Peace)
        if index_up and middle_up and not ring_up and not pinky_up:
            return "INDEX_MIDDLE_UP"

        # THUMB LEFT / RIGHT
        if not index_up and not middle_up and not ring_up and not pinky_up:
            wrist = lms[0]
            thumb_tip = lms[4]
            if abs(thumb_tip.x - wrist.x) > 0.1:  # Extended
                if thumb_tip.x < wrist.x:
                    return "THUMB_LEFT"
                else:
                    return "THUMB_RIGHT"

        return "UNKNOWN"

    def _is_thumb_extended(self, lms):
        # Distance between thumb tip and index MCP
        return math.hypot(lms[4].x - lms[5].x, lms[4].y - lms[5].y) > 0.1
