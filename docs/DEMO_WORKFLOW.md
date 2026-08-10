# Asterion Demo Workflow

This document outlines the exact workflow to reproduce the core investigation pipeline demonstrated in the E-Rakshak Final Presentation.

## Prerequisites

1. Asterion is running locally (either via Docker Compose or manual setup).
2. You have a valid telecom CDR dataset. Example datasets are provided in the `datasets/demo/` directory.

## Step 1: Case Management

1. Navigate to the **Cases** tab in the sidebar.
2. Click **New Case**.
3. Provide a Case Title (e.g., "Operation Nightfall") and Description.
4. Click **Create Case**.
5. Select the newly created case to enter the investigation context.

## Step 2: Data Ingestion (CSV Import)

1. Navigate to the **Import Data** tab.
2. Ensure you have selected your active case.
3. Click to browse, or drag-and-drop a CSV dataset (e.g., `datasets/demo/asterion_demo_dataset.csv`).
4. Select the correct **Telecom Operator** from the dropdown (Asterion automatically tries to detect this based on headers and filename).
5. Click **Import Evidence**.
6. The system will parse the records, extract network measurements, and commit them to the database.

## Step 3: Localization Pipeline

1. Navigate to the **Localization** tab.
2. Click **Run Pipeline**.
3. Asterion's scientific engine will calculate locations using **Non-Linear Least Squares** or the **Quality-Weighted Centroid** fallback.
4. Review the timeline of computed coordinates.

## Step 4: Tracking and Confidence

1. Navigate to the **Tracking** tab.
2. Click **Apply Kalman Smoothing**.
3. Asterion will filter out erratic jumps and enforce chronological constraints.
4. The system automatically computes **GDOP** (Geometric Dilution of Precision) to represent confidence bounds for each point.

## Step 5: Geospatial Visualization

1. Navigate to the **Map** tab.
2. View the resulting **Heatmap**, which visualizes location density weighted by confidence and dwell time.
3. Toggle the **Trajectory Track** to view the chronological path of the device.

## Step 6: Evidence Generation

1. Navigate to the **Reports** tab.
2. Click **Generate Evidence Packet**.
3. Asterion generates a tamper-evident audit report containing a **SHA-256 integrity hash**, mathematically linking the final map coordinates directly to the raw, imported CSV rows.
