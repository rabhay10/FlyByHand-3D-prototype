import cv2

def test_cameras():
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Index {i} is OPEN")
            ret, frame = cap.read()
            if ret:
                print(f"  Captured frame at {i}")
            cap.release()
        else:
            print(f"Index {i} is closed")

if __name__ == "__main__":
    test_cameras()
