# 🚁 Hand Gesture Drone Controller (3D Simulation)

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-v4.5+-green.svg)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-orange.svg)

A high-performance drone simulation controlled entirely by hand gestures. This project uses **Computer Vision** and **MediaPipe** to detect gestures via webcam, translating them into real-time 3D physics-based drone movements.

---

![unnamed](https://github.com/user-attachments/assets/a0663e34-b145-428d-a3c2-f302bf423c64)

---

## ✨ Features

- **🎮 Intuitive Gesture Control**: Control flight dynamics with simple hand movements.
- **🚀 3D Simulation Engine**: Physics-based flight model with momentum, drag, and gravity.
- **🗺️ Interactive HUD**: Real-time Heads-Up Display showing system status, gesture commands, and control vectors.
- **🏁 Checkerboard Arena**: High-contrast testing environment for spatial orientation.
- **🎥 Dynamic Chase Camera**: Smooth camera following with perspective projection.

---

## 🖐️ Gesture Reference

Navigate the 3D space using the following controls:

| Gesture | Action | Description |
| :--- | :--- | :--- |
| ✊ **FIST** | **TAKEOFF / UP** | Arm the drone and increase altitude |
| ✋ **OPEN PALM** | **LAND / DOWN** | Decrease altitude or land on the ground |
| ☝️ **POINT INDEX** | **FORWARD** | Tilt and move the drone forward |
| ✌️ **PEACE (V)** | **BACKWARD** | Tilt and move the drone backward |
| 🛸 **OTHER** | **HOVER** | Maintain current position with auto-stabilization |

> [!TIP]
> Use a well-lit environment for the best hand tracking performance!

---

## 🛠️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/rabhay10/hand-gesture-drone.git
cd hand-gesture-drone
```

### 2. Install Dependencies
Ensure you have Python 3.8+ installed.
```bash
pip install -r requirements.txt
```

### 3. Run the Simulation
```bash
python main.py
```

---

## 🏗️ Project Structure

- `main.py`: The entry point that integrates gesture detection with the simulation loop.
- `gesture_detector.py`: MediaPipe-powered engine for hand tracking and gesture recognition.
- `virtual_drone.py`: 3D physics engine and rendering logic for the virtual drone.
- `drone_controller.py`: Command abstraction layer (supports both Simulation and Real SDKs).

---

## 🚀 Roadmap

- [ ] **Real Drone Integration**: Connect to DJI Tello or Antigravity SDKs.
- [ ] **Voice Commands**: Hybrid control using speech recognition.
- [ ] **Obstacle Avoidance**: Virtual obstacles within the 3D simulation.
- [ ] **Gesture Customization**: Configurable mapping for user-defined gestures.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
