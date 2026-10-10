# Risk-Aware Optimal Routing in MANETs

## 1. Project Overview

A Mobile Ad hoc Network (MANET) is a wireless network consisting of mobile devices that communicate with one another without relying on fixed network infrastructure.

Routing in MANETs is challenging because network topology can change as devices move. Links may also differ in reliability, trustworthiness, and expected lifetime.

This project implements a Python-based mathematical routing model that selects a suitable route between a source node and a destination node by considering route cost, trust, link lifetime, and risk.

The system provides a graphical visualization of the network, displays routing metrics, compares alternative routes, and demonstrates how degraded communication links can affect routing decisions.

## 2. Project Objectives

- Model a MANET using graph theory.
- Identify communication links using a transmission-range constraint.
- Calculate trust, link lifetime, link risk, and link cost.
- Identify feasible routes between a source and destination.
- Select the lowest-cost route that satisfies the specified constraints.
- Compare the selected route with alternative feasible routes.
- Demonstrate the effect of link degradation on routing decisions.
- Visualize the network and export link metrics for analysis.

## 3. Technologies Used

- Python 3
- NetworkX
- Matplotlib
- Tkinter (Python GUI support)
- CSV for exporting link metrics

## 4. Network Configuration

The current model uses the following configuration:

| Parameter | Value |
|---|---|
| Number of nodes | 10 |
| Source node | N0 |
| Destination node | N9 |
| Transmission range | 50 metres |
| Maximum hop count | 5 |
| Minimum trust | 0.50 |
| Minimum link lifetime | 2 seconds |
| Maximum route risk | 1.0 |

The network is represented as a graph in which nodes represent devices and edges represent communication links.

Communication links are discovered according to the distance between nodes and the configured transmission range.

## 5. Mathematical Model

### 5.1 Trust Calculation

Trust is calculated using forwarding reliability, acknowledgement reliability, reputation, and a false-advertisement ratio.

The trust equation is:

T(i,j) = w1*F(i,j) + w2*A(i,j) + w3*Rep(i,j) + w4*(1-H(i,j))

Where:

- F = Forwarding reliability
- A = Acknowledgement reliability
- Rep = Reputation
- H = False-advertisement ratio
- w1, w2, w3, w4 = Trust weights

The current model assigns a weight of 0.25 to each trust component.

### 5.2 Route Cost

The route-selection model uses the following cost function:

C(P) = alpha*Hops(P)
       + beta*sum(1 - Trust(i,j))
       + gamma*sum(1/Lifetime(i,j) + D(i,j))

Where:

- C(P) = Total route cost
- Hops(P) = Number of links in the route
- Trust(i,j) = Trust value of a communication link
- Lifetime(i,j) = Estimated link lifetime
- D(i,j) = Link drop ratio
- alpha, beta, gamma = Cost weights

The current weights are:

- Alpha = 0.50
- Beta = 0.25
- Gamma = 0.25

### 5.3 Route Risk

The model calculates route risk by summing the risk contributions of its links:

R(P) = sum((1 - Trust(i,j))
           + delta/Lifetime(i,j)
           + eta*D(i,j))

Where:

- R(P) = Total route risk
- Delta = 0.20
- Eta = 0.30

### 5.4 Route Selection

The routing engine enumerates candidate simple paths from the source to the destination, subject to the maximum hop count.

It checks link eligibility and route constraints, then selects the feasible route with the lowest calculated cost.

The selected route must satisfy the configured trust, lifetime, hop-count, and route-risk constraints.

## 6. Main Features

- Graphical visualization of the MANET.
- Display of source and destination nodes.
- Visualization of the selected route.
- Link discovery based on transmission range.
- Calculation of trust, lifetime, cost, and risk.
- Comparison of feasible alternative routes.
- Link degradation and route recalculation.
- Node mobility simulation.
- Reset to the baseline network state.
- CSV export of link metrics.

## 7. Project Structure

```text
Risk-Aware-MANET-Routing/
|
|-- risk_aware_manet.py
|-- manet_visualization.py
|-- README.md
|-- screenshots/
```

- `risk_aware_manet.py`: Implements the mathematical routing model, link metrics, route evaluation, constraints, and CSV export.
- `manet_visualization.py`: Provides the graphical network visualization and interactive controls.
- `README.md`: Documents the project and explains how to run it.
- `screenshots/`: Contains screenshots demonstrating the application.

## 8. Installation

### Prerequisites

- Python 3
- pip
- A graphical desktop environment for displaying the Matplotlib window

### Install Required Packages

On Ubuntu, install the required system packages:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-matplotlib python3-networkx python3-tk
```

## 9. How to Run

Place both Python files in the same directory.

Navigate to the project directory:

```bash
cd ~/ns3/ns-3.47
```

Run the graphical application:

```bash
python3 manet_visualization.py
```

The visualization imports `risk_aware_manet.py` automatically. Both files must be in the same directory.

### Running the Terminal Menu

To run the routing engine's interactive terminal menu instead, use:

```bash
python3 risk_aware_manet.py
```

## 10. Using the Application

The graphical application provides the following controls:

- **Reset / Baseline:** Restores the initial node positions and clears degraded links.
- **Degrade Link:** Degrades a link on the currently selected route and recalculates routing.
- **Recalculate:** Re-evaluates the route using the current network state.
- **Move +5 s:** Advances the mathematical mobility model by five seconds.
- **Show Link Metrics:** Displays the calculated properties of discovered links.
- **Show Alternative Routes:** Displays feasible routes ranked by cost.
- **Save CSV:** Exports link metrics to a CSV file.

The displayed results can be used to compare route cost, risk, hop count, and the effects of link degradation.

## 11. Results and Evaluation

The application displays the selected route, hop count, route risk, route cost, and configured constraints.

Experiments can be conducted by degrading communication links, advancing node mobility, and comparing alternative routes.

The results should be evaluated to determine whether the selected route satisfies the constraints and has the lowest cost among the feasible candidate routes.

Screenshots and measured results should be included in the project report.

## 12. Advantages

- Considers trust and risk in addition to hop count.
- Supports mathematical comparison of alternative feasible routes.
- Allows link degradation and mobility experiments.
- Provides a graphical representation of routing decisions.
- Exports link metrics for further analysis.

## 13. Limitations

- Link trust and reliability values are modelled inputs.
- The current model does not demonstrate real wireless packet transmission.
- Enumerating simple paths may become computationally expensive as the network grows.
- The quality of routing decisions depends on the selected weights, thresholds, and assumptions.

## 14. Scope and Future Improvements

Possible future improvements include:

- Integrating the routing algorithm with an ns-3 wireless network simulation.
- Evaluating packet delivery ratio, end-to-end delay, and throughput.
- Testing larger networks and different mobility patterns.
- Improving the route-search algorithm for larger network topologies.
- Calibrating trust and risk values using measured network behaviour.

## 15. Conclusion

This project demonstrates a mathematical approach to routing in Mobile Ad hoc Networks by combining graph representation, trust calculation, link lifetime estimation, route-cost minimization, and risk constraints.

The graphical interface enables users to visualize the selected route, inspect link metrics, compare feasible alternatives, and investigate the effect of degraded communication links.

The project illustrates how mathematical modelling can support routing decisions in dynamic network environments.

| Team Member | Primary Role | Contributions |
|---|---|---|
| Member 1 | Algorithm and Solution design | Varun Dev |
| Member 2 | Project Coordinator | Abhijith M |
| Member 3 | Mathematical/Logical Modeling | Emy Biju |
| Member 4 | Implementation and Coding | Abhijit vellekkat |
| Member 5 | Data and Experimentation | Sandeep UB |
| Member 6 | Testing and Validation | Bineesh BB |
| Member 7 | Presentation | Mohan Krishna |
| Member 8 | Documanetation | Pooja |


## 16. Repository

GitHub Repository: https://github.com/AV-Abhi1289/secure_routing
