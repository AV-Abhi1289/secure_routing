"""
Risk-Aware Optimal Routing in MANETs
Python routing engine connected to manet_visualization.py.

H means false route-advertisement ratio:
higher H = lower honesty, so trust uses (1 - H).

Cost:
C(P) = alpha*hop_count
       + beta*sum(1 - trust)
       + gamma*sum(1/lifetime + drop_ratio)

Risk constraint:
R(P) = sum((1-trust) + DELTA/lifetime + ETA*drop_ratio)
"""

import csv
import math

# -------------------- Configuration --------------------

NUM_NODES = 10
SOURCE = 0
DESTINATION = 9
TX_RANGE = 50.0

W1 = W2 = W3 = W4 = 0.25

ALPHA = 0.50
BETA = 0.25
GAMMA = 0.25

DELTA = 0.20
ETA = 0.30

TMIN = 0.50
LMIN = 2.0
RMAX = 1.0
HMAX = 5
MAX_LIFETIME = 120.0
SIMULATION_TIME = 0.0

# -------------------- Mobility --------------------

initial_positions = {
    0: (0.0, 0.0),
    1: (20.0, 0.0),
    2: (40.0, 0.0),
    3: (60.0, 0.0),
    4: (80.0, 0.0),
    5: (0.0, 20.0),
    6: (20.0, 20.0),
    7: (40.0, 20.0),
    8: (60.0, 20.0),
    9: (80.0, 20.0),
}
positions = dict(initial_positions)

velocities = {
    0: (0.10, 0.00),
    1: (0.05, 0.03),
    2: (0.00, 0.05),
    3: (-0.05, 0.02),
    4: (-0.10, 0.00),
    5: (0.05, -0.03),
    6: (0.00, -0.05),
    7: (-0.03, -0.02),
    8: (0.02, 0.00),
    9: (-0.05, 0.02),
}

# F = forwarding reliability, A = ACK reliability,
# Rep = reputation, H = false-advertisement ratio, D = drop ratio.
DEFAULT_METRICS = {"F": 1.00, "A": 0.90, "Rep": 0.85, "H": 0.10, "D": 0.05}

special_metrics = {
    (0, 2): {"F": 1.00, "A": 0.75, "Rep": 0.8644, "H": 0.10, "D": 0.25},
    (2, 9): {"F": 1.00, "A": 0.05, "Rep": 0.7939, "H": 0.10, "D": 0.95},
    (0, 6): {"F": 1.00, "A": 0.90, "Rep": 0.88, "H": 0.10, "D": 0.05},
    (3, 6): {"F": 1.00, "A": 1.00, "Rep": 0.90, "H": 0.10, "D": 0.02},
    (3, 9): {"F": 1.00, "A": 1.00, "Rep": 0.88, "H": 0.10, "D": 0.02},
    (0, 1): {"F": 1.00, "A": 0.90, "Rep": 0.86, "H": 0.10, "D": 0.05},
    (1, 8): {"F": 1.00, "A": 1.00, "Rep": 0.87, "H": 0.10, "D": 0.02},
    (8, 9): {"F": 1.00, "A": 1.00, "Rep": 0.88, "H": 0.10, "D": 0.02},
    (2, 3): {"F": 1.00, "A": 0.85, "Rep": 0.84, "H": 0.10, "D": 0.05},
    (2, 7): {"F": 1.00, "A": 0.85, "Rep": 0.84, "H": 0.10, "D": 0.05},
    (6, 7): {"F": 1.00, "A": 0.90, "Rep": 0.86, "H": 0.10, "D": 0.03},
    (7, 8): {"F": 1.00, "A": 0.90, "Rep": 0.86, "H": 0.10, "D": 0.03},
}
degraded_links = set()

# Per-node trust overrides edited from the GUI: {node: {"F":..,"A":..,...}}
# Only the keys the user has changed are stored.
node_overrides = {}
METRIC_KEYS = ("F", "A", "Rep", "H", "D")
LOWER_IS_WORSE = ("F", "A", "Rep")   # for H and D, higher is worse


# -------------------- Link utilities --------------------

def normalize_link(a, b=None):
    """Accept either normalize_link((a, b)) or normalize_link(a, b)."""
    if b is None:
        a, b = a
    return (min(a, b), max(a, b))


def distance(node_a, node_b):
    x1, y1 = positions[node_a]
    x2, y2 = positions[node_b]
    return math.hypot(x2 - x1, y2 - y1)


def discover_links():
    links = []
    for a in range(NUM_NODES):
        for b in range(a + 1, NUM_NODES):
            if distance(a, b) <= TX_RANGE:
                links.append((a, b))
    return links


def get_metrics(link):
    link = normalize_link(link)
    metrics = dict(DEFAULT_METRICS)
    if link in special_metrics:
        metrics.update(special_metrics[link])
    # Node overrides: if both endpoints override a metric, the worse value wins.
    for key in METRIC_KEYS:
        values = [
            node_overrides[n][key] for n in link
            if n in node_overrides and key in node_overrides[n]
        ]
        if values:
            metrics[key] = min(values) if key in LOWER_IS_WORSE else max(values)
    if link in degraded_links:
        metrics["A"] = 0.05
        metrics["D"] = 0.95
        metrics["H"] = 0.80
    return metrics


def calculate_trust(link_or_metrics):
    """Accept a link tuple or an already retrieved metrics dictionary."""
    if isinstance(link_or_metrics, dict):
        metrics = link_or_metrics
    else:
        metrics = get_metrics(link_or_metrics)

    honesty = 1.0 - metrics["H"]
    trust = (
        W1 * metrics["F"]
        + W2 * metrics["A"]
        + W3 * metrics["Rep"]
        + W4 * honesty
    )
    return max(0.0, min(1.0, trust))


# -------------------- Lifetime, risk, cost --------------------

def calculate_link_lifetime(link):
    a, b = normalize_link(link)
    x1, y1 = positions[a]
    x2, y2 = positions[b]
    vx1, vy1 = velocities[a]
    vx2, vy2 = velocities[b]

    dx, dy = x2 - x1, y2 - y1
    dvx, dvy = vx2 - vx1, vy2 - vy1
    d = math.hypot(dx, dy)

    if d >= TX_RANGE:
        return 0.0
    if d == 0:
        return MAX_LIFETIME

    radial_velocity = (dx * dvx + dy * dvy) / d
    if radial_velocity <= 0:
        return MAX_LIFETIME

    return max(0.0, min(MAX_LIFETIME, (TX_RANGE - d) / radial_velocity))


def calculate_link_risk(link):
    metrics = get_metrics(link)
    trust = calculate_trust(metrics)
    lifetime = calculate_link_lifetime(link)
    if lifetime <= 0:
        return float("inf")
    return (1.0 - trust) + DELTA * (1.0 / lifetime) + ETA * metrics["D"]


def calculate_link_cost(link):
    metrics = get_metrics(link)
    trust = calculate_trust(metrics)
    lifetime = calculate_link_lifetime(link)
    if lifetime <= 0:
        return float("inf")
    return ALPHA + BETA * (1.0 - trust) + GAMMA * ((1.0 / lifetime) + metrics["D"])


def is_link_valid(link):
    return (
        calculate_trust(link) >= TMIN
        and calculate_link_lifetime(link) >= LMIN
    )


# -------------------- Graph and routes --------------------

def build_graph():
    graph = {node: [] for node in range(NUM_NODES)}
    for a, b in discover_links():
        if is_link_valid((a, b)):
            graph[a].append(b)
            graph[b].append(a)
    return graph


def get_route_links(route):
    if not route or len(route) < 2:
        return []
    return [normalize_link(route[i], route[i + 1]) for i in range(len(route) - 1)]


def route_hops(route):
    return max(0, len(route) - 1) if route else 0


def route_risk(route):
    links = get_route_links(route)
    if not links:
        return float("inf")
    risks = [calculate_link_risk(link) for link in links]
    if any(math.isinf(value) for value in risks):
        return float("inf")
    return sum(risks)


def route_cost(route):
    links = get_route_links(route)
    if not links:
        return float("inf")
    costs = [calculate_link_cost(link) for link in links]
    if any(math.isinf(value) for value in costs):
        return float("inf")
    return sum(costs)


def route_is_feasible(route):
    if not route or len(route) < 2:
        return False
    if route[0] != SOURCE or route[-1] != DESTINATION:
        return False
    if route_hops(route) > HMAX:
        return False
    if any(not is_link_valid(link) for link in get_route_links(route)):
        return False
    return route_risk(route) <= RMAX


def find_feasible_routes(graph, source=SOURCE, destination=DESTINATION):
    routes = []

    def visit(node, path):
        if len(path) - 1 > HMAX:
            return
        if node == destination:
            if route_is_feasible(path):
                routes.append(path.copy())
            return
        for neighbour in graph.get(node, []):
            if neighbour not in path:
                visit(neighbour, path + [neighbour])

    visit(source, [source])
    return routes


def constrained_dijkstra(graph, source=SOURCE, destination=DESTINATION):
    """Compatibility name; uses bounded simple-path enumeration and cost ranking."""
    routes = find_feasible_routes(graph, source, destination)
    if not routes:
        return None
    return min(routes, key=lambda route: (route_cost(route), route))


def get_alternative_routes(graph, source=SOURCE, destination=DESTINATION):
    return sorted(
        find_feasible_routes(graph, source, destination),
        key=lambda route: (route_cost(route), route),
    )


# -------------------- Simulation controls --------------------

def advance_simulation(seconds=5.0):
    global SIMULATION_TIME
    if seconds < 0:
        raise ValueError("Simulation time cannot move backwards.")
    for node in range(NUM_NODES):
        x, y = positions[node]
        vx, vy = velocities[node]
        positions[node] = (x + vx * seconds, y + vy * seconds)
    SIMULATION_TIME += seconds
    return SIMULATION_TIME


def degrade_link(link, b=None):
    """Accept either degrade_link((a, b)) or degrade_link(a, b)."""
    normalized = normalize_link(link, b)
    degraded_links.add(normalized)
    print(f"Link N{normalized[0]}-N{normalized[1]} has been marked as degraded.")


def reset_simulation():
    global SIMULATION_TIME
    positions.clear()
    positions.update(initial_positions)
    degraded_links.clear()
    node_overrides.clear()
    SIMULATION_TIME = 0.0


# -------------------- CSV export --------------------

def save_csv(filename="risk_aware_link_metrics.csv"):
    fields = [
        "Node_A", "Node_B", "Distance", "F", "A", "Rep",
        "False_Advertisement_Ratio_H", "D", "Trust",
        "Lifetime", "Risk", "Cost", "Eligible", "Degraded",
    ]
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for link in discover_links():
            a, b = link
            metrics = get_metrics(link)
            writer.writerow({
                "Node_A": f"N{a}",
                "Node_B": f"N{b}",
                "Distance": round(distance(a, b), 4),
                "F": metrics["F"],
                "A": metrics["A"],
                "Rep": metrics["Rep"],
                "False_Advertisement_Ratio_H": metrics["H"],
                "D": metrics["D"],
                "Trust": round(calculate_trust(metrics), 4),
                "Lifetime": round(calculate_link_lifetime(link), 4),
                "Risk": round(calculate_link_risk(link), 4),
                "Cost": round(calculate_link_cost(link), 4),
                "Eligible": is_link_valid(link),
                "Degraded": normalize_link(link) in degraded_links,
            })
    print(f"CSV exported successfully: {filename}")


# -------------------- Terminal experiment/menu --------------------

def run_complete_experiment():
    reset_simulation()
    print("\n=== RISK-AWARE MANET ROUTING EXPERIMENT ===")
    graph = build_graph()
    before = constrained_dijkstra(graph)
    print(f"Discovered links: {len(discover_links())}")
    if before is None:
        print("No feasible baseline route was found.")
        return

    print("Baseline route:", " -> ".join(f"N{x}" for x in before))
    print(f"Hops: {route_hops(before)}")
    print(f"Risk: {route_risk(before):.4f}")
    print(f"Cost: {route_cost(before):.4f}")

    print("\nAlternative routes:")
    for index, route in enumerate(get_alternative_routes(graph)[:10], 1):
        print(
            f"{index}. {' -> '.join(f'N{x}' for x in route)}"
            f" | hops={route_hops(route)}"
            f" | risk={route_risk(route):.4f}"
            f" | cost={route_cost(route):.4f}"
        )

    first_link = get_route_links(before)[0]
    degrade_link(first_link)
    after = constrained_dijkstra(build_graph())

    print("\nAfter degradation:")
    if after is None:
        print("No feasible route remains.")
    else:
        print("Selected route:", " -> ".join(f"N{x}" for x in after))
        print(f"Hops: {route_hops(after)}")
        print(f"Risk: {route_risk(after):.4f}")
        print(f"Cost: {route_cost(after):.4f}")
        print("Route changed:", "YES" if before != after else "NO")

    save_csv()


def show_menu():
    while True:
        print("\n=== RISK-AWARE MANET ROUTING ===")
        print("1. Discover links")
        print("2. Display eligible graph")
        print("3. Find best feasible route")
        print("4. Display alternative routes")
        print("5. Degrade a link")
        print("6. Advance mobility by 5 seconds")
        print("7. Reset simulation")
        print("8. Export CSV")
        print("9. Run complete experiment")
        print("0. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            print(discover_links())
        elif choice == "2":
            for node, neighbours in build_graph().items():
                print(f"N{node}: {neighbours}")
        elif choice == "3":
            route = constrained_dijkstra(build_graph())
            if route:
                print("Best route:", " -> ".join(f"N{x}" for x in route))
                print("Hops:", route_hops(route))
                print("Risk:", round(route_risk(route), 4))
                print("Cost:", round(route_cost(route), 4))
            else:
                print("No feasible route found.")
        elif choice == "4":
            routes = get_alternative_routes(build_graph())
            for index, route in enumerate(routes, 1):
                print(
                    f"{index}. {' -> '.join(f'N{x}' for x in route)}"
                    f" | risk={route_risk(route):.4f}"
                    f" | cost={route_cost(route):.4f}"
                )
            if not routes:
                print("No feasible routes found.")
        elif choice == "5":
            try:
                a = int(input("First node ID (0-9): "))
                b = int(input("Second node ID (0-9): "))
                if a not in range(NUM_NODES) or b not in range(NUM_NODES) or a == b:
                    print("Invalid node IDs.")
                elif normalize_link(a, b) not in discover_links():
                    print("These nodes are not currently within transmission range.")
                else:
                    degrade_link(a, b)
            except ValueError:
                print("Please enter integer node IDs.")
        elif choice == "6":
            advance_simulation(5.0)
            print(f"Simulation time: {SIMULATION_TIME:.1f} seconds")
        elif choice == "7":
            reset_simulation()
            print("Simulation reset.")
        elif choice == "8":
            save_csv()
        elif choice == "9":
            run_complete_experiment()
        elif choice == "0":
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    show_menu()
