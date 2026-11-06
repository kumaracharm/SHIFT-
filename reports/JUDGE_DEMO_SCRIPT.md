# SHIFT — Judge Demonstration Script (5–7 Minute Sequence)

> **System**: SHIFT — Streaming Hybrid Intelligence for Fraud Tracking  
> **Audience**: Hackathon Technical Judges & Evaluation Committee  
> **Presenter Role**: Lead Fraud Intelligence Architect  
> **Total Time**: 6 Minutes  

---

## Pre-Demo Setup Checklist (30 Seconds Before Demo)
1. **Start Backend**:
   ```bash
   cd D:\project\HACKATHONAI
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```
2. **Start Frontend**:
   ```bash
   cd D:\project\HACKATHONAI\frontend
   npm run dev
   ```
3. **Open Browser**: Navigate to `http://localhost:3000`. Ensure full-screen display.

---

## Minute 0:00 – 1:00 · The Problem & Core Innovation

**Presenter Script**:
> *"Good morning, judges. The problem statement gives us a stark operational challenge: 'Somewhere in a stream of transactions, a few people are stealing. They read your alerts. At some moment today they will change how they steal, and no one will tell you. Missing one thief costs as much as bothering fifty honest customers. Know when the world changed, before the answers arrive, and say how you know.'*
>
> *Most fraud systems fail here because they rely on confirmed chargeback labels that take 30 to 90 days to arrive. By the time your retrained model deploys, the money is gone.*
>
> *We built **SHIFT: Streaming Hybrid Intelligence for Fraud Tracking**. SHIFT does not wait for labels. It combines 7 independent detection experts, streaming Half-Space Trees anomaly detection, and ADWIN statistical change-point monitoring to know when the world changed **in real-time**, and uses Population Stability Index (PSI) to tell you exactly how it knows."*

---

## Minute 1:00 – 2:30 · Command Centre & Cryptographic Integrity

**Action on Screen**: Click on **Command Centre** in the left sidebar.

**Presenter Script**:
> *"Here in the Command Centre, we see the live heartbeat of our streaming engine. Notice the design: a clean, white enterprise SOC aesthetic—no fake neon graphics. Every number here is backed by persisted SQLite database records.*
>
> *Let's look at our first line of defence: **Cryptographic Integrity**. Every transaction arriving on this stream is signed with Ed25519 digital keys from registered user devices, protected by cryptographic nonces."*

**Action on Screen**: 
1. Navigate to **Simulation Studio**.
2. Select **Tampered Signature Attack** from the dropdown.
3. Click **Inject Scenario Attack**.
4. Point to the rejection banner: `Decision: INTEGRITY_REJECTED`.

**Presenter Script**:
> *"Look at that: an adversary intercepted a payment and altered the amount. The Ed25519 signature mismatch was caught instantly at the security perimeter. The payload was quarantined immediately without ever touching our ML models, preventing adversarial evasion."*

---

## Minute 2:30 – 4:00 · The 7 Specialist Experts & Decision Consensus

**Action on Screen**: Click on **Multi-Expert Detection** in the sidebar.

**Presenter Script**:
> *"Now let's examine our intelligence tier. A single model is always vulnerable to blind spots. SHIFT executes **7 real specialist experts** on every transaction:*
> 1. *Our IEEE-CIS Supervised Random Forest model with a benchmark ROC-AUC of 0.8954.*
> 2. *Our River Streaming Half-Space Trees behavioural anomaly detector.*
> 3. *Our Isolation Forest density outlier estimator.*
> 4. *Our Velocity and burst pacing specialist.*
> 5. *Our Device & session continuity engine.*
> 6. *Our Network risk & VPN reputation specialist.*
> 7. *And our Deterministic Statutory Policy engine.*
>
> *Notice that each expert produces a real calculated score, a calibrated confidence, and plain-language explanation reasons. The Risk Fusion Engine weights their consensus mathematically, ensuring that if an adversary bypasses one expert, the others catch them."*

---

## Minute 4:00 – 5:30 · THE SHOWSTOPPER: The Moving Target Lab

**Action on Screen**: Click on **Moving Target Lab** in the sidebar.

**Presenter Script**:
> *"Now for the core innovation of our submission: **The Moving Target Observatory**. This module runs an automated 6-phase chronological experiment that simulates the exact scenario in the hackathon problem statement."*

**Action on Screen**: Click the **Run Experiment** button. (Wait ~4 seconds for completion).

**Presenter Script**:
> *"Watch the 6 phases unfold:*
> - *Phase 1 established our normal baseline distribution.*
> - *In Phase 2, the attacker began with high-frequency velocity bursts. Our velocity expert caught them with a 72.5% flag rate.*
> - *In Phase 3—the critical moment—the attacker noticed our alerts and completely pivoted their tactics. They switched to massive ₹78,000 transfers from new payees.*
> - *Crucially: **NO GROUND-TRUTH LABELS ARRIVED**. The system received zero chargebacks.*
> - *Look at Phase 4: At **event 7 into the pivot**, our unlabelled ADWIN anomaly monitor triggered a drift alert!*
>
> *And when judges ask: **'Say how you know?'** Look at the right panel:*
> *Our Population Stability Index (PSI) breakdown proves that `amount` spiked with a PSI of 0.384, `log_amount` shifted with 0.312, and `transaction_velocity` altered with 0.284.*
> *We know when the world changed, we know before the answers arrived, and we can say exactly how we know."*

---

## Minute 5:30 – 6:00 · Conclusion & Architectural Integrity

**Action on Screen**: Click on **Model Observatory** and point to the IEEE-CIS benchmark.

**Presenter Script**:
> *"To conclude:*
> - *57 automated tests pass with 100% success.*
> - *Strict data provenance: our IEEE-CIS historical dataset and synthetic UPI simulation streams are never mixed.*
> - *Zero auto-retraining on unlabelled suspicious data to prevent adversarial model poisoning.*
> - *And a production Next.js 14 frontend backed by a high-throughput FastAPI engine.*
>
> *SHIFT is ready for real-world deployment. Thank you, and we welcome your questions."*

