# Electro-Optical (EO) Focal Plane Array (FPA) Sensor Calibration & Ingest Simulator

## Technical Project Overview
This repository contains an engineering-level Python pipeline designed to simulate the non-ideal hardware limitations of physical digital camera sensors (Focal Plane Arrays) and apply radiometric calibration metrics to guarantee data integrity. 

The pipeline acts as a Hardware-in-the-Loop (HWIL) verification tool, modeling how front-end physical detector noise impacts downstream image processing blocks before firmware code execution.

## Modeled Sensor Physics & Defect Mechanics
The simulation matrix actively injects four distinct physical limitations native to semiconductor optical sensors:
1. **Dark Current Offset:** Simulates thermal baseline electron drift generated within the silicon matrix, modeled via a uniform matrix bias.
2. **Fixed-Pattern Noise (FPN):** Column-to-column pixel sensitivity variations caused by microscopic manufacturing tolerances, modeled via a Gaussian distribution layer.
3. **Photon Shot Noise:** Time-varying noise caused by the statistical randomness of photon arrival rates, modeled dynamically based on local amplitude values.
4. **Silicon Array Defects:** Randomly distributes large manufacturing drop-outs including **Dead Pixels** (stuck at 0 counts) and shorted **Hot Pixels** (saturated at 255 counts) stamped as multi-pixel matrix blocks.

## Calibration Architecture
To recover the pristine signal vector, the software executes a two-stage calibration array:
* **Radiometric Flat-Field Correction:** Ingests a laboratory reference "Dark Frame" (lens cap closed simulation) to subtract uniform thermal drift bias, and applies a gain matrix normalization map to iron out pixel-to-pixel responsivity variances.
* **Dynamic Dead Pixel Replacement (DPR) Filter:** Programmatically generates a **Bad Pixel Map (BPM)** from raw uncalibrated limits, scans out-of-bound coordinate matrices, and applies a dynamic neighborhood expansion loop (3x3 up to 15x15) to calculate localized median interpolation values, cleanly wiping out complex multi-pixel cluster defects.
