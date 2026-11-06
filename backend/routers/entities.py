"""
DRIFTGUARD 2.0 Entity Intelligence & Knowledge Graph Router
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Set
from collections import defaultdict
import json
from dashboard.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/entities", tags=["Entities"])


@router.get("/graph")
def get_entity_graph(limit: int = Query(60, ge=10, le=200)) -> Dict[str, Any]:
    """
    Constructs an interactive entity knowledge graph for Apache ECharts.
    Extracts relations: Senders, Receivers, Devices, Locations, and Mule Rings.
    """
    dash_service = DashboardService()
    df = dash_service.get_recent_transactions(limit=limit)

    if df.empty:
        return {
            "status": "success",
            "nodes": [],
            "links": [],
            "categories": [
                {"name": "Sender User"},
                {"name": "Merchant"},
                {"name": "Device"},
                {"name": "Location"},
                {"name": "Mule Ring"},
            ],
        }

    nodes_dict: Dict[str, Dict[str, Any]] = {}
    links: List[Dict[str, Any]] = []
    seen_links: Set[str] = set()

    for _, row in df.iterrows():
        sender = str(row["sender_id"])
        receiver = str(row["receiver_id"])
        device = f"DEV-{str(row['device_id'])[-6:]}"
        location = str(row.get("location", "Bengaluru"))
        action = row["action_decision"]
        amount = float(row["amount"])

        # Determine if part of mule ring
        is_mule = "mule" in receiver.lower() or "mule" in sender.lower() or action == "BLOCK"

        # Sender Node
        if sender not in nodes_dict:
            nodes_dict[sender] = {
                "id": sender,
                "name": sender,
                "category": 0,  # Sender User
                "symbolSize": 32,
                "value": amount,
                "risk_tier": "HIGH" if action == "BLOCK" else ("MEDIUM" if action == "REVIEW" else "LOW"),
            }
        else:
            nodes_dict[sender]["value"] += amount

        # Receiver Node
        rec_cat = 4 if is_mule else 1  # Mule Ring or Merchant
        if receiver not in nodes_dict:
            nodes_dict[receiver] = {
                "id": receiver,
                "name": receiver,
                "category": rec_cat,
                "symbolSize": 40 if is_mule else 28,
                "value": amount,
                "risk_tier": "CRITICAL" if is_mule else ("MEDIUM" if action == "REVIEW" else "LOW"),
            }
        else:
            nodes_dict[receiver]["value"] += amount

        # Device Node
        if device not in nodes_dict:
            nodes_dict[device] = {
                "id": device,
                "name": device,
                "category": 2,  # Device
                "symbolSize": 22,
                "value": 1,
                "risk_tier": "LOW",
            }

        # Location Node
        if location not in nodes_dict:
            nodes_dict[location] = {
                "id": location,
                "name": location,
                "category": 3,  # Location
                "symbolSize": 24,
                "value": 1,
                "risk_tier": "LOW",
            }

        # Links
        # Sender -> Receiver
        tx_link_key = f"{sender}->{receiver}"
        if tx_link_key not in seen_links:
            seen_links.add(tx_link_key)
            links.append({
                "source": sender,
                "target": receiver,
                "value": round(amount, 2),
                "label": f"₹{amount:,.0f}",
                "lineStyle": {
                    "color": "#E11D48" if action == "BLOCK" else ("#D97706" if action == "REVIEW" else "#0D9488"),
                    "width": 3 if action == "BLOCK" else 1.5,
                },
            })

        # Sender -> Device
        dev_link_key = f"{sender}->{device}"
        if dev_link_key not in seen_links:
            seen_links.add(dev_link_key)
            links.append({
                "source": sender,
                "target": device,
                "value": 1,
                "label": "Uses Device",
                "lineStyle": {"type": "dashed", "color": "#94A3B8"},
            })

        # Sender -> Location
        loc_link_key = f"{sender}->{location}"
        if loc_link_key not in seen_links:
            seen_links.add(loc_link_key)
            links.append({
                "source": sender,
                "target": location,
                "value": 1,
                "label": "Located In",
                "lineStyle": {"type": "dotted", "color": "#CBD5E1"},
            })

    return {
        "status": "success",
        "nodes": list(nodes_dict.values()),
        "links": links,
        "categories": [
            {"name": "Sender User"},
            {"name": "Merchant"},
            {"name": "Device"},
            {"name": "Location"},
            {"name": "Mule Ring"},
        ],
    }


@router.get("/{entity_id}")
def get_entity_profile(entity_id: str) -> Dict[str, Any]:
    """Retrieves deep profile, counterparty network, and exposure for a given entity."""
    dash_service = DashboardService()
    df = dash_service.get_recent_transactions(limit=200)

    matched = df[(df["sender_id"] == entity_id) | (df["receiver_id"] == entity_id) | (df["device_id"] == entity_id)]

    total_volume = float(matched["amount"].sum()) if not matched.empty else 0.0
    tx_count = len(matched)
    blocks = len(matched[matched["action_decision"] == "BLOCK"])
    reviews = len(matched[matched["action_decision"] == "REVIEW"])

    counterparties = list(set(
        matched["receiver_id"].tolist() if not matched.empty else []
    ))[:8]

    return {
        "status": "success",
        "entity_id": entity_id,
        "tx_count": tx_count,
        "total_volume_inr": total_volume,
        "blocked_count": blocks,
        "review_count": reviews,
        "risk_rating": "CRITICAL" if blocks > 0 else ("HIGH" if reviews > 1 else "STANDARD"),
        "top_counterparties": counterparties,
    }

