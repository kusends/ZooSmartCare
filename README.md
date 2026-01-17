# ZooSmartCare

**Project Status:** In Development. Currently, only the **Backend** and **IoT Controller** are implemented. The **Web Client** and **Mobile Client** are in the planning stage and not yet available.

**ZooSmartCare** is an integrated hardware-software system designed to automate animal care processes in zoos. It transforms the approach to animal husbandry from reactive (treating consequences) to proactive (preventing problems) by creating a "Smart Enclosure" ecosystem.

The system bridges the gap between biological species' needs for a stable environment and the physical limitations of staff, ensuring continuous, automated control 24/7.

## Core Functionality

The solution operates on a closed-loop management cycle: **Monitoring → Response → Analysis**.

### 1. IoT Controller
* Autonomous reading of environmental sensors (temperature, humidity, light) with noise filtration algorithms.
* Local decision-making for climate control (heating, ventilation) based on stored configuration files, ensuring safety even without server connection.
* Control of servo motors for scheduled feeding with precise portion dosing using an internal Real-Time Clock (RTC).
* Automatic switching to local storage mode during network outages to ensure data integrity.

### 2. Backend 
* Secure data ingestion from distributed IoT devices via **MQTT** and request processing from client apps via **REST**.
* Validation of incoming data against veterinary norms. Automatic incident generation upon detecting anomalies.
* Acts as the Source of Truth for enclosure settings, ensuring synchronization with IoT controllers.
* Aggregation of telemetry in a **Time-series Database** for retrospective analysis.

### 3. Client Interfaces
* **Web Client (Admin & Zoologist):**
    * Interactive dashboard with real-time status of all enclosures.
    * Animal Knowledge Base (diet, climate profiles, medical history).
    * Schedule constructor (feeding cycles, seasonality).
    * Analytics and reporting tools.
* **Mobile Client (Technical Staff):**
    * Instant alerts for critical events (e.g., temperature drop, low battery).
    * Quick identification of enclosures and access to status history.
    * Recording maintenance actions (cleaning, refilling food) on-site.

## System Architecture & Security

### Operating Environment
* Combines physical objects (enclosures) and digital infrastructure.
* Designed for **24/7/365** operation.
* IoT controllers maintain autonomous life support functions during server downtime (up to 30 mins tolerance for central monitoring data gaps).
* Critical alert transmission < 5 seconds.

### Security Standards
* All communication channels are secured via **TLS/SSL**.
* Strict role-based authentication model to prevent unauthorized parameter changes.
* Guaranteed storage of measurement history and staff action logs for incident investigation.

## Business Objectives
* Continuous monitoring prevents unobserved failures during night shifts or weekends.
* Automated feeding removes human error in dosing, preventing obesity or nutrient deficiency.
* Digital records allow veterinarians to correlate animal health with environmental history.
