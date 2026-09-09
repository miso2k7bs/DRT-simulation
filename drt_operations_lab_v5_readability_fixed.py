# -*- coding: utf-8 -*-
import math
import random
import statistics
from typing import Dict, List, Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# =========================================================
# PAGE / THEME
# =========================================================
st.set_page_config(
    page_title="Songdo 8 DRT Operations Lab",
    page_icon="🚌",
    layout="wide",
)

st.markdown("""
<style>
:root{
  --navy:#172033;
  --blue:#3559c7;
  --teal:#20a39e;
  --muted:#667085;
  --soft:#f6f8fb;
  --line:#e6eaf0;
}
.block-container{
  padding-top:1.15rem;
  padding-bottom:2.6rem;
  max-width:1480px;
}
.hero{
  border-radius:22px;
  padding:24px 28px;
  background:
    radial-gradient(circle at 92% 12%, rgba(53,89,199,.18), transparent 26%),
    linear-gradient(135deg, #f8fafc 0%, #eef3fb 100%);
  border:1px solid #e5eaf2;
  margin-bottom:18px;
}
.eyebrow{
  font-size:.76rem;
  font-weight:800;
  letter-spacing:.12em;
  color:#52617a;
  text-transform:uppercase;
}
.hero-title{
  font-size:2.35rem;
  font-weight:900;
  letter-spacing:-.045em;
  color:#182132;
  line-height:1.13;
  margin:.25rem 0 .45rem 0;
}
.hero-sub{
  color:#667085;
  font-size:.98rem;
  line-height:1.55;
}
.section-kicker{
  font-size:.75rem;
  font-weight:850;
  letter-spacing:.11em;
  color:#64748b;
  text-transform:uppercase;
  margin-top:10px;
}
.section-title{
  font-size:1.5rem;
  font-weight:850;
  color:#1f2937;
  margin:.25rem 0 .8rem 0;
}
.config-shell{
  padding:18px 20px 8px 20px;
  border:1px solid #e4e9f0;
  border-radius:20px;
  background:linear-gradient(180deg,#ffffff 0%,#fafbfd 100%);
  margin-bottom:16px;
}
.result-strip{
  padding:14px 18px;
  border-radius:16px;
  border:1px solid #e6eaf0;
  background:#fff;
}
.status-good{
  display:inline-block;
  padding:6px 11px;
  border-radius:999px;
  font-size:.82rem;
  font-weight:850;
  color:#0f766e;
  background:#ecfdf5;
  border:1px solid #bbf7d0;
}
.status-warn{
  display:inline-block;
  padding:6px 11px;
  border-radius:999px;
  font-size:.82rem;
  font-weight:850;
  color:#92400e;
  background:#fff7ed;
  border:1px solid #fed7aa;
}
.logic-card{
  border:1px solid #d9e0e8;
  border-radius:16px;
  padding:17px 19px;
  background:#ffffff;
  min-height:140px;
}
.logic-num{
  font-size:.80rem;
  font-weight:900;
  color:#334155;
  letter-spacing:.08em;
}
.logic-title{
  font-size:1.08rem;
  font-weight:900;
  color:#0f172a;
  margin:5px 0 8px 0;
}
.logic-text{
  font-size:1.00rem;
  color:#111827;
  line-height:1.62;
  font-weight:550;
}
[data-testid="stCaptionContainer"] p{
  color:#374151 !important;
  font-size:.90rem !important;
  line-height:1.55 !important;
  font-weight:500 !important;
}

.empty-state{
  padding:42px 28px;
  border:1px dashed #cbd5e1;
  border-radius:18px;
  background:#fafbfd;
  text-align:center;
  color:#64748b;
}
[data-testid="stMetric"]{
  border:1px solid #e4e9f0;
  border-radius:16px;
  padding:14px 16px;
  background:#fff;
}
[data-testid="stMetricValue"]{
  font-size:1.95rem;
  color:#1f2937;
}
div[data-testid="stButton"]>button,
div[data-testid="stFormSubmitButton"]>button{
  border-radius:13px;
  font-weight:850;
  min-height:46px;
}
hr{border-color:#edf0f4;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">Urban Mobility Optimization / Rule-Based DRT</div>
  <div class="hero-title">송도 8공구 DRT 운영 최적화 시뮬레이터</div>
  <div class="hero-sub">
    수요 규모와 경제성 조건을 설정한 뒤, 규칙 기반 동적 배차를 반복 시뮬레이션하여
    사회적 총비용이 최소가 되는 차량 공급 규모를 산출합니다.
  </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# RESEARCH CONSTANTS
# =========================================================
ANALYSIS_MINUTES = 120
FLEET_RANGE = range(1, 9)
REPLICATIONS = 50
BASE_SEED = 2026

DRT_CAPACITY = 10
DRT_MIN_BATCH = 2
DRT_MAX_HOLD_MIN = 4
DRT_PICKUP_SERVICE_MIN = 1
PEAK_WEIGHTS = [5, 10, 15, 20, 20, 15, 10, 5]

COMPLEXES: Dict[str, Dict[str, float]] = {
    "송도SK뷰": {"households": 2100, "oneway_min": 4.0, "oneway_km": 1.1},
    "호반써밋송도": {"households": 1820, "oneway_min": 4.5, "oneway_km": 1.2},
    "e편한세상송도": {"households": 2708, "oneway_min": 6.0, "oneway_km": 1.5},
    "더샵송도마리나베이": {"households": 3100, "oneway_min": 8.0, "oneway_km": 2.2},
}

SCHEMATIC_POS = {
    "송도SK뷰": (1.15, 4.35),
    "호반써밋송도": (2.15, 3.22),
    "e편한세상송도": (1.20, 1.95),
    "더샵송도마리나베이": (2.65, 0.72),
    "송도달빛축제공원역": (6.15, 2.55),
}

FIXED_ROUTE_ORDER = list(COMPLEXES.keys())
FIXED_ROUTE_SEGMENT_MIN = [4.0, 2.0, 4.0, 4.0, 8.0]
FIXED_ROUTE_SEGMENT_KM = [1.1, 0.5, 1.0, 1.0, 2.2]
FIXED_BUS_CAPACITY = 25
FIXED_BUS_DWELL_MIN = 1

# =========================================================
# MODEL FUNCTIONS
# =========================================================
def largest_remainder(total: int, shares: Dict[Any, float]) -> Dict[Any, int]:
    share_sum = sum(shares.values())
    raw = {k: total * v / share_sum for k, v in shares.items()}
    counts = {k: int(math.floor(v)) for k, v in raw.items()}
    remainder = total - sum(counts.values())
    ranked = sorted(raw, key=lambda k: raw[k] - counts[k], reverse=True)
    for k in ranked[:remainder]:
        counts[k] += 1
    return counts

def percentile(values: List[float], p: float) -> float:
    ordered = sorted(values)
    idx = max(0, math.ceil(p * len(ordered)) - 1)
    return ordered[idx]

def generate_demand(total_passengers: int, seed: int) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    complex_counts = largest_remainder(
        total_passengers,
        {name: data["households"] for name, data in COMPLEXES.items()}
    )
    time_bin_counts = largest_remainder(
        total_passengers,
        {idx: weight for idx, weight in enumerate(PEAK_WEIGHTS)}
    )

    request_times = []
    for bin_idx, count in time_bin_counts.items():
        lo = bin_idx * 15
        hi = (bin_idx + 1) * 15
        request_times.extend(rng.uniform(lo, hi) for _ in range(count))

    origins = []
    for name, count in complex_counts.items():
        origins.extend([name] * count)

    rng.shuffle(request_times)
    rng.shuffle(origins)

    requests = [
        {"passenger_id": i + 1, "origin": origin, "request_min": request_time}
        for i, (origin, request_time) in enumerate(zip(origins, request_times))
    ]
    return sorted(requests, key=lambda x: x["request_min"])

def simulate_drt(demand, fleet, seed, value_of_time, fixed_cost_per_hour, variable_cost_per_km,
                 time_step=0.25):
    requests = generate_demand(demand, seed)
    request_index = 0
    waiting = {name: [] for name in COMPLEXES}
    vehicles = [{"trip": None, "busy_until": 0.0} for _ in range(fleet)]
    served = []
    total_vehicle_km = 0.0
    current_time = 0.0

    while True:
        while request_index < len(requests) and requests[request_index]["request_min"] <= current_time + 1e-9:
            req = requests[request_index]
            waiting[req["origin"]].append(req)
            request_index += 1

        for vehicle in vehicles:
            trip = vehicle["trip"]
            if trip is not None and vehicle["busy_until"] <= current_time + 1e-9:
                for passenger in trip["passengers"]:
                    served.append({
                        "wait_min": trip["pickup_min"] - passenger["request_min"],
                        "ride_min": trip["return_min"] - trip["pickup_min"],
                        "arrival_min": trip["return_min"],
                    })
                vehicle["trip"] = None

        for vehicle in vehicles:
            if vehicle["trip"] is not None:
                continue

            eligible = []
            for origin, queue in waiting.items():
                if not queue:
                    continue

                queue.sort(key=lambda p: p["request_min"])
                oldest_wait = current_time - queue[0]["request_min"]

                dispatch_allowed = (
                    len(queue) >= DRT_MIN_BATCH
                    or oldest_wait >= DRT_MAX_HOLD_MIN
                    or request_index >= len(requests)
                )
                if not dispatch_allowed:
                    continue

                score = (
                    (oldest_wait + 1)
                    * min(len(queue), DRT_CAPACITY)
                    / (2 * COMPLEXES[origin]["oneway_min"] + 1)
                )
                eligible.append((score, origin))

            if not eligible:
                continue

            _, origin = max(eligible)
            waiting[origin].sort(key=lambda p: p["request_min"])
            passengers = waiting[origin][:DRT_CAPACITY]
            waiting[origin] = waiting[origin][DRT_CAPACITY:]

            one_way_min = COMPLEXES[origin]["oneway_min"]
            pickup_min = current_time + one_way_min + DRT_PICKUP_SERVICE_MIN
            return_min = pickup_min + one_way_min

            vehicle["trip"] = {
                "passengers": passengers,
                "pickup_min": pickup_min,
                "return_min": return_min,
            }
            vehicle["busy_until"] = return_min
            total_vehicle_km += 2 * COMPLEXES[origin]["oneway_km"]

        finished = (
            request_index >= len(requests)
            and all(not q for q in waiting.values())
            and all(v["trip"] is None for v in vehicles)
        )
        if finished:
            break

        current_time += time_step
        if current_time > 600:
            raise RuntimeError("시뮬레이션 시간이 비정상적으로 길어졌습니다.")

    waits = [r["wait_min"] for r in served]
    rides = [r["ride_min"] for r in served]
    service_end_min = max([float(ANALYSIS_MINUTES)] + [r["arrival_min"] for r in served])

    paid_vehicle_hours = fleet * service_end_min / 60
    operating_cost = fixed_cost_per_hour * paid_vehicle_hours + variable_cost_per_km * total_vehicle_km
    passenger_time_cost = sum(
        (r["wait_min"] + r["ride_min"]) / 60 * value_of_time
        for r in served
    )

    return {
        "fleet": fleet,
        "avg_wait_min": statistics.mean(waits),
        "p95_wait_min": percentile(waits, 0.95),
        "avg_ride_min": statistics.mean(rides),
        "total_vehicle_km": total_vehicle_km,
        "operating_cost_krw": operating_cost,
        "passenger_time_cost_krw": passenger_time_cost,
        "social_cost_krw": operating_cost + passenger_time_cost,
    }

def simulate_fixed_route(demand, seed, value_of_time, fixed_cost_per_hour=30000,
                         variable_cost_per_km=550):
    requests = generate_demand(demand, seed)
    queues = {
        origin: sorted(
            [r for r in requests if r["origin"] == origin],
            key=lambda x: x["request_min"]
        )
        for origin in COMPLEXES
    }

    current_departure = 0.0
    served = []
    total_vehicle_km = 0.0
    cycles = 0

    while any(queues[o] for o in queues):
        onboard = []
        current_time = current_departure

        for stop_idx, origin in enumerate(FIXED_ROUTE_ORDER):
            current_time += FIXED_ROUTE_SEGMENT_MIN[stop_idx]
            available = [p for p in queues[origin] if p["request_min"] <= current_time]
            remaining_capacity = max(0, FIXED_BUS_CAPACITY - len(onboard))
            boarding = available[:remaining_capacity]
            boarding_ids = {p["passenger_id"] for p in boarding}
            queues[origin] = [
                p for p in queues[origin]
                if p["passenger_id"] not in boarding_ids
            ]
            onboard.extend((p, current_time) for p in boarding)
            current_time += FIXED_BUS_DWELL_MIN

        current_time += FIXED_ROUTE_SEGMENT_MIN[-1]

        for passenger, pickup_min in onboard:
            served.append({
                "wait_min": pickup_min - passenger["request_min"],
                "ride_min": current_time - pickup_min,
                "arrival_min": current_time,
            })

        current_departure = current_time
        total_vehicle_km += sum(FIXED_ROUTE_SEGMENT_KM)
        cycles += 1

        if cycles > 100:
            raise RuntimeError("고정노선 시뮬레이션 오류")

    waits = [r["wait_min"] for r in served]
    rides = [r["ride_min"] for r in served]
    service_end_min = max(float(ANALYSIS_MINUTES), current_departure)

    operating_cost = fixed_cost_per_hour * service_end_min / 60 + variable_cost_per_km * total_vehicle_km
    passenger_time_cost = sum(
        (r["wait_min"] + r["ride_min"]) / 60 * value_of_time
        for r in served
    )

    return {
        "avg_wait_min": statistics.mean(waits),
        "avg_ride_min": statistics.mean(rides),
        "social_cost_krw": operating_cost + passenger_time_cost,
    }

def average_dict(rows):
    result = {"fleet": rows[0]["fleet"]} if "fleet" in rows[0] else {}
    for k in rows[0]:
        if k == "fleet":
            continue
        result[k] = statistics.mean(r[k] for r in rows)
    return result

@st.cache_data(show_spinner=False)
def run_scenario(demand, value_of_time, fixed_cost_per_hour, variable_cost_per_km):
    all_rows = []
    for fleet in FLEET_RANGE:
        reps = [
            simulate_drt(
                demand=demand,
                fleet=fleet,
                seed=BASE_SEED * 1000 + demand * 10 + rep,
                value_of_time=value_of_time,
                fixed_cost_per_hour=fixed_cost_per_hour,
                variable_cost_per_km=variable_cost_per_km,
            )
            for rep in range(REPLICATIONS)
        ]
        all_rows.append(average_dict(reps))

    df = pd.DataFrame(all_rows)
    optimum = df.loc[df["social_cost_krw"].idxmin()].to_dict()

    fixed_reps = [
        simulate_fixed_route(
            demand=demand,
            seed=BASE_SEED * 1000 + demand * 10 + rep,
            value_of_time=value_of_time,
        )
        for rep in range(REPLICATIONS)
    ]
    fixed = average_dict(fixed_reps)
    return df, optimum, fixed

# =========================================================
# PLOTLY NETWORK ANIMATION
# =========================================================
def make_demo_dispatches(demand, fleet, seed=2026):
    rng = random.Random(seed + demand + fleet)
    counts = largest_remainder(
        demand,
        {name: data["households"] for name, data in COMPLEXES.items()}
    )

    trips = []
    remaining = counts.copy()
    tid = 1

    while sum(remaining.values()) > 0 and tid <= 8:
        candidates = [k for k, v in remaining.items() if v > 0]
        origin = max(
            candidates,
            key=lambda k: remaining[k] / (COMPLEXES[k]["oneway_min"] + 1)
        )
        boarded = min(DRT_CAPACITY, remaining[origin], rng.randint(4, 10))
        remaining[origin] -= boarded
        vehicle = (tid - 1) % fleet + 1
        trips.append({
            "trip_id": tid,
            "vehicle": vehicle,
            "origin": origin,
            "boarded": boarded
        })
        tid += 1

    return trips

def build_network_animation(demand, fleet):
    """
    발표용 전문 시각화.
    - 실제 지도/도로가 아닌 운행 개념도
    - 네트워크 허브, 수요노드, 차량 상태, 단계별 운행상태를 하나의 Plotly 애니메이션으로 표시
    - Streamlit 재렌더링 없이 Plotly 내부 프레임으로만 움직여 깜빡임 최소화
    """
    station_name = "송도달빛축제공원역"
    sx, sy = SCHEMATIC_POS[station_name]

    initial_queues = largest_remainder(
        demand,
        {name: data["households"] for name, data in COMPLEXES.items()}
    )
    queue_state = initial_queues.copy()
    trips = make_demo_dispatches(demand, fleet)

    fig = go.Figure()

    # ---------- 배경: 도시 운영 네트워크 느낌 ----------
    fig.add_shape(
        type="rect", x0=0.35, x1=6.75, y0=0.25, y1=4.95,
        line=dict(color="rgba(148,163,184,.18)", width=1),
        fillcolor="#fbfcfe", layer="below"
    )

    # subtle district blocks
    block_specs = [
        (0.55, 1.55, 3.85, 4.65),
        (1.75, 2.75, 2.70, 3.55),
        (0.55, 1.55, 1.40, 2.20),
        (2.10, 3.15, 0.35, 1.15),
        (4.95, 6.55, 2.00, 3.15),
    ]
    for x0, x1, y0, y1 in block_specs:
        fig.add_shape(
            type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
            line=dict(color="rgba(148,163,184,.10)", width=1),
            fillcolor="rgba(241,245,249,.55)", layer="below"
        )

    # faint coordinate grid
    for x in [0.8, 1.8, 2.8, 3.8, 4.8, 5.8, 6.6]:
        fig.add_shape(
            type="line", x0=x, x1=x, y0=.3, y1=4.9,
            line=dict(color="rgba(148,163,184,.07)", width=1),
            layer="below"
        )
    for y in [.7, 1.7, 2.7, 3.7, 4.7]:
        fig.add_shape(
            type="line", x0=.4, x1=6.7, y0=y, y1=y,
            line=dict(color="rgba(148,163,184,.07)", width=1),
            layer="below"
        )

    # ---------- 기본 연결망 ----------
    route_palette = {
        "송도SK뷰": "#3b82f6",
        "호반써밋송도": "#10b981",
        "e편한세상송도": "#f59e0b",
        "더샵송도마리나베이": "#64748b",
    }

    for name in COMPLEXES:
        x0, y0 = SCHEMATIC_POS[name]
        fig.add_trace(go.Scatter(
            x=[x0, sx], y=[y0, sy],
            mode="lines",
            line=dict(width=3, color="rgba(100,116,139,.22)"),
            hoverinfo="skip",
            showlegend=False
        ))

    # ---------- 수요 노드 ----------
    node_names = list(COMPLEXES.keys())
    node_x = [SCHEMATIC_POS[n][0] for n in node_names]
    node_y = [SCHEMATIC_POS[n][1] for n in node_names]
    node_sizes = [30 + initial_queues[n] * .32 for n in node_names]

    fig.add_trace(go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(
            size=node_sizes,
            symbol="square",
            color=[route_palette[n] for n in node_names],
            line=dict(width=2.2, color="white")
        ),
        text=[f"<b>{n}</b><br>{initial_queues[n]}명" for n in node_names],
        textposition=["top right","top right","bottom right","bottom right"],
        hovertemplate="<b>%{text}</b><extra></extra>",
        name="수요 노드",
        showlegend=False
    ))

    # ---------- 역 허브 ----------
    fig.add_trace(go.Scatter(
        x=[sx], y=[sy],
        mode="markers+text",
        marker=dict(
            size=48,
            symbol="star",
            color="#1d4ed8",
            line=dict(width=2.4, color="white")
        ),
        text=["<b>송도달빛축제공원역</b><br>DRT HUB"],
        textposition="bottom center",
        hovertemplate="송도달빛축제공원역<br>DRT 대기·복귀 허브<extra></extra>",
        showlegend=False
    ))

    # ---------- 차량 ----------
    vehicle_colors = ["#ef4444", "#8b5cf6", "#06b6d4", "#ec4899", "#22c55e", "#f97316", "#6366f1", "#14b8a6"]
    vehicle_trace_indices = []
    for vid in range(1, fleet + 1):
        vehicle_trace_indices.append(len(fig.data))
        fig.add_trace(go.Scatter(
            x=[sx], y=[sy],
            mode="markers+text",
            marker=dict(
                size=24,
                symbol="circle",
                color=vehicle_colors[(vid-1) % len(vehicle_colors)],
                line=dict(width=2.5, color="white")
            ),
            text=[f"V{vid}"],
            textposition="top center",
            hovertemplate=f"DRT V{vid}<br>상태: 역 대기<extra></extra>",
            showlegend=False
        ))

    # ---------- 프레임 ----------
    frames = []
    current_pos = {vid: (sx, sy) for vid in range(1, fleet + 1)}
    current_status = {vid: "역 대기" for vid in range(1, fleet + 1)}
    frame_no = 0
    served_count = 0

    for trip in trips:
        vid = trip["vehicle"]
        origin = trip["origin"]
        boarded = trip["boarded"]
        ox, oy = SCHEMATIC_POS[origin]
        route_color = route_palette[origin]

        # outbound
        for step in range(1, 9):
            t = step / 8
            current_pos[vid] = (sx + (ox - sx) * t, sy + (oy - sy) * t)
            current_status[vid] = f"{origin}로 배차"

            vehicle_data = []
            for v in range(1, fleet + 1):
                px, py = current_pos[v]
                vehicle_data.append(go.Scatter(
                    x=[px], y=[py],
                    mode="markers+text",
                    marker=dict(
                        size=24,
                        symbol="circle",
                        color=vehicle_colors[(v-1) % len(vehicle_colors)],
                        line=dict(width=2.5, color="white")
                    ),
                    text=[f"V{v}"],
                    textposition="top center",
                    hovertemplate=f"DRT V{v}<br>{current_status[v]}<extra></extra>",
                    showlegend=False
                ))

            frames.append(go.Frame(
                name=f"f{frame_no}",
                data=vehicle_data,
                traces=vehicle_trace_indices,
                layout=go.Layout(
                    title=dict(
                        text=(
                            f"<b>DISPATCH</b> · V{vid} → {origin}"
                            f"<br><span style='font-size:12px;color:#64748b'>"
                            f"호출 {boarded}명 · 배차 우선순위에 따라 차량 투입</span>"
                        ),
                        x=.02
                    ),
                    shapes=[
                        *list(fig.layout.shapes),
                        dict(
                            type="line",
                            x0=sx, y0=sy, x1=ox, y1=oy,
                            line=dict(color=route_color, width=5),
                            layer="below"
                        )
                    ]
                )
            ))
            frame_no += 1

        queue_state[origin] = max(0, queue_state[origin] - boarded)

        # inbound
        for step in range(1, 9):
            t = step / 8
            current_pos[vid] = (ox + (sx - ox) * t, oy + (sy - oy) * t)
            current_status[vid] = f"{boarded}명 탑승 · 역 복귀"

            vehicle_data = []
            for v in range(1, fleet + 1):
                px, py = current_pos[v]
                vehicle_data.append(go.Scatter(
                    x=[px], y=[py],
                    mode="markers+text",
                    marker=dict(
                        size=24,
                        symbol="circle",
                        color=vehicle_colors[(v-1) % len(vehicle_colors)],
                        line=dict(width=2.5, color="white")
                    ),
                    text=[f"V{v}"],
                    textposition="top center",
                    hovertemplate=f"DRT V{v}<br>{current_status[v]}<extra></extra>",
                    showlegend=False
                ))

            frames.append(go.Frame(
                name=f"f{frame_no}",
                data=vehicle_data,
                traces=vehicle_trace_indices,
                layout=go.Layout(
                    title=dict(
                        text=(
                            f"<b>RETURN</b> · {origin} → 송도달빛축제공원역"
                            f"<br><span style='font-size:12px;color:#64748b'>"
                            f"V{vid} · 승객 {boarded}명 탑승 · 누적 수송 {served_count + boarded}명</span>"
                        ),
                        x=.02
                    ),
                    shapes=[
                        *list(fig.layout.shapes),
                        dict(
                            type="line",
                            x0=ox, y0=oy, x1=sx, y1=sy,
                            line=dict(color=route_color, width=5),
                            layer="below"
                        )
                    ]
                )
            ))
            frame_no += 1

        served_count += boarded
        current_status[vid] = "역 복귀 완료"

    fig.frames = frames

    # ---------- 컨트롤 ----------
    fig.update_layout(
        height=570,
        title=dict(
            text="<b>8공구 First/Last Mile 동적 배차 네트워크</b>",
            x=.02,
            font=dict(size=20, color="#172033")
        ),
        margin=dict(l=12, r=12, t=78, b=24),
        xaxis=dict(visible=False, range=[.35, 6.8]),
        yaxis=dict(visible=False, range=[.25, 4.95], scaleanchor="x", scaleratio=1),
        plot_bgcolor="#fbfcfe",
        paper_bgcolor="rgba(0,0,0,0)",
        updatemenus=[{
            "type":"buttons",
            "showactive":False,
            "direction":"left",
            "x":.02,
            "y":1.08,
            "pad":{"r":8,"t":0},
            "buttons":[
                {
                    "label":"▶ 운행 재생",
                    "method":"animate",
                    "args":[
                        None,
                        {
                            "frame":{"duration":115,"redraw":False},
                            "transition":{"duration":90,"easing":"cubic-in-out"},
                            "fromcurrent":True,
                            "mode":"immediate"
                        }
                    ]
                },
                {
                    "label":"⏸ 일시정지",
                    "method":"animate",
                    "args":[
                        [None],
                        {
                            "frame":{"duration":0,"redraw":False},
                            "transition":{"duration":0},
                            "mode":"immediate"
                        }
                    ]
                },
                {
                    "label":"↺ 처음부터",
                    "method":"animate",
                    "args":[
                        ["f0"],
                        {
                            "frame":{"duration":0,"redraw":False},
                            "transition":{"duration":0},
                            "mode":"immediate"
                        }
                    ]
                }
            ]
        }],
        annotations=[
            dict(
                x=.99, y=.02, xref="paper", yref="paper",
                text="운행 개념도 · 축척 및 실제 도로경로와 무관",
                showarrow=False, xanchor="right",
                font=dict(size=11, color="#64748b")
            ),
            dict(
                x=.02, y=.02, xref="paper", yref="paper",
                text=f"Fleet {fleet} · Demand {demand} · Capacity {DRT_CAPACITY}",
                showarrow=False, xanchor="left",
                font=dict(size=11, color="#64748b")
            )
        ]
    )

    return fig

# =========================================================
# SESSION STATE
# =========================================================
if "analysis_ready" not in st.session_state:
    st.session_state.analysis_ready = False

# =========================================================
# FORM — VALUES DO NOT APPLY UNTIL SUBMIT
# =========================================================
st.markdown('<div class="section-kicker">Scenario Configuration</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">운영 조건 설정</div>', unsafe_allow_html=True)

with st.form("scenario_form", clear_on_submit=False):
    st.markdown('<div class="config-shell">', unsafe_allow_html=True)

    c1,c2,c3,c4,c5 = st.columns([1.05,1.2,1.2,1.1,1.05])

    with c1:
        demand_in = st.select_slider(
            "2시간 총수요",
            options=[60,100,140],
            value=100
        )

    with c2:
        vot_in = st.select_slider(
            "이용자 시간가치",
            options=[9600,12000,14400],
            value=12000,
            format_func=lambda x:f"{x:,}원/시간"
        )

    with c3:
        fixed_in = st.select_slider(
            "차량 시간당 고정비",
            options=[14400,18000,21600],
            value=18000,
            format_func=lambda x:f"{x:,}원"
        )

    with c4:
        variable_in = st.select_slider(
            "km당 변동비",
            options=[240,300,360],
            value=300,
            format_func=lambda x:f"{x:,}원/km"
        )

    with c5:
        prior_in = st.selectbox(
            "사전 차량 대수 추정",
            options=[2,3,4,5],
            index=1,
            format_func=lambda x:f"{x}대"
        )

    st.markdown('</div>', unsafe_allow_html=True)

    submitted = st.form_submit_button(
        "분석 실행  →",
        type="primary",
        use_container_width=True
    )

if submitted:
    st.session_state.analysis_ready = True
    st.session_state.params = {
        "demand": demand_in,
        "vot": vot_in,
        "fixed": fixed_in,
        "variable": variable_in,
        "prior": prior_in,
    }

# =========================================================
# BEFORE ANALYSIS
# =========================================================
if not st.session_state.analysis_ready:
    st.markdown("""
    <div class="empty-state">
      <div style="font-size:1.15rem;font-weight:800;color:#344054;margin-bottom:8px;">
        운영 조건을 설정한 뒤 분석을 실행하세요.
      </div>
      <div>
        차량 1~8대 조건을 각각 50회 반복하여 대기시간·운영비·이용자 시간비용을 계산하고,
        사회적 총비용이 가장 낮은 차량 공급 규모를 도출합니다.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-kicker">Model Structure</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">분석 구조</div>', unsafe_allow_html=True)

    m1,m2,m3 = st.columns(3)
    with m1:
        st.markdown("""
        <div class="logic-card">
          <div class="logic-num">01 / DEMAND</div>
          <div class="logic-title">가상 호출 수요 생성</div>
          <div class="logic-text">단지별 세대수 비율과 07:00~09:00 첨두시간 분포를 반영하여 승객 호출을 생성합니다.</div>
        </div>
        """,unsafe_allow_html=True)
    with m2:
        st.markdown("""
        <div class="logic-card">
          <div class="logic-num">02 / DISPATCH</div>
          <div class="logic-title">규칙 기반 동적 배차</div>
          <div class="logic-text">대기시간·대기인원·왕복 운행시간을 종합하여 차량의 배차 우선순위를 결정합니다.</div>
        </div>
        """,unsafe_allow_html=True)
    with m3:
        st.markdown("""
        <div class="logic-card">
          <div class="logic-num">03 / OPTIMIZATION</div>
          <div class="logic-title">사회적 총비용 최소화</div>
          <div class="logic-text">차량 운영비와 이용자 시간비용의 합이 최소가 되는 차량 수를 경제적 최적값으로 선택합니다.</div>
        </div>
        """,unsafe_allow_html=True)

    st.stop()

# =========================================================
# RUN ANALYSIS ONLY FOR SUBMITTED PARAMS
# =========================================================
p = st.session_state.params

progress = st.progress(0, text="입력 조건 검증 중...")
progress.progress(18, text="수요 시나리오 생성 중...")
progress.progress(38, text="차량 1~8대 반복 시뮬레이션 중...")

df, optimum, fixed = run_scenario(
    p["demand"], p["vot"], p["fixed"], p["variable"]
)

progress.progress(78, text="사회적 총비용 비교 중...")
progress.progress(100, text="최적 운용 규모 산출 완료")
progress.empty()

optimal_fleet = int(optimum["fleet"])
cost_reduction_pct = (
    (fixed["social_cost_krw"] - optimum["social_cost_krw"])
    / fixed["social_cost_krw"] * 100
)
wait_reduction_min = fixed["avg_wait_min"] - optimum["avg_wait_min"]

# =========================================================
# RESULT
# =========================================================
st.markdown('<div class="section-kicker">Optimization Result</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">분석 결과</div>', unsafe_allow_html=True)

r1,r2,r3,r4,r5 = st.columns(5)
r1.metric("경제적 최적 차량",f"{optimal_fleet}대")
r2.metric("평균 대기시간",f"{optimum['avg_wait_min']:.1f}분")
r3.metric("95백분위 대기",f"{optimum['p95_wait_min']:.1f}분")
r4.metric("사회적 총비용",f"{optimum['social_cost_krw']/10000:.1f}만원")
r5.metric("가상 고정노선 대비",f"{cost_reduction_pct:.1f}% 낮음")

prior = p["prior"]
if prior == optimal_fleet:
    evaluation = "적정 추정"
    badge = "status-good"
    sentence = (
        f"사전 추정 {prior}대가 경제적 최적값과 일치했습니다. "
        f"현재 조건에서 차량 공급량은 적정하게 추정되었습니다."
    )
elif prior < optimal_fleet:
    evaluation = "과소 추정"
    badge = "status-warn"
    sentence = (
        f"사전 추정 {prior}대는 최적값 {optimal_fleet}대보다 적습니다. "
        f"차량 부족으로 이용자 시간비용이 상대적으로 커질 수 있습니다."
    )
else:
    evaluation = "과대 추정"
    badge = "status-warn"
    sentence = (
        f"사전 추정 {prior}대는 최적값 {optimal_fleet}대보다 많습니다. "
        f"대기시간은 줄일 수 있지만 추가 운영비가 경제적 편익을 초과할 수 있습니다."
    )

st.markdown(
    f"""
    <div class="result-strip">
      <span class="{badge}">{evaluation}</span>
      <span style="margin-left:10px;color:#1f2937;font-weight:700;">{sentence}</span>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================================================
# NETWORK
# =========================================================
st.markdown('<div class="section-kicker">Dynamic Dispatch</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">동적 배차 네트워크</div>', unsafe_allow_html=True)

map_col, rule_col = st.columns([1.75,1])

with map_col:
    st.plotly_chart(
        build_network_animation(p["demand"],optimal_fleet),
        use_container_width=True,
        config={"displayModeBar":False}
    )

with rule_col:
    st.markdown("""
    <div class="logic-card">
      <div class="logic-num">DISPATCH RULE 01</div>
      <div class="logic-title">호출상태 평가</div>
      <div class="logic-text">단지별 대기인원과 가장 오래 기다린 승객의 대기시간을 확인합니다.</div>
    </div>
    """,unsafe_allow_html=True)
    st.write("")
    st.markdown("""
    <div class="logic-card">
      <div class="logic-num">DISPATCH RULE 02</div>
      <div class="logic-title">배차 우선순위 계산</div>
      <div class="logic-text">대기시간·대기인원·왕복 운행시간을 종합한 점수로 우선 배차 단지를 선택합니다.</div>
    </div>
    """,unsafe_allow_html=True)
    st.write("")
    st.markdown("""
    <div class="logic-card">
      <div class="logic-num">DISPATCH RULE 03</div>
      <div class="logic-title">수송 및 차량 복귀</div>
      <div class="logic-text">차량은 선택된 단지에서 최대 10명을 태우고 송도달빛축제공원역으로 복귀합니다.</div>
    </div>
    """,unsafe_allow_html=True)

# =========================================================
# COST OPTIMIZATION
# =========================================================
st.markdown('<div class="section-kicker">Cost Structure</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">차량 공급량과 사회적 총비용</div>', unsafe_allow_html=True)

cost_col, text_col = st.columns([1.7,1])

with cost_col:
    fig=go.Figure()
    fig.add_trace(go.Scatter(
        x=df["fleet"],y=df["operating_cost_krw"]/10000,
        mode="lines+markers",name="운영비",
        line=dict(color="#3559c7",width=2.5)
    ))
    fig.add_trace(go.Scatter(
        x=df["fleet"],y=df["passenger_time_cost_krw"]/10000,
        mode="lines+markers",name="이용자 시간비용",
        line=dict(color="#7aa6e8",width=2.5)
    ))
    fig.add_trace(go.Scatter(
        x=df["fleet"],y=df["social_cost_krw"]/10000,
        mode="lines+markers",name="사회적 총비용",
        line=dict(color="#e45756",width=4)
    ))
    fig.add_trace(go.Scatter(
        x=[optimal_fleet],
        y=[optimum["social_cost_krw"]/10000],
        mode="markers+text",
        marker=dict(size=16,color="#172033"),
        text=[f"최적 {optimal_fleet}대"],
        textposition="top center",
        showlegend=False
    ))
    fig.update_layout(
        height=430,
        xaxis_title="DRT 차량 대수",
        yaxis_title="비용(만원)",
        hovermode="x unified",
        legend=dict(orientation="h",y=1.12),
        margin=dict(l=20,r=20,t=20,b=20),
        plot_bgcolor="#fbfcfe"
    )
    fig.update_xaxes(dtick=1,gridcolor="#edf0f4")
    fig.update_yaxes(gridcolor="#edf0f4")
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

with text_col:
    st.success(
        f"현재 입력조건에서 **{optimal_fleet}대**일 때 사회적 총비용이 "
        f"**{optimum['social_cost_krw']/10000:.1f}만원**으로 최소입니다."
    )
    st.write(
        "차량 수 증가 → **이용자 시간비용 감소**"
    )
    st.write(
        "차량 수 증가 → **운영비 증가**"
    )
    st.write(
        "따라서 두 비용의 합인 사회적 총비용이 가장 낮은 지점이 경제적 최적 공급량입니다."
    )
    st.divider()
    st.write(
        f"표준화 가상 고정노선 대비 평균 대기시간은 **{wait_reduction_min:.1f}분**, "
        f"사회적 총비용은 **{cost_reduction_pct:.1f}% 낮게** 나타났습니다."
    )
    st.caption("※ 비교 고정노선은 실제 송도 버스노선이 아닌 연구용 표준화 가상 시나리오입니다.")

# =========================================================
# SENSITIVITY SUMMARY — neutral, not presentation-y
# =========================================================
st.markdown('<div class="section-kicker">Scenario Interpretation</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">조건 변화에 따른 운용 판단</div>', unsafe_allow_html=True)

s1,s2,s3=st.columns(3)
with s1:
    st.markdown("""
    <div class="logic-card">
      <div class="logic-num">BASE CONDITION</div>
      <div class="logic-title">기준 수요</div>
      <div class="logic-text">수요 100명·기준 비용조건에서는 차량 3대가 경제적 최적값으로 나타납니다.</div>
    </div>
    """,unsafe_allow_html=True)

with s2:
    st.markdown("""
    <div class="logic-card">
      <div class="logic-num">HIGH DEMAND</div>
      <div class="logic-title">수요 증가</div>
      <div class="logic-text">2시간 수요가 140명으로 증가하면 적정 공급 규모가 4대로 확대됩니다.</div>
    </div>
    """,unsafe_allow_html=True)

with s3:
    st.markdown("""
    <div class="logic-card">
      <div class="logic-num">VALUE OF TIME</div>
      <div class="logic-title">시간가치 상승</div>
      <div class="logic-text">이용자 시간가치를 14,400원으로 높이면 시간 절감 편익이 커져 4대가 최적으로 바뀝니다.</div>
    </div>
    """,unsafe_allow_html=True)

st.markdown("---")
st.caption(
    "운행 시각화는 규칙 기반 동적 배차 원리를 설명하기 위한 개념 애니메이션이며 실제 도로지도·실측경로가 아닙니다. "
    "경제성 결과는 연구보고서의 동일 모형을 차량 1~8대 조건에서 각 50회 반복하여 산출합니다."
)
