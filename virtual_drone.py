import cv2
import numpy as np
import math

class VirtualDrone:
    def __init__(self):
        # 3D State
        self.pos = np.array([0.0, 50.0, 0.0])
        self.vel = np.array([0.0, 0.0, 0.0])
        self.yaw = 0.0
        self.prop_angle = 0.0
        self.cam_pos = np.array([0.0, 150.0, -300.0]) # Initial camera position
        self.time = 0.0 # For animations
        
        # Physics Constants
        self.MAX_SPEED = 30.0
        self.ACCEL = 40.0
        self.DRAG = 2.5  # Higher drag for more "viscous" / stable feel
        self.YAW_SPEED = 120.0
        
        self.active = False
        self.target_prop_speed = 0.0
        self.current_prop_speed = 0.0
        
        # 3D Model Definition (Small Drone)
        # Scaled down by ~50% from previous
        # 1. Fuselage
        w, h, l = 5, 3, 8
        self.fuselage = np.array([
            [w, h, l], [w, h, -l], [w, -h, l], [w, -h, -l],
            [-w, h, l], [-w, h, -l], [-w, -h, l], [-w, -h, -l]
        ])
        
        # 2. Arms
        arm_len = 25
        self.arms = np.array([
            [arm_len, 0, arm_len],   
            [arm_len, 0, -arm_len], 
            [-arm_len, 0, arm_len], 
            [-arm_len, 0, -arm_len],
        ])
        
        # Room / Space Definition
        self.ROOM_SIZE = 800 # -400 to 400
        
    def update(self, dt, inputs):
        self.prop_angle += 40
        
        if not self.active:
            if self.pos[1] > 0: 
                self.vel[1] -= 9.8 * dt * 5
                self.pos += self.vel * dt
                if self.pos[1] < 0:
                    self.pos[1] = 0
                    self.vel = np.zeros(3)
            return

        # Smooth Inputs & Physics
        # We use a simple lerp-like approach for velocity transitions
        target_vx = inputs.get('roll', 0) * self.MAX_SPEED
        target_vz = inputs.get('pitch', 0) * self.MAX_SPEED
        target_vy = inputs.get('throttle', 0) * self.MAX_SPEED
        
        # Smoothly interpolate velocity
        self.vel[0] += (target_vx - self.vel[0]) * self.DRAG * dt
        self.vel[2] += (target_vz - self.vel[2]) * self.DRAG * dt
        self.vel[1] += (target_vy - self.vel[1]) * self.DRAG * dt
        self.yaw += inputs.get('yaw', 0) * self.YAW_SPEED * dt

        # Propeller animation smoothing
        self.target_prop_speed = 1.0 if self.active else 0.0
        self.current_prop_speed += (self.target_prop_speed - self.current_prop_speed) * 3.0 * dt
        self.prop_angle += self.current_prop_speed * 1000 * dt

        self.pos += self.vel * dt
        
        # Floor collision
        if self.pos[1] < 0:
            self.pos[1] = 0
            self.vel[1] = 0
            
        # Room boundaries collisions (Soft bounce)
        half_room = self.ROOM_SIZE / 2
        if abs(self.pos[0]) > half_room:
            self.pos[0] = np.sign(self.pos[0]) * half_room
            self.vel[0] *= -0.5
        if abs(self.pos[2]) > half_room:
            self.pos[2] = np.sign(self.pos[2]) * half_room
            self.vel[2] *= -0.5
        if self.pos[1] > self.ROOM_SIZE: # Ceiling
            self.pos[1] = self.ROOM_SIZE
            self.vel[1] *= -0.5

        # Smooth Camera Follow
        target_cam = np.array([self.pos[0], self.pos[1] + 100, self.pos[2] - 250])
        self.cam_pos += (target_cam - self.cam_pos) * 5.0 * dt # Camera Smoothing delay

    def draw_3d(self):
        W, H = 640, 480
        canvas = np.zeros((H, W, 3), dtype=np.uint8)
        
        # Fixed Camera for Room View OR Chase?
        # User wants a "space where I can test it". A fixed view of the room usually gives better context than chase cam close up.
        # Let's try a dynamic camera that looks at drone but keeps room in view if possible.
        # Actually, chase camera with wider FOV works well for flying.
        
        focal_length = 500 # Slightly wider FOV
        cam_center = np.array([W/2, H/2])
        
        # Use smoothed cam_pos
        cam_pos = self.cam_pos        
        # Projection
        def project(p_world):
            p_cam = p_world - cam_pos
            # Pitch down 15 deg
            pitch = math.radians(15)
            cc, cs = math.cos(pitch), math.sin(pitch)
            R_cam = np.array([[1, 0, 0], [0, cc, cs], [0, -cs, cc]])
            p_cam = p_cam @ R_cam.T
            
            x, y, z = p_cam
            if z <= 10: return None
            
            u = int(focal_length * x / z + cam_center[0])
            v = int(focal_length * -y / z + cam_center[1]) # Invert Y for screen coords (Up is -Y)
            return (u, v)

        # 0. DRAW SKY GRADIENT (Realism)
        for i in range(H//2):
            col = (int(80 + (i/(H/2))*40), int(40 + (i/(H/2))*20), int(20 + (i/(H/2))*10))
            cv2.line(canvas, (0, i), (W, i), col, 1)

        # 1. DRAW CHECKERBOARD GROUND
        color_1 = (40, 40, 40)
        color_2 = (60, 60, 60) # Lighter
        
        # Determine grid alignment
        step = 200
        grid_sz = 1200
        drone_x, drone_z = self.pos[0], self.pos[2]
        
        start_x = int((drone_x - grid_sz/2) // step)
        end_x = int((drone_x + grid_sz/2) // step)
        start_z = int((drone_z - grid_sz/2) // step)
        end_z = int((drone_z + grid_sz/2) // step)
        
        for x in range(start_x, end_x + 1):
            for z in range(start_z, end_z + 1):
                # Quad corners
                p1 = project(np.array([x*step, 0, z*step]))
                p2 = project(np.array([(x+1)*step, 0, z*step]))
                p3 = project(np.array([(x+1)*step, 0, (z+1)*step]))
                p4 = project(np.array([x*step, 0, (z+1)*step]))
                
                if p1 and p2 and p3 and p4:
                    pts = np.array([p1, p2, p3, p4])
                    # Checker pattern
                    col = color_1 if (x+z)%2==0 else color_2
                    cv2.fillPoly(canvas, [pts], col)

        # 2. DRAW DRONE SHADOW
        # Project shadow directly onto Y=0 plane
        shadow_p = np.array([self.pos[0], 0, self.pos[2]])
        s_center = project(shadow_p)
        if s_center:
            # Shadow size decreases with altitude
            alt_factor = max(0, 1.0 - (self.pos[1] / 500.0))
            s_radius = int(25 * alt_factor)
            if s_radius > 2:
                # Use a slightly transparent-looking dark circle
                overlay = canvas.copy()
                cv2.circle(overlay, s_center, s_radius, (10, 10, 10), -1)
                cv2.addWeighted(overlay, 0.5, canvas, 0.5, 0, canvas)

        # Rotation with Tilt (Realism: Tilts in direction of velocity)
        rot_y = math.radians(self.yaw)
        # Tilt factors: more velocity = more tilt
        tilt_x = -self.vel[2] * 1.5   # Forward/Back tilt
        tilt_z = self.vel[0] * 1.5    # Left/Right roll
        
        # Add a bit of "organic" wobble
        if self.active:
            tilt_x += math.sin(self.time * 3.0) * 2.0
            tilt_z += math.cos(self.time * 2.5) * 2.0

        rot_x = math.radians(tilt_x)
        rot_z = math.radians(tilt_z)
        
        Rx = np.array([[1, 0, 0], [0, math.cos(rot_x), -math.sin(rot_x)], [0, math.sin(rot_x), math.cos(rot_x)]])
        Ry = np.array([[math.cos(rot_y), 0, math.sin(rot_y)], [0, 1, 0], [-math.sin(rot_y), 0, math.cos(rot_y)]])
        Rz = np.array([[math.cos(rot_z), -math.sin(rot_z), 0], [math.sin(rot_z), math.cos(rot_z), 0], [0, 0, 1]])
        
        R_total = Rx @ Rz @ Ry

        fuse_world = (self.fuselage @ R_total.T) + self.pos
        arms_world = (self.arms @ R_total.T) + self.pos
        
        fuse_scr = [project(p) for p in fuse_world]
        arms_scr = [project(p) for p in arms_world]
        center_scr = project(self.pos)
        
        if all(fuse_scr) and center_scr and all(arms_scr):
            # Body Rendering (Filled Polygons for professional look)
            color_hull = (50, 50, 50)
            color_glow = (255, 100, 0) # Orange glow
            
            # Draw hull facets
            def draw_face(indices, color):
                pts = np.array([fuse_scr[i] for i in indices])
                cv2.fillPoly(canvas, [pts], color)
                cv2.polylines(canvas, [pts], True, (100, 100, 100), 1)

            # Define 6 faces of the body
            draw_face([0,1,3,2], (30,30,30)) # Back
            draw_face([4,5,7,6], (60,60,60)) # Front
            draw_face([0,1,5,4], (40,40,40)) # Top
            draw_face([2,3,7,6], (20,20,20)) # Bottom
            draw_face([0,2,6,4], (45,45,45)) # Left
            draw_face([1,3,7,5], (45,45,45)) # Right

            # High-intensity LEDs (Front: Green, Back: Red)
            # Front faces are 4,5,7,6? Let's check fuselage definition
            # Fuselage: [w, h, l]... [w, -h, -l]... Back is -L, Front is +L
            # Fuselage points 4,5,6,7 have -W (left side) and various H, L. 
            # Actually let's just use specific indices for ends.
            
            # Rear (Back) -> Red
            for i in [0, 1]:
                cv2.circle(canvas, fuse_scr[i], 4, (0, 0, 255), -1)
                if self.active: cv2.circle(canvas, fuse_scr[i], 8, (0, 0, 150), 1) # Glow
                
            # Front -> Green
            for i in [4, 5]:
                cv2.circle(canvas, fuse_scr[i], 4, (0, 255, 0), -1)
                if self.active: cv2.circle(canvas, fuse_scr[i], 8, (0, 150, 0), 1) # Glow
            
            # Arms
            for i, arm_pt in enumerate(arms_scr):
                # Arm thickness and color
                cv2.line(canvas, center_scr, arm_pt, (60, 60, 60), 4)
                # Propeller
                if self.current_prop_speed > 0.1:
                    # Spinning prop disc
                    p_radius = int(14 * self.current_prop_speed)
                    cv2.circle(canvas, arm_pt, p_radius, (180, 180, 180), 1)
                    # Motion blur lines
                    a = math.radians(self.prop_angle + i*90)
                    for angle_off in [0, 180]:
                        cur_a = a + math.radians(angle_off)
                        off = (int(p_radius*math.cos(cur_a)), int(p_radius*math.sin(cur_a)))
                        cv2.line(canvas, arm_pt, (arm_pt[0]+off[0], arm_pt[1]+off[1]), (220, 220, 220), 1)
                else:
                    cv2.circle(canvas, arm_pt, 8, (40, 40, 40), 1)

        # Status Text
        status = "ARMED" if self.active else "DISARMED"
        col = (0, 255, 0) if self.active else (0, 0, 255)
        cv2.putText(canvas, f"STATUS: {status}", (W-200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)
        cv2.putText(canvas, "TEST ROOM: 800x800", (10, H-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
        
        return canvas
