# SHIFT — Algorithm Design & Theoretical Foundations

> **System**: SHIFT — Streaming Hybrid Intelligence for Fraud Tracking  
> **Topic**: Algorithm Design, Streaming Mathematics, and Drift Forensics  
> **Date**: 2026-11-06  

---

## 1. The Moving Target Challenge: Mathematical Formulation

In static fraud detection, an ML model estimates the conditional posterior probability:
$$P(Y = 1 \mid X)$$
where $X \in \mathbb{R}^d$ is the transaction feature vector and $Y \in \{0, 1\}$ indicates fraud.

In dynamic adversarial streaming environments, this formulation suffers from two catastrophic vulnerabilities:
1. **Covariate Shift**: $P(X)$ changes over time while $P(Y \mid X)$ remains unchanged (e.g. holiday shopping or payment rail adoption).
2. **Concept Drift**: The conditional distribution $P(Y \mid X)$ changes because adversaries intentionally mutate their tactics to evade learned decision boundaries.

Crucially, **ground-truth fraud labels $Y$ arrive with severe delay**—typically 14 to 90 days following victim disputes or bank chargebacks. A detection system that requires confirmed labels to detect changes will remain blind throughout the active theft window.

---

## 2. SHIFT Algorithmic Framework

SHIFT addresses this through a **Tripartite Streaming Algorithm**:
1. **Streaming Anomaly Detection without Class Labels** ($S_{\text{anom}}$)
2. **Adaptive Sliding Window (ADWIN) Mean Shift Tracking**
3. **Population Stability Index (PSI) Feature Forensics**

---

## 3. Streaming Anomaly Detection: Half-Space Trees (HST)

### 3.1. Theoretical Basis
Standard offline tree ensembles (e.g., Isolation Forest) require full retraining over a batch of data, which introduces latency and high memory footprint. SHIFT implements streaming **Half-Space Trees (Tan et al., 2011)** via the `river` streaming library.

### 3.2. Online Windowed Update
- A collection of $T$ random binary trees are constructed over the bounded feature workspace $[0, 1]^d$.
- Each tree node maintains two counters:
  - $r$: reference window counter (baseline legitimate density).
  - $l$: latest window counter (streaming sliding window).
- For an incoming streaming sample $x$:
  $$S_{\text{HST}}(x) = \frac{1}{T} \sum_{t=1}^{T} \left(1 - \frac{r(\text{leaf}_t(x))}{r_{\max}}\right)$$
- If sample $x$ falls into regions of the feature space that were sparsely populated during the reference window, $r(\text{leaf}_t(x))$ is low, yielding a high anomaly score $S_{\text{HST}}(x) \to 1.0$.

---

## 4. Unlabelled Concept Drift Detection: ADWIN

### 4.1. Algorithm Mechanics (Bifet & Gavaldà, 2007)
ADWIN maintains a variable-length sliding window $W$ of real-valued observations. In SHIFT, $W$ tracks the stream of **unlabelled HST anomaly scores**:
$$W = \langle s_1, s_2, \dots, s_n \rangle \quad \text{where } s_i = S_{\text{HST}}(x_i)$$

Whenever two sub-windows $W_0$ and $W_1$ (such that $W = W_0 \cdot W_1$) exhibit a difference in means that exceeds a statistically rigorous threshold $\epsilon_{\text{cut}}$, ADWIN drops the older sub-window and flags drift:
$$\epsilon_{\text{cut}} = \sqrt{\frac{1}{2m} \ln\left(\frac{4 |W|}{\delta}\right)}$$
where:
$$m = \frac{1}{\frac{1}{|W_0|} + \frac{1}{|W_1|}}$$
and $\delta = 0.002$ is the confidence parameter.

### 4.2. Why This Catches the Moving Target Before Labels Arrive
When fraudsters read alerts and pivot tactics (e.g. from rapid low-value transactions to sudden high-value night-time transfers), the individual transaction features enter unmapped sub-spaces. The HST anomaly scores spike. ADWIN registers a statistically significant change in the distribution of anomaly scores within **7 to 15 events**, providing an early warning alert **weeks before chargeback labels arrive**.

---

## 5. Forensic Feature Attribution: Population Stability Index (PSI)

While ADWIN detects **WHEN** the world changed, PSI determines **WHAT** changed.

### 5.1. Formulation
For each feature $j \in \{1, \dots, d\}$, SHIFT segments the historical reference window into $B = 10$ quantile bins. For the rolling streaming window, bin proportions are computed:
$$\text{PSI}_j = \sum_{b=1}^{B} \left(P_{j, b} - Q_{j, b}\right) \cdot \ln\left(\frac{P_{j, b}}{Q_{j, b}} + \epsilon\right)$$
where:
- $P_{j, b}$: proportion of observations in bin $b$ in the baseline reference window.
- $Q_{j, b}$: proportion of observations in bin $b$ in the active streaming window.
- $\epsilon = 10^{-4}$ prevents division-by-zero or $\ln(0)$.

### 5.2. Operational Thresholds
- **$\text{PSI} < 0.10$**: Stable feature distribution.
- **$0.10 \le \text{PSI} < 0.25$**: Moderate distribution shift (telemetry advisory).
- **$\text{PSI} \ge 0.25$**: Significant covariate drift (triggers automated policy escalation).

---

## 6. Multi-Expert Risk Fusion Architecture

Instead of trusting a single black-box classifier, SHIFT executes 7 independent specialists on every transaction:

| # | Expert Name | Methodology | Primary Signals Used |
|---|-------------|-------------|----------------------|
| 1 | Supervised Fraud Expert | Random Forest (IEEE-CIS) | Tabular amount, velocity, context patterns |
| 2 | Behavioural HST Expert | Streaming Half-Space Trees | Rolling behavioral subspace density |
| 3 | Isolation Forest Expert | Subspace Tree Isolation | Offline high-dimensional outlier score |
| 4 | Velocity & Burst Expert | Sliding Window Rate Monitor | $t_{\text{prev}}$, transactions per minute |
| 5 | Device & Session Expert | Fingerprint Continuity Engine | Device switch, multi-session collision |
| 6 | Network Risk Expert | Reputation & ASN Validator | VPN flag, proxy flag, untrusted ASN |
| 7 | Rule-Based Policy Expert | Statutory Banking Limits | High-value thresholds (₹100k), Mule accounts |

The final risk score combines all signals:
$$\text{Fused Risk} = \frac{\sum_{i=1}^{7} w_i \cdot c_i \cdot s_i}{\sum_{i=1}^{7} w_i \cdot c_i}$$

---

## 7. Guardrail: No Blind Auto-Retraining

A frequent, dangerous error in streaming ML is automatically fine-tuning model weights on unlabelled suspicious events. This enables **Adversarial Poisoning**: attackers feed subtly shifted fraudulent samples over time to pull the decision boundary into accepting their fraud as normal.

**SHIFT's Invariant Rule**:
- Unlabelled drift triggers **Sensitivity Escalation & Investigation Routing**.
- Model parameters are **NEVER** updated until verified ground-truth labels are supplied through the authorized `observe_ground_truth()` API.

