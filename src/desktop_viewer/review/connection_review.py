from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass(frozen=True)
class ConnectionReview:
    relationship_step_id: str
    relationship_global_id: str
    owner1_global_id: str
    owner1_class: str
    owner1_name: str
    owner2_global_id: str
    owner2_class: str
    owner2_name: str
    system_names: str
    port_distance_mm: float
    bbox_distance_mm: float
    bbox_overlap: bool

    @property
    def owner_global_ids(self) -> list[str]:
        return [self.owner1_global_id, self.owner2_global_id]

@dataclass(frozen=True)
class ConnectionHumanReview:
    relationship_step_id: str
    relationship_global_id: str
    owner1_global_id: str
    owner2_global_id: str
    review_status: str
    confirmed_value: str
    reviewed_at: str

def _row_to_review(row: dict[str, str]) -> ConnectionReview:
    """Convert one CSV row to a ConnectionReview."""
    return ConnectionReview(
        relationship_step_id=row["relationship_step_id"],
        relationship_global_id=row["relationship_global_id"],
        owner1_global_id=row["owner1_global_id"],
        owner1_class=row["owner1_class"],
        owner1_name=row["owner1_name"],
        owner2_global_id=row["owner2_global_id"],
        owner2_class=row["owner2_class"],
        owner2_name=row["owner2_name"],
        system_names=row["system_names"],
        port_distance_mm=float(row["port_distance_mm"]),
        bbox_distance_mm=float(row["bbox_distance_mm"]),
        bbox_overlap=row["bbox_overlap"].strip().upper() == "TRUE",
    )


def load_connection_reviews(csv_path: Path) -> list[ConnectionReview]:
    """Load all connection-review records from an ENMA analysis CSV."""
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [_row_to_review(row) for row in reader]


def load_connection_review(
    csv_path: Path,
    relationship_step_id: str,
) -> ConnectionReview:
    """Load one connection-review record from an ENMA analysis CSV."""
    relationship_step_id = str(relationship_step_id)

    for review in load_connection_reviews(csv_path):
        if review.relationship_step_id == relationship_step_id:
            return review

    raise KeyError(
        f"Relationship STEP id not found: {relationship_step_id}"
    )


HUMAN_REVIEW_FIELDNAMES = [
    "relationship_step_id",
    "relationship_global_id",
    "owner1_global_id",
    "owner2_global_id",
    "review_status",
    "confirmed_value",
    "reviewed_at",
]


def load_connection_human_reviews(
    csv_path: Path,
) -> dict[str, ConnectionHumanReview]:
    """Load saved human-review decisions keyed by relationship STEP id."""
    if not csv_path.exists():
        return {}

    reviews: dict[str, ConnectionHumanReview] = {}

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            review = ConnectionHumanReview(
                relationship_step_id=row["relationship_step_id"],
                relationship_global_id=row["relationship_global_id"],
                owner1_global_id=row["owner1_global_id"],
                owner2_global_id=row["owner2_global_id"],
                review_status=row["review_status"],
                confirmed_value=row["confirmed_value"],
                reviewed_at=row["reviewed_at"],
            )
            reviews[review.relationship_step_id] = review

    return reviews


def save_connection_human_review(
    csv_path: Path,
    connection_review: ConnectionReview,
    review_status: str,
    confirmed_value: str,
) -> ConnectionHumanReview:
    """Insert or update one human-review decision."""
    reviews = load_connection_human_reviews(csv_path)

    human_review = ConnectionHumanReview(
        relationship_step_id=connection_review.relationship_step_id,
        relationship_global_id=connection_review.relationship_global_id,
        owner1_global_id=connection_review.owner1_global_id,
        owner2_global_id=connection_review.owner2_global_id,
        review_status=review_status,
        confirmed_value=confirmed_value,
        reviewed_at=datetime.now().astimezone().isoformat(timespec="seconds"),
    )

    reviews[human_review.relationship_step_id] = human_review

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HUMAN_REVIEW_FIELDNAMES)
        writer.writeheader()

        for review in reviews.values():
            writer.writerow(
                {
                    "relationship_step_id": review.relationship_step_id,
                    "relationship_global_id": review.relationship_global_id,
                    "owner1_global_id": review.owner1_global_id,
                    "owner2_global_id": review.owner2_global_id,
                    "review_status": review.review_status,
                    "confirmed_value": review.confirmed_value,
                    "reviewed_at": review.reviewed_at,
                }
            )

    return human_review
