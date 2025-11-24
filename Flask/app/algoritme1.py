from dataclasses import dataclass, field
from collections import Counter
from typing import List, Optional, Dict, Tuple
import numpy as np


# -----------------------------
# Datamodellen
# -----------------------------

@dataclass
class Shift:
    """
    Een shift/optie in de zaal.
    """
    id: int
    event_type: str        # bv. "trouw", "receptie", "bedrijfsfeest"
    role: str              # bv. "bar", "zaal", "opbouw", "afbraak"
    time_slot: str         # bv. "ochtend", "namiddag", "avond", "nacht"
    weekday: str           # bv. "ma-do", "vr-zo"
    location: str          # bv. "zaal A", "zaal B"
    duration_hours: float  # bv. 5.0

    # Wordt later opgevuld door encode_shift_features()
    feature_vector: Optional[np.ndarray] = field(default=None, repr=False)


@dataclass
class Employee:
    """
    Werknemer die shifts kiest.
    """
    id: int
    name: str
    # Id’s van patronen/shifts die expliciet als favoriet zijn aangeduid.
    favorite_shift_ids: List[int] = field(default_factory=list)


# -----------------------------
# Feature encoding
# -----------------------------

class FeatureEncoder:
    """
    Encodet Shifts naar numerieke vectors met one-hot encoding voor categorieën.
    """

    def __init__(self):
        # Definitie van mogelijke categorieën
        self.event_types = ["trouw", "receptie", "bedrijfsfeest"]
        self.roles = ["bar", "zaal", "opbouw", "afbraak", "allround"]
        self.time_slots = ["ochtend", "namiddag", "avond", "nacht"]
        self.weekdays = ["ma-do", "vr-zo"]
        self.locations = ["zaal A", "zaal B", "zaal C"]

        # Bereken totale lengte van de feature vector
        self.size = (
            len(self.event_types)
            + len(self.roles)
            + len(self.time_slots)
            + len(self.weekdays)
            + len(self.locations)
            + 1  # duration_hours (genormaliseerd)
        )

    def encode(self, shift: Shift) -> np.ndarray:
        """
        Encodeer één shift naar een feature vector.
        """
        vec = np.zeros(self.size, dtype=float)
        idx = 0

        # event_type
        for et in self.event_types:
            if shift.event_type == et:
                vec[idx] = 1.0
            idx += 1

        # role
        for r in self.roles:
            if shift.role == r:
                vec[idx] = 1.0
            idx += 1

        # time_slot
        for ts in self.time_slots:
            if shift.time_slot == ts:
                vec[idx] = 1.0
            idx += 1

        # weekday
        for wd in self.weekdays:
            if shift.weekday == wd:
                vec[idx] = 1.0
            idx += 1

        # location
        for loc in self.locations:
            if shift.location == loc:
                vec[idx] = 1.0
            idx += 1

        # duration_hours: simpele normalisatie bv. delen door 10
        vec[idx] = shift.duration_hours / 10.0

        return vec

    def encode_shifts(self, shifts: List[Shift]) -> None:
        """
        Vul feature_vector in bij alle gegeven shifts.
        """
        for s in shifts:
            s.feature_vector = self.encode(s)


# -----------------------------
# Hulpfuncties voor profielen
# -----------------------------

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Cosinusgelijkenis tussen twee vectors.
    """
    if a is None or b is None:
        return 0.0
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def build_user_profile(past_shifts: List[Shift]) -> Optional[np.ndarray]:
    """
    Maak een gebruikersprofiel door het gemiddelde te nemen van feature_vectors
    van alle eerder gekozen shifts.
    """
    if not past_shifts:
        return None
    vectors = [s.feature_vector for s in past_shifts if s.feature_vector is not None]
    if not vectors:
        return None
    return np.mean(np.stack(vectors, axis=0), axis=0)


def compute_pattern_stats(past_shifts: List[Shift]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Bepaal meest gekozen event_type, role en time_slot.
    """
    if not past_shifts:
        return None, None, None

    event_type = Counter(s.event_type for s in past_shifts).most_common(1)[0][0]
    role = Counter(s.role for s in past_shifts).most_common(1)[0][0]
    slot = Counter(s.time_slot for s in past_shifts).most_common(1)[0][0]
    return event_type, role, slot


def is_favorite_shift(employee: Employee, shift: Shift) -> bool:
    """
    Check of deze shift expliciet als favoriet is aangeduid door de werknemer.
    """
    return shift.id in employee.favorite_shift_ids


# -----------------------------
# Scoring & recommendations
# -----------------------------

def score_shift(
    employee: Employee,
    shift: Shift,
    user_vector: Optional[np.ndarray],
    preferred_event: Optional[str],
    preferred_role: Optional[str],
    preferred_slot: Optional[str],
    alpha: float = 0.6,
    beta: float = 0.3,
    gamma: float = 1.0,
) -> float:
    """
    Bereken totale score voor een shift.
    - alpha: gewicht voor content-based similarity
    - beta: gewicht voor patroon-boost
    - gamma: gewicht voor favorite-boost
    """
    # 1) content-based similarity
    similarity = cosine_similarity(shift.feature_vector, user_vector) if user_vector is not None else 0.0

    # 2) patroon-boost (meest voorkomende event_type/role/slot)
    pattern_boost = 0.0
    if preferred_event and shift.event_type == preferred_event:
        pattern_boost += 0.3
    if preferred_role and shift.role == preferred_role:
        pattern_boost += 0.3
    if preferred_slot and shift.time_slot == preferred_slot:
        pattern_boost += 0.2

    # 3) favoriet-boost
    favorite_boost = gamma if is_favorite_shift(employee, shift) else 0.0

    total_score = alpha * similarity + beta * pattern_boost + favorite_boost
    return total_score


def get_recommended_shifts(
    employee: Employee,
    all_shifts_for_event: List[Shift],
    past_shifts_for_employee: List[Shift],
) -> List[Shift]:
    """
    Geeft de lijst van shifts terug, gesorteerd van meest naar minst aanbevolen
    voor deze werknemer.
    """

    # Zorg dat alle shifts een feature_vector hebben.
    encoder = FeatureEncoder()
    encoder.encode_shifts(all_shifts_for_event)
    encoder.encode_shifts(past_shifts_for_employee)

    # Gebruikersprofiel + patronen bepalen
    user_vector = build_user_profile(past_shifts_for_employee)
    preferred_event, preferred_role, preferred_slot = compute_pattern_stats(past_shifts_for_employee)

    scored: List[Tuple[float, Shift]] = []
    for shift in all_shifts_for_event:
        score = score_shift(
            employee=employee,
            shift=shift,
            user_vector=user_vector,
            preferred_event=preferred_event,
            preferred_role=preferred_role,
            preferred_slot=preferred_slot,
        )
        scored.append((score, shift))

    # Sorteer op score, van hoog naar laag
    scored.sort(key=lambda x: x[0], reverse=True)

    # Retourneer enkel de shifts
    return [shift for _, shift in scored]


# -----------------------------
# Demo / test
# -----------------------------

if __name__ == "__main__":
    # Voorbeeldwerknemer
    emp = Employee(id=1, name="Lisa", favorite_shift_ids=[3])

    # Historiek: eerder gekozen shifts
    past_shifts = [
        Shift(id=101, event_type="trouw", role="bar", time_slot="avond", weekday="vr-zo", location="zaal A", duration_hours=6),
        Shift(id=102, event_type="trouw", role="zaal", time_slot="avond", weekday="vr-zo", location="zaal A", duration_hours=5),
        Shift(id=103, event_type="receptie", role="bar", time_slot="namiddag", weekday="ma-do", location="zaal B", duration_hours=4),
    ]

    # Beschikbare shifts voor een nieuw trouwfeest
    upcoming_shifts = [
        Shift(id=1, event_type="trouw", event_type="trouw", role="bar", time_slot="avond", weekday="vr-zo", location="zaal A", duration_hours=6),
        Shift(id=2, event_type="trouw", role="zaal", time_slot="namiddag", weekday="vr-zo", location="zaal B", duration_hours=5),
        Shift(id=3, event_type="receptie", role="bar", time_slot="avond", weekday="ma-do", location="zaal C", duration_hours=4),
        Shift(id=4, event_type="bedrijfsfeest", role="opbouw", time_slot="ochtend", weekday="ma-do", location="zaal A", duration_hours=3),
    ]

    recommendations = get_recommended_shifts(emp, upcoming_shifts, past_shifts)

    print("Aanbevolen volgorde van shifts voor", emp.name, ":")
    for s in recommendations:
        print(
            f"- Shift {s.id}: {s.event_type}, role={s.role}, slot={s.time_slot}, "
            f"loc={s.location}, duur={s.duration_hours}u"