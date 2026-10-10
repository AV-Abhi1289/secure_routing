"""
RISK-AWARE OPTIMAL ROUTING IN MANETs
Graphical visualization connected to risk_aware_manet.py
"""

import math
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

import risk_aware_manet as core


# ============================================================
# 1. APPLICATION STATE
# ============================================================

baseline_route = None
baseline_risk = None
baseline_cost = None
baseline_hops = None

degraded_link = None
status_message = "Baseline network loaded."
buttons = []


# ============================================================
# 2. ROUTING ENGINE CONNECTION
# ============================================================

def find_best_route():
    graph = core.build_graph()
    return core.constrained_dijkstra(
        graph, core.SOURCE, core.DESTINATION
    )


def get_alternative_routes():
    graph = core.build_graph()
    return core.get_alternative_routes(graph)


def route_text(path):
    if not path:
        return "No feasible route"
    return " -> ".join(f"N{node}" for node in path)


def safe_number(value, digits=4):
    if math.isinf(value):
        return "INF"
    return f"{value:.{digits}f}"


def route_summary(path):
    if not path:
        return None

    return {
        "route": list(path),
        "hops": core.route_hops(path),
        "risk": core.route_risk(path),
        "cost": core.route_cost(path)
    }


def capture_baseline():
    global baseline_route, baseline_risk
    global baseline_cost, baseline_hops

    baseline_route = find_best_route()

    if baseline_route:
        baseline_hops = core.route_hops(baseline_route)
        baseline_risk = core.route_risk(baseline_route)
        baseline_cost = core.route_cost(baseline_route)
    else:
        baseline_hops = None
        baseline_risk = None
        baseline_cost = None


# ============================================================
# 3. BUILD THE PHYSICAL NETWORK
# ============================================================

def build_physical_graph():
    graph = nx.Graph()
    graph.add_nodes_from(range(core.NUM_NODES))
    graph.add_edges_from(core.discover_links())
    return graph


def link_is_degraded(link):
    normalized = core.normalize_link(link[0], link[1])
    return normalized in core.degraded_links


def link_filter_reason(link):
    trust = core.calculate_trust(link)
    lifetime = core.calculate_link_lifetime(link)
    reasons = []

    if trust < core.TMIN:
        reasons.append("Low trust")

    if lifetime < core.LMIN:
        reasons.append("Short lifetime")

    return ", ".join(reasons)


# ============================================================
# 4. CREATE THE GRAPHICAL WINDOW
# ============================================================

fig, ax = plt.subplots(figsize=(16, 9))

plt.subplots_adjust(
    left=0.035,
    right=0.61,
    top=0.90,
    bottom=0.19
)

metrics_display = fig.text(
    0.63, 0.88, "",
    fontsize=9,
    verticalalignment="top",
    family="monospace"
)


# ============================================================
# 5. DRAW THE NETWORK
# ============================================================

def draw_network():
    ax.clear()
    graph = build_physical_graph()

    positions = {
        node: tuple(core.positions[node])
        for node in range(core.NUM_NODES)
    }

    selected_route = find_best_route()

    eligible_edges = []
    filtered_edges = []
    degraded_edges = []

    for u, v in graph.edges():
        link = core.normalize_link(u, v)

        if link_is_degraded(link):
            degraded_edges.append((u, v))
        elif core.is_link_valid(link):
            eligible_edges.append((u, v))
        else:
            filtered_edges.append((u, v))

    nx.draw_networkx_edges(
        graph, positions, ax=ax,
        edgelist=eligible_edges,
        edge_color="gray", width=1.3, alpha=0.8
    )

    if filtered_edges:
        nx.draw_networkx_edges(
            graph, positions, ax=ax,
            edgelist=filtered_edges,
            edge_color="orange",
            style="dashed", width=2.0
        )

    if degraded_edges:
        nx.draw_networkx_edges(
            graph, positions, ax=ax,
            edgelist=degraded_edges,
            edge_color="red",
            style="dashed", width=3.0
        )

    if selected_route and len(selected_route) > 1:
        route_edges = list(
            zip(selected_route[:-1], selected_route[1:])
        )

        nx.draw_networkx_edges(
            graph, positions, ax=ax,
            edgelist=route_edges,
            edge_color="green", width=4.0
        )

    node_colors = []

    for node in graph.nodes():
        if node == core.SOURCE:
            node_colors.append("limegreen")
        elif node == core.DESTINATION:
            node_colors.append("gold")
        else:
            node_colors.append("skyblue")

    nx.draw_networkx_nodes(
        graph, positions, ax=ax,
        node_color=node_colors,
        node_size=750,
        edgecolors="black"
    )

    nx.draw_networkx_labels(
        graph, positions, ax=ax,
        labels={node: f"N{node}" for node in graph.nodes()},
        font_size=10,
        font_weight="bold"
    )

    ax.set_title(
        "Risk-Aware Optimal Routing in MANETs",
        fontsize=15, fontweight="bold"
    )

    ax.set_xlabel(
        "Grey: Eligible | Orange dashed: Filtered | "
        "Red dashed: Degraded | Green: Selected route"
    )

    ax.set_aspect("equal", adjustable="datalim")
    ax.margins(0.12)
    ax.axis("off")

    # ---------------- Metrics panel ----------------

    current = route_summary(selected_route)
    physical_count = len(core.discover_links())

    eligible_count = sum(
        1 for link in core.discover_links()
        if core.is_link_valid(link)
    )

    filtered_count = physical_count - eligible_count

    degraded_text = (
        f"N{degraded_link[0]}-N{degraded_link[1]}"
        if degraded_link is not None else "None"
    )

    if current:
        changed_text = (
            "YES" if baseline_route is not None
            and current["route"] != baseline_route else "NO"
        )

        risk_status = (
            "PASS" if current["risk"] <= core.RMAX else "FAIL"
        )

        hop_status = (
            "PASS" if current["hops"] <= core.HMAX else "FAIL"
        )

        if baseline_risk is None:
            comparison = "Baseline metrics unavailable"
        else:
            comparison = (
                f"Baseline route: {route_text(baseline_route)}\n"
                f"Baseline hops: {baseline_hops}\n"
                f"Baseline risk: {baseline_risk:.4f}\n"
                f"Baseline cost: {baseline_cost:.4f}\n"
                f"Route changed: {changed_text}\n"
                f"Risk change vs baseline: "
                f"{current['risk'] - baseline_risk:+.4f}\n"
                f"Cost change vs baseline: "
                f"{current['cost'] - baseline_cost:+.4f}"
            )

        current_metrics = (
            "CURRENT ROUTE\n"
            f"Route: {route_text(selected_route)}\n"
            f"Hops: {current['hops']} "
            f"(limit {core.HMAX}) [{hop_status}]\n"
            f"Risk: {current['risk']:.4f} "
            f"(limit {core.RMAX}) [{risk_status}]\n"
            f"Cost: {current['cost']:.4f}\n\n"
            f"BASELINE COMPARISON\n{comparison}\n\n"
        )
    else:
        current_metrics = (
            "CURRENT ROUTE\nNo feasible route found.\n\n"
        )

    parameters = (
        "NETWORK AND PARAMETERS\n"
        f"Nodes: {core.NUM_NODES}\n"
        f"Source: N{core.SOURCE}\n"
        f"Destination: N{core.DESTINATION}\n"
        f"Transmission range: {core.TX_RANGE:.1f} m\n"
        f"Discovered links: {physical_count}\n"
        f"Eligible links: {eligible_count}\n"
        f"Filtered links: {filtered_count}\n"
        f"Tmin: {core.TMIN}\n"
        f"Lmin: {core.LMIN:.1f} s\n"
        f"Rmax: {core.RMAX}\n"
        f"Hmax: {core.HMAX}\n"
        f"Alpha: {core.ALPHA}  Beta: {core.BETA}\n"
        f"Delta: {core.DELTA}  Eta: {core.ETA}\n"
        f"Simulation time: {core.SIMULATION_TIME:.1f} s\n"
        f"Degraded link: {degraded_text}\n"
    )

    metrics_display.set_text(
        f"STATUS: {status_message}\n\n"
        f"{current_metrics}{parameters}"
    )

    fig.canvas.draw_idle()


# ============================================================
# 6. RESET / BASELINE BUTTON
# ============================================================

def reset_baseline(event):
    global degraded_link, status_message

    core.reset_simulation()
    degraded_link = None
    capture_baseline()

    status_message = "Baseline restored."
    draw_network()


# ============================================================
# 7. DEGRADE LINK BUTTON
# ============================================================

def degrade_baseline_link(event):
    global degraded_link, status_message

    if degraded_link is not None:
        status_message = "A link is already degraded. Reset first."
        draw_network()
        return

    route = find_best_route()

    if not route or len(route) < 2:
        status_message = "No feasible route available to degrade."
        draw_network()
        return

    degraded_link = core.normalize_link(route[0], route[1])
    core.degrade_link(degraded_link)

    status_message = (
        f"Degraded N{degraded_link[0]}-{degraded_link[1]}; "
        "route recalculated."
    )

    draw_network()


# ============================================================
# 8. RECALCULATE ROUTE BUTTON
# ============================================================

def recalculate_route(event):
    global status_message

    status_message = "Route recalculated using the routing engine."
    draw_network()


# ============================================================
# 9. MOBILITY BUTTON
# ============================================================

def advance_mobility(event):
    global status_message

    core.advance_simulation(5.0)
    status_message = "Mobility advanced by 5 seconds."
    draw_network()


# ============================================================
# 10. LINK METRICS TABLE
# ============================================================

def show_link_metrics(event):
    links = core.discover_links()

    columns = [
        "Link", "Dist", "F", "ACK", "Rep",
        "H", "D", "Trust", "Lifetime",
        "Risk", "Cost", "Status"
    ]

    rows = []

    for link in links:
        metrics = core.get_metrics(link)
        trust = core.calculate_trust(link)
        lifetime = core.calculate_link_lifetime(link)
        risk = core.calculate_link_risk(link)
        cost = core.calculate_link_cost(link)
        link_distance = core.distance(link[0], link[1])

        if link_is_degraded(link):
            status = "DEGRADED"
        elif not core.is_link_valid(link):
            status = link_filter_reason(link)
        else:
            status = "ELIGIBLE"

        rows.append([
            f"N{link[0]}-N{link[1]}",
            f"{link_distance:.1f}",
            f"{metrics['F']:.2f}",
            f"{metrics['A']:.2f}",
            f"{metrics['Rep']:.2f}",
            f"{metrics['H']:.2f}",
            f"{metrics['D']:.2f}",
            f"{trust:.3f}",
            f"{lifetime:.1f}",
            safe_number(risk, 3),
            safe_number(cost, 3),
            status
        ])

    table_fig, table_ax = plt.subplots(figsize=(17, 10))
    table_ax.axis("off")

    table_ax.set_title(
        "Detailed Link Metrics — Values from Routing Engine",
        fontsize=14, fontweight="bold", pad=20
    )

    table = table_ax.table(
        cellText=rows,
        colLabels=columns,
        loc="center",
        cellLoc="center"
    )

    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.0, 1.35)

    table_ax.text(
        0.01, 0.02,
        "F = Forwarding | ACK = ACK reliability | "
        "Rep = Reputation | H = False-advertisement ratio | "
        "D = Drop ratio\n"
        "Trust < Tmin or Lifetime < Lmin means the link is "
        "excluded from routing.",
        transform=table_ax.transAxes,
        fontsize=9,
        verticalalignment="bottom"
    )

    table_fig.tight_layout()
    plt.show()


# ============================================================
# 11. ALTERNATIVE ROUTES TABLE
# ============================================================

def show_alternative_routes(event):
    routes = get_alternative_routes()

    columns = [
        "Rank", "Route", "Hops",
        "Total Risk", "Total Cost", "Selected?"
    ]

    selected = find_best_route()
    rows = []

    for rank, path in enumerate(routes[:15], start=1):
        selected_text = "YES" if path == selected else "No"

        rows.append([
            rank,
            route_text(path),
            core.route_hops(path),
            f"{core.route_risk(path):.4f}",
            f"{core.route_cost(path):.4f}",
            selected_text
        ])

    if not rows:
        rows = [["-", "No feasible routes", "-", "-", "-", "-"]]

    table_fig, table_ax = plt.subplots(figsize=(13, 8))
    table_ax.axis("off")

    table_ax.set_title(
        "Feasible Alternative Routes — Sorted by Cost",
        fontsize=14, fontweight="bold", pad=20
    )

    table = table_ax.table(
        cellText=rows,
        colLabels=columns,
        loc="center",
        cellLoc="center"
    )

    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.5)

    table_ax.text(
        0.01, 0.02,
        "Routes are generated by the routing engine and must "
        "satisfy link eligibility, Rmax and Hmax.",
        transform=table_ax.transAxes,
        fontsize=9
    )

    table_fig.tight_layout()
    plt.show()


# ============================================================
# 12. CSV EXPORT BUTTON
# ============================================================

def save_link_metrics(event):
    global status_message

    try:
        core.save_csv()
        status_message = "CSV export requested."
    except Exception as error:
        status_message = f"CSV export failed: {error}"

    draw_network()


# ============================================================
# 13. CREATE BUTTONS
# ============================================================

def create_button(rectangle, label, callback):
    button_axis = plt.axes(rectangle)
    button = Button(button_axis, label)
    button.on_clicked(callback)
    buttons.append(button)


create_button(
    [0.035, 0.095, 0.13, 0.055],
    "Reset / Baseline", reset_baseline
)

create_button(
    [0.175, 0.095, 0.12, 0.055],
    "Degrade Link", degrade_baseline_link
)

create_button(
    [0.305, 0.095, 0.12, 0.055],
    "Recalculate", recalculate_route
)

create_button(
    [0.435, 0.095, 0.12, 0.055],
    "Move +5 s", advance_mobility
)

create_button(
    [0.08, 0.025, 0.18, 0.05],
    "Show Link Metrics", show_link_metrics
)

create_button(
    [0.285, 0.025, 0.18, 0.05],
    "Show Alternative Routes", show_alternative_routes
)

create_button(
    [0.49, 0.025, 0.13, 0.05],
    "Save CSV", save_link_metrics
)


# ============================================================
# 14. INITIALIZE THE APPLICATION
# ============================================================

core.reset_simulation()
capture_baseline()
draw_network()
plt.show()
