import numpy as np
import matplotlib.pyplot as plt

def generate_synthetic_sensor_frame(width=512, height=512, signal_level=120):
    """
    Simulates a perfect, ideal optical wavefront striking a digital camera sensor.
    Creates a uniform flat-field target image grid.
    """
    return np.ones((height, width), dtype=np.float64) * signal_level

def inject_fpa_hardware_defects(ideal_frame, dark_current=8.0, fixed_pattern_std=4.0):
    """
    Simulates the physical, non-ideal hardware limitations of a real image sensor:
    1. Dark Current / Thermal Baseline Noise
    2. Fixed-Pattern Noise (FPA column-to-column pixel variations)
    3. Random Shot Noise (Photon arrival variations)
    4. Dead / Hot Pixels (Manufacturing defects stamped as 10x10 blocks)
    """
    height, width = ideal_frame.shape
    corrupted_frame = ideal_frame.copy()
    
    # 1. Add Dark Current baseline offset
    corrupted_frame += dark_current
    
    # 2. Add Fixed-Pattern Noise (FPN) matrix layer 
    fpn_matrix = np.random.normal(0, fixed_pattern_std, size=(height, width))
    corrupted_frame += fpn_matrix
    
    # 3. Add Photon Shot Noise
    shot_noise = np.random.normal(0, np.sqrt(corrupted_frame))
    corrupted_frame += shot_noise
    
    # 4. Inject physical hardware defects (10x10 blocks so they are highly visible)
    num_defects = 8
    block_size = 10
    for _ in range(num_defects):
        y_dead, x_dead = np.random.randint(0, height - block_size), np.random.randint(0, width - block_size)
        y_hot, x_hot = np.random.randint(0, height - block_size), np.random.randint(0, width - block_size)
        
        corrupted_frame[y_dead:y_dead+block_size, x_dead:x_dead+block_size] = 0.0      
        corrupted_frame[y_hot:y_hot+block_size, x_hot:x_hot+block_size] = 255.0      
        
    return np.clip(corrupted_frame, 0, 255).astype(np.uint8)

def execute_flat_field_calibration(corrupted_frame, dark_frame, gain_map):
    """
    Applies standard radiometric calibration matrix math:
    Calibrated = (Corrupted - Dark) * Gain_Map
    """
    pixel_corrected = corrupted_frame.astype(np.float64) - dark_frame
    calibrated_frame = pixel_corrected * gain_map
    return np.clip(calibrated_frame, 0, 255).astype(np.uint8)

def apply_dead_pixel_replacement(calibrated_frame, bad_pixel_mask):
    """
    Professional DPR Filter: Uses a predefined Bad Pixel Mask (BPM) 
    to locate defects and applies a dynamic neighborhood expansion loop.
    """
    height, width = calibrated_frame.shape
    dpr_frame = calibrated_frame.copy()
    
    # Extract coordinates directly from our dedicated hardware mask
    bad_y, bad_x = np.where(bad_pixel_mask == True)
    
    for y, x in zip(bad_y, bad_x):
        window_radius = 1
        success = False
        
        while not success and window_radius < 15:
            y_min, y_max = max(0, y - window_radius), min(height, y + window_radius + 1)
            x_min, x_max = max(0, x - window_radius), min(width, x + window_radius + 1)
            
            neighborhood = calibrated_frame[y_min:y_max, x_min:x_max]
            local_mask = bad_pixel_mask[y_min:y_max, x_min:x_max]
            
            # Extract ONLY pixels that are marked as healthy in the mask
            valid_pixels = neighborhood[local_mask == False]
            
            if len(valid_pixels) > 0:
                dpr_frame[y, x] = np.median(valid_pixels)
                success = True
            else:
                window_radius += 1
                
    return dpr_frame


# =====================================================================
# =====================================================================
width, height = 512, 512
ideal_wavefront = generate_synthetic_sensor_frame(width, height, signal_level=120)
dark_frame_reference = np.random.normal(8.0, 1.0, size=(height, width)) 
gain_matrix_map = np.ones((height, width), dtype=np.float64)

# 1. Generate the raw corrupted frame coming off the bench
raw_camera_output = inject_fpa_hardware_defects(ideal_wavefront)

# 2. CREATE THE BAD PIXEL MASK FIRST (Analyze raw, uncalibrated limits)
bad_pixel_mask = (raw_camera_output <= 2) | (raw_camera_output >= 253)

# 3. Apply standard Flat-Field calibration matrix
calibrated_image = execute_flat_field_calibration(raw_camera_output, dark_frame_reference, gain_matrix_map)

# 4. Run DPR using our dedicated pristine mask coordinates
pristine_final_image = apply_dead_pixel_replacement(calibrated_image, bad_pixel_mask)


# =====================================================================
# =====================================================================
fig, axes = plt.subplots(2, 2, figsize=(10, 10))
fig.suptitle("Electro-Optical (EO) FPA Sensor Calibration Dashboard", fontsize=14, fontweight='bold')

# Panel 1: Ideal flat-field input
im1 = axes[0, 0].imshow(ideal_wavefront, cmap='gray', vmin=0, vmax=255)
axes[0, 0].set_title("1. Ideal Wavefront (Flat-Field Input)")
fig.colorbar(im1, ax=axes[0, 0], fraction=0.046, pad=0.04)

# Panel 2: Raw sensor corrupted output
im2 = axes[0, 1].imshow(raw_camera_output, cmap='gray', vmin=0, vmax=255)
axes[0, 1].set_title("2. Raw FPA Sensor Output (With Large Defects)")
fig.colorbar(im2, ax=axes[0, 1], fraction=0.046, pad=0.04)

# Panel 3: Reference Dark Frame Mask
im3 = axes[1, 0].imshow(dark_frame_reference, cmap='gray', vmin=0, vmax=255)
axes[1, 0].set_title("3. Lab Reference Dark Frame (Thermal Mask)")
fig.colorbar(im3, ax=axes[1, 0], fraction=0.046, pad=0.04)

# Panel 4: Final Cleared Output Image (With full [1, 1] index routing)
im4 = axes[1, 1].imshow(pristine_final_image, cmap='gray', vmin=0, vmax=255)
axes[1, 1].set_title("4. Calibrated Output Matrix (With DPR Filter)")
fig.colorbar(im4, ax=axes[1, 1], fraction=0.046, pad=0.04)

plt.tight_layout()
plt.show()
