# Scientific Engine

The Asterion platform utilizes a decoupled, mathematically rigorous scientific engine to reconstruct device locations from cellular measurements.

## Core Principles

1. **No Data Fabrication**: If a coordinate cannot be scientifically determined, it is explicitly marked as "Unknown".
2. **Quality Weighting**: Signals with higher received signal strength (RSSI) and closer timing advances (TA) exert stronger mathematical pull on the location estimate.
3. **Traceability**: Every output coordinate is verifiably linked to an input row from a CDR dataset.

## Multilateration Pipeline

Asterion attempts Non-Linear Least Squares (NLLS) first. If the mathematical rank is deficient (e.g., only 1 or 2 towers are visible), it gracefully falls back to a Quality-Weighted Centroid.

### 1. Non-Linear Least Squares (NLLS)
The NLLS solver utilizes the **Levenberg-Marquardt** algorithm to minimize the residual errors between observed signal distances and theoretical distances.
- **Optimizer:** `scipy.optimize.least_squares(method="lm")`
- **Cost Function**: Minimizes $\sum (d_{observed} - d_{theoretical})^2$

### 2. Quality-Weighted Centroid
When NLLS cannot converge (due to collinear geometry or insufficient towers), the engine calculates a center of mass weighted by RF signal strength.
- Closer towers (stronger RSSI) pull the estimated location proportionally closer to their exact coordinates.

## Trajectory Smoothing (Kalman Tracking)

Raw multilateration outputs often appear jagged due to environmental signal bounce (multipath fading). Asterion applies a **2D Constant Velocity Kalman Filter** to track the device over time.

- **State Vector**: Contains $X$, $Y$ positions and $V_x$, $V_y$ velocities.
- **Chronology Enforcement**: The filter strictly prevents chronological impossibility (e.g., negative time deltas between events), dropping or flagging invalid observations.

## Confidence Estimation (GDOP)

A location estimate is only useful if its reliability is known. Asterion quantifies this using **Geometric Dilution of Precision (GDOP)**.

- **Low GDOP (< 3)**: High confidence. Towers surround the target in optimal geometry.
- **High GDOP (> 7)**: Low confidence. Towers are clustered or collinear, leading to high spatial ambiguity.

Asterion also computes the covariance matrix to generate **Error Ellipses**—representing the 95% confidence bounds around any estimated point.
