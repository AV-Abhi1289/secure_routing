"""
RISK-AWARE OPTIMAL ROUTING IN MANETs
Graphical visualization connected to risk_aware_manet.py
"""

import math
import textwrap
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider

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

selected_node = None
sliders = {}
slider_updating = False
METRIC_LABELS = {"F": "F (forward)", "A": "ACK", "Rep": "Rep",
                 "H": "H (false adv.)", "D": "D (drop)"}


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
    bottom=0.28
)

metrics_display = fig.text(
    0.63, 0.88, "",
    fontsize=9,
    verticalalignment="top",
    family="monospace"
)
metrics_display.set_fontsize(8.5)


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

    edge_colors, edge_widths = [], []
    for node in graph.nodes():
        if node == selected_node:
            edge_colors.append("red")
            edge_widths.append(4.0)
        elif node in core.node_overrides and core.node_overrides[node]:
            edge_colors.append("purple")
            edge_widths.append(3.0)
        else:
            edge_colors.append("black")
            edge_widths.append(1.0)

    nx.draw_networkx_nodes(
        graph, positions, ax=ax,
        node_color=node_colors,
        node_size=750,
        edgecolors=edge_colors,
        linewidths=edge_widths
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
        "Red dashed: Degraded | Green: Selected route\n"
        "Click a node to edit its trust stats | "
        "Red ring: selected | Purple ring: edited"
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
        f"Src N{core.SOURCE} -> Dst N{core.DESTINATION} | "
        f"Range {core.TX_RANGE:.0f} m | Time {core.SIMULATION_TIME:.0f} s\n"
        f"Links: {physical_count} found, {eligible_count} eligible, "
        f"{filtered_count} filtered\n"
        f"Tmin {core.TMIN} | Lmin {core.LMIN:.0f} s | "
        f"Rmax {core.RMAX} | Hmax {core.HMAX}\n"
        f"Alpha {core.ALPHA} Beta {core.BETA} | "
        f"Delta {core.DELTA} Eta {core.ETA}\n"
        f"Degraded link: {degraded_text}\n"
    )

    metrics_display.set_text(
        f"{textwrap.fill('STATUS: ' + status_message, 62)}\n\n"
        f"{selected_node_text()}"
        f"{current_metrics}{parameters}"
    )

    fig.canvas.draw_idle()



# ============================================================
# 5b. NODE SELECTION AND EDITING
# ============================================================

def node_value(node, key):
    """Override if set, otherwise the average over the node's links."""
    override = core.node_overrides.get(node, {})
    if key in override:
        return override[key]

    values = [
        core.get_metrics(link)[key]
        for link in core.discover_links() if node in link
    ]
    if values:
        return sum(values) / len(values)
    return core.DEFAULT_METRICS[key]


def selected_node_text():
    if selected_node is None:
        return "SELECTED NODE\nClick a node to edit its stats.\n\n"

    n = selected_node
    override = core.node_overrides.get(n, {})
    edited = ", ".join(
        f"{k}={v:.2f}" for k, v in override.items()
    ) or "none"

    lines = [f"SELECTED NODE: N{n}", f"Edited values: {edited}",
             "Link   Trust Life  Risk  Status"]

    incident = [l for l in core.discover_links() if n in l]
    incident.sort(key=lambda l: core.calculate_link_risk(l), reverse=True)
    hidden = max(0, len(incident) - 5)

    for link in incident[:5]:
        trust = core.calculate_trust(link)
        life = core.calculate_link_lifetime(link)
        risk = core.calculate_link_risk(link)

        if link_is_degraded(link):
            status = "DEGRADED"
        elif core.is_link_valid(link):
            status = "ok"
        else:
            status = link_filter_reason(link)

        lines.append(
            f"N{link[0]}-N{link[1]}  {trust:.2f}  {life:5.1f} "
            f"{safe_number(risk, 2):>5} {status}"
        )

    if hidden:
        lines.append(f"... {hidden} more links (highest risk shown)")

    return "\n".join(lines) + "\n\n"


def sync_sliders():
    global slider_updating
    slider_updating = True
    for key, slider in sliders.items():
        slider.set_val(
            node_value(selected_node, key)
            if selected_node is not None else 0.0
        )
    slider_updating = False


def on_node_click(event):
    global selected_node, status_message

    if event.inaxes is not ax or event.button != 1:
        return
    if event.xdata is None or event.ydata is None:
        return

    best, best_distance = None, 7.0
    for node in range(core.NUM_NODES):
        x, y = core.positions[node]
        d = math.hypot(event.xdata - x, event.ydata - y)
        if d < best_distance:
            best, best_distance = node, d

    if best is None:
        return

    selected_node = best
    status_message = f"Selected N{best}. Use the sliders to edit its stats."
    sync_sliders()
    draw_network()


def make_slider_handler(key):
    def handler(value):
        global status_message
        if slider_updating or selected_node is None:
            return
        core.node_overrides.setdefault(selected_node, {})[key] = round(value, 2)
        status_message = (
            f"N{selected_node}: {key} set to {value:.2f}; "
            "route recalculated."
        )
        draw_network()
    return handler


def reset_selected_node(event):
    global status_message
    if selected_node is None:
        status_message = "No node selected."
    else:
        core.node_overrides.pop(selected_node, None)
        status_message = f"N{selected_node} stats restored to defaults."
        sync_sliders()
    draw_network()


# ============================================================
# 6. RESET / BASELINE BUTTON
# ============================================================

def reset_baseline(event):
    global degraded_link, status_message

    core.reset_simulation()
    degraded_link = None
    capture_baseline()

    status_message = "Baseline restored."
    sync_sliders()
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
# 12b. DEMO PRESETS
# ============================================================

BAD = {"H": 0.90, "D": 0.80, "A": 0.10}

PRESETS = [
    {
        "label": "Malicious\nRelay N7",
        "text": "Malicious relay: N7 now advertises falsely and drops "
                "packets, so the route avoids it.",
        "overrides": {7: dict(BAD)},
        "select": 7,
    },
    {
        "label": "Two Bad\nRelays",
        "text": "Two compromised relays (N7, N2): a longer 3-hop route "
                "is chosen to avoid both.",
        "overrides": {7: dict(BAD), 2: dict(BAD)},
        "select": 7,
    },
    {
        "label": "Suspicious\nN7",
        "text": "Mildly suspicious N7 (low Rep, some drops): route is "
                "kept but its risk rises sharply.",
        "overrides": {7: {"Rep": 0.30, "D": 0.40}},
        "select": 7,
    },
    {
        "label": "Mobility\n+120 s",
        "text": "Nodes drift for 120 s: link lifetimes change and "
                "the route moves to N3.",
        "overrides": {},
        "advance": 120.0,
        "select": None,
    },
    {
        "label": "Total\nBlackout",
        "text": "All relays N1-N8 compromised: no feasible route "
                "satisfies the constraints.",
        "overrides": {n: dict(BAD) for n in range(1, 9)},
        "select": None,
    },
]


def apply_preset(preset):
    global degraded_link, selected_node, status_message

    # Clean network first, so the baseline comparison is always
    # against the healthy network.
    core.reset_simulation()
    degraded_link = None
    capture_baseline()

    for node, values in preset["overrides"].items():
        core.node_overrides[node] = dict(values)

    if preset.get("advance"):
        core.advance_simulation(preset["advance"])

    selected_node = preset.get("select")
    status_message = "PRESET - " + preset["text"]

    sync_sliders()
    draw_network()


def make_preset_callback(preset):
    return lambda event: apply_preset(preset)


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


# ---------------- Demo preset buttons ----------------

fig.text(0.035, 0.225, "DEMO PRESETS", fontsize=9, fontweight="bold")

for index, preset in enumerate(PRESETS):
    create_button(
        [0.035 + index * 0.117, 0.165, 0.105, 0.055],
        preset["label"], make_preset_callback(preset)
    )
    buttons[-1].label.set_fontsize(8)

# ---------------- Node editing controls ----------------

fig.text(0.78, 0.205, "EDIT SELECTED NODE", fontsize=9,
         fontweight="bold")

for index, key in enumerate(core.METRIC_KEYS):
    slider_axis = plt.axes([0.78, 0.17 - index * 0.026, 0.16, 0.018])
    slider = Slider(slider_axis, METRIC_LABELS[key], 0.0, 1.0,
                    valinit=0.0, valstep=0.01)
    slider.label.set_fontsize(8)
    slider.valtext.set_fontsize(8)
    slider.on_changed(make_slider_handler(key))
    sliders[key] = slider

create_button(
    [0.78, 0.015, 0.16, 0.03],
    "Reset Selected Node", reset_selected_node
)

fig.canvas.mpl_connect("button_press_event", on_node_click)


# ============================================================
# 14. INITIALIZE THE APPLICATION
# ============================================================

core.reset_simulation()
capture_baseline()
draw_network()
plt.show()
