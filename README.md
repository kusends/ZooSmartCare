# ZooSmartCare

**ZooSmartCare** is an integrated hardware-software system designed to automate animal care processes in zoos. It transforms the approach to animal husbandry from reactive (treating consequences) to proactive (preventing problems) by creating a "Smart Enclosure" ecosystem.

The system bridges the gap between biological species' needs for a stable environment and the physical limitations of staff, ensuring continuous, automated control 24/7.

## Core Functionality

The solution operates on a closed-loop management cycle: **Monitoring → Response → Analysis**.

### 1. IoT Controller (The "Smart Enclosure")
* **Data Collection:** Autonomous reading of environmental sensors (temperature, humidity, light) with noise filtration algorithms.
* **Autonomous Control:** Local decision-making for climate control (heating, ventilation) based on stored configuration files, ensuring safety even without server connection.
* **Precision Feeding:** Control of servo motors for scheduled feeding with precise portion dosing using an internal Real-Time Clock (RTC).
* **Data Buffering:** Automatic switching to local storage mode during network outages to ensure data integrity.

### 2. Backend (Server)
* **API Gateway:** Secure data ingestion from distributed IoT devices via **MQTT** and request processing from client apps via **REST**.
* **Real-time Analysis:** Validation of incoming data against veterinary norms. Automatic incident generation upon detecting anomalies.
* **Configuration Management:** Acts as the "Source of Truth" for enclosure settings, ensuring synchronization with IoT controllers.
* **Storage:** Aggregation of telemetry in a **Time-series Database** for retrospective analysis.

### 3. Client Interfaces
* **Web Client (Admin & Zoologist):**
    * Interactive dashboard with real-time status of all enclosures.
    * Animal Knowledge Base (diet, climate profiles, medical history).
    * Schedule constructor (feeding cycles, seasonality).
    * Analytics and reporting tools.
* **Mobile Client (Technical Staff):**
    * **Push Notifications:** Instant alerts for critical events (e.g., temperature drop, low battery).
    * **QR Scanner:** Quick identification of enclosures and access to status history.
    * **Digital Log:** Recording maintenance actions (cleaning, refilling food) on-site.

## System Architecture & Security

### Operating Environment
* **Distributed Architecture:** Combines physical objects (enclosures) and digital infrastructure.
* **Availability:** Designed for **24/7/365** operation.
* **Fault Tolerance:** IoT controllers maintain autonomous life support functions during server downtime (up to 30 mins tolerance for central monitoring data gaps).
* **Latency:** Critical alert transmission < 5 seconds.

### Security Standards
* **Encryption:** All communication channels (IoT-Server-Clients) are secured via **TLS/SSL**.
* **Access Control:** Strict role-based authentication model to prevent unauthorized parameter changes.
* **Data Integrity:** Guaranteed storage of measurement history and staff action logs for incident investigation.

## Business Objectives
* **Eliminate "Blind Spots":** Continuous monitoring prevents unobserved failures during night shifts or weekends.
* **Precision:** Automated feeding removes human error in dosing, preventing obesity or nutrient deficiency.
* **Analytics:** Digital records allow veterinarians to correlate animal health with environmental history.

## License

This project is proprietary software designed for zoo management automation.
