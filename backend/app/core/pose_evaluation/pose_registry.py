"""Canonical pose taxonomy registry with English and Sanskrit names.

Covers all 82 poses from the Yoga-82 dataset plus common aliases.
Each entry stores: canonical_key, english_name, sanskrit_name, aliases, and
the class indices from the Yoga-82 hierarchy (class_6, class_20, class_82).
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PoseInfo:
    """Metadata for a single yoga pose."""
    key: str
    english_name: str
    sanskrit_name: str
    aliases: tuple[str, ...] = ()
    class_82_id: int = -1
    class_20_id: int = -1
    class_6_id: int = -1
    dataset_folder: str = ""


# ── Full Yoga-82 Pose Registry ─────────────────────────
# Each entry maps the Yoga-82 folder name to canonical info.
# class IDs are from the Yoga-82 train/test label columns.

POSE_REGISTRY: dict[str, PoseInfo] = {}

_POSE_DEFS: list[tuple[str, str, str, str, int, int, int]] = [
    # (dataset_folder, key, english_name, sanskrit_name, class_6, class_20, class_82)
    ("Akarna_Dhanurasana", "akarna_dhanurasana", "Shooting Bow Pose", "Akarna Dhanurasana", 1, 8, 0),
    ("Bharadvaja's_Twist_pose_or_Bharadvajasana_I_", "bharadvajasana_i", "Bharadvaja's Twist Pose", "Bharadvajasana I", 1, 5, 1),
    ("Boat_Pose_or_Paripurna_Navasana_", "boat_pose", "Boat Pose", "Paripurna Navasana", 5, 19, 2),
    ("Bound_Angle_Pose_or_Baddha_Konasana_", "bound_angle_pose", "Bound Angle Pose", "Baddha Konasana", 1, 4, 3),
    ("Bow_Pose_or_Dhanurasana_", "bow_pose", "Bow Pose", "Dhanurasana", 5, 19, 4),
    ("Bridge_Pose_or_Setu_Bandha_Sarvangasana_", "bridge_pose", "Bridge Pose", "Setu Bandha Sarvangasana", 5, 17, 5),
    ("Camel_Pose_or_Ustrasana_", "camel_pose", "Camel Pose", "Ustrasana", 5, 17, 6),
    ("Cat_Cow_Pose_or_Marjaryasana_", "cat_cow_pose", "Cat Cow Pose", "Marjaryasana", 5, 18, 7),
    ("Chair_Pose_or_Utkatasana_", "chair_pose", "Chair Pose", "Utkatasana", 0, 0, 8),
    ("Child_Pose_or_Balasana_", "child_pose", "Child's Pose", "Balasana", 4, 14, 9),
    ("Cobra_Pose_or_Bhujangasana_", "cobra_pose", "Cobra Pose", "Bhujangasana", 4, 14, 10),
    ("Cockerel_Pose", "cockerel_pose", "Cockerel Pose", "Kukkutasana", 2, 9, 11),
    ("Corpse_Pose_or_Savasana_", "corpse_pose", "Corpse Pose", "Savasana", 4, 13, 12),
    ("Cow_Face_Pose_or_Gomukhasana_", "cow_face_pose", "Cow Face Pose", "Gomukhasana", 1, 5, 13),
    ("Crane_(Crow)_Pose_or_Bakasana_", "crane_pose", "Crane (Crow) Pose", "Bakasana", 2, 9, 14),
    ("Dolphin_Plank_Pose_or_Makara_Adho_Mukha_Svanasana_", "dolphin_plank_pose", "Dolphin Plank Pose", "Makara Adho Mukha Svanasana", 4, 16, 15),
    ("Dolphin_Pose_or_Ardha_Pincha_Mayurasana_", "dolphin_pose", "Dolphin Pose", "Ardha Pincha Mayurasana", 4, 15, 16),
    ("Downward-Facing_Dog_pose_or_Adho_Mukha_Svanasana_", "downward_dog", "Downward-Facing Dog Pose", "Adho Mukha Svanasana", 4, 15, 17),
    ("Eagle_Pose_or_Garudasana_", "eagle_pose", "Eagle Pose", "Garudasana", 0, 0, 18),
    ("Eight-Angle_Pose_or_Astavakrasana_", "eight_angle_pose", "Eight-Angle Pose", "Astavakrasana", 2, 9, 19),
    ("Extended_Puppy_Pose_or_Uttana_Shishosana_", "extended_puppy_pose", "Extended Puppy Pose", "Uttana Shishosana", 4, 14, 20),
    ("Extended_Revolved_Side_Angle_Pose_or_Utthita_Parsvakonasana_", "extended_side_angle_pose", "Extended Side Angle Pose", "Utthita Parsvakonasana", 0, 2, 21),
    ("Extended_Revolved_Triangle_Pose_or_Utthita_Trikonasana_", "triangle_pose", "Triangle Pose", "Utthita Trikonasana", 0, 2, 22),
    ("Feathered_Peacock_Pose_or_Pincha_Mayurasana_", "feathered_peacock_pose", "Feathered Peacock Pose", "Pincha Mayurasana", 3, 12, 23),
    ("Firefly_Pose_or_Tittibhasana_", "firefly_pose", "Firefly Pose", "Tittibhasana", 2, 10, 24),
    ("Fish_Pose_or_Matsyasana_", "fish_pose", "Fish Pose", "Matsyasana", 5, 17, 25),
    ("Four-Limbed_Staff_Pose_or_Chaturanga_Dandasana_", "four_limbed_staff_pose", "Four-Limbed Staff Pose", "Chaturanga Dandasana", 4, 16, 26),
    ("Frog_Pose_or_Bhekasana", "frog_pose", "Frog Pose", "Bhekasana", 4, 14, 27),
    ("Garland_Pose_or_Malasana_", "garland_pose", "Garland Pose", "Malasana", 0, 0, 28),
    ("Gate_Pose_or_Parighasana_", "gate_pose", "Gate Pose", "Parighasana", 0, 1, 29),
    ("Half_Lord_of_the_Fishes_Pose_or_Ardha_Matsyendrasana_", "half_lord_fishes_pose", "Half Lord of the Fishes Pose", "Ardha Matsyendrasana", 1, 5, 30),
    ("Half_Moon_Pose_or_Ardha_Chandrasana_", "half_moon_pose", "Half Moon Pose", "Ardha Chandrasana", 0, 2, 31),
    ("Handstand_pose_or_Adho_Mukha_Vrksasana_", "handstand_pose", "Handstand Pose", "Adho Mukha Vrksasana", 3, 12, 32),
    ("Happy_Baby_Pose_or_Ananda_Balasana_", "happy_baby_pose", "Happy Baby Pose", "Ananda Balasana", 5, 19, 33),
    ("Head-to-Knee_Forward_Bend_pose_or_Janu_Sirsasana_", "head_to_knee_pose", "Head-to-Knee Forward Bend Pose", "Janu Sirsasana", 1, 6, 34),
    ("Heron_Pose_or_Krounchasana_", "heron_pose", "Heron Pose", "Krounchasana", 1, 7, 35),
    ("Intense_Side_Stretch_Pose_or_Parsvottanasana_", "intense_side_stretch_pose", "Intense Side Stretch Pose", "Parsvottanasana", 0, 3, 36),
    ("Legs-Up-the-Wall_Pose_or_Viparita_Karani_", "legs_up_wall_pose", "Legs-Up-the-Wall Pose", "Viparita Karani", 3, 11, 37),
    ("Locust_Pose_or_Salabhasana_", "locust_pose", "Locust Pose", "Salabhasana", 5, 19, 38),
    ("Lord_of_the_Dance_Pose_or_Natarajasana_", "lord_of_dance_pose", "Lord of the Dance Pose", "Natarajasana", 0, 1, 39),
    ("Low_Lunge_pose_or_Anjaneyasana_", "low_lunge_pose", "Low Lunge Pose", "Anjaneyasana", 0, 1, 40),
    ("Noose_Pose_or_Pasasana_", "noose_pose", "Noose Pose", "Pasasana", 0, 0, 41),
    ("Peacock_Pose_or_Mayurasana_", "peacock_pose", "Peacock Pose", "Mayurasana", 2, 10, 42),
    ("Pigeon_Pose_or_Kapotasana_", "pigeon_pose", "Pigeon Pose", "Kapotasana", 5, 17, 43),
    ("Plank_Pose_or_Kumbhakasana_", "plank_pose", "Plank Pose", "Kumbhakasana", 4, 16, 44),
    ("Plow_Pose_or_Halasana_", "plow_pose", "Plow Pose", "Halasana", 3, 11, 45),
    ("Pose_Dedicated_to_the_Sage_Koundinya_or_Eka_Pada_Koundinyanasana_I_and_II", "sage_koundinya_pose", "Sage Koundinya Pose", "Eka Pada Koundinyanasana", 2, 10, 46),
    ("Rajakapotasana", "king_pigeon_pose", "King Pigeon Pose", "Rajakapotasana", 5, 17, 47),
    ("Reclining_Hand-to-Big-Toe_Pose_or_Supta_Padangusthasana_", "reclining_hand_to_toe_pose", "Reclining Hand-to-Big-Toe Pose", "Supta Padangusthasana", 5, 19, 48),
    ("Revolved_Head-to-Knee_Pose_or_Parivrtta_Janu_Sirsasana_", "revolved_head_to_knee_pose", "Revolved Head-to-Knee Pose", "Parivrtta Janu Sirsasana", 1, 6, 49),
    ("Scale_Pose_or_Tolasana_", "scale_pose", "Scale Pose", "Tolasana", 2, 9, 50),
    ("Scorpion_pose_or_vrischikasana", "scorpion_pose", "Scorpion Pose", "Vrischikasana", 3, 12, 51),
    ("Seated_Forward_Bend_pose_or_Paschimottanasana_", "seated_forward_bend_pose", "Seated Forward Bend Pose", "Paschimottanasana", 1, 6, 52),
    ("Shoulder-Pressing_Pose_or_Bhujapidasana_", "shoulder_pressing_pose", "Shoulder-Pressing Pose", "Bhujapidasana", 2, 9, 53),
    ("Side-Reclining_Leg_Lift_pose_or_Anantasana_", "side_reclining_leg_lift_pose", "Side-Reclining Leg Lift Pose", "Anantasana", 5, 19, 54),
    ("Side_Crane_(Crow)_Pose_or_Parsva_Bakasana_", "side_crane_pose", "Side Crane (Crow) Pose", "Parsva Bakasana", 2, 9, 55),
    ("Side_Plank_Pose_or_Vasisthasana_", "side_plank_pose", "Side Plank Pose", "Vasisthasana", 2, 10, 56),
    ("Sitting pose 1 (normal)", "sitting_pose", "Sitting Pose", "Sukhasana", 1, 4, 57),
    ("Split pose", "split_pose", "Split Pose", "Hanumanasana", 1, 7, 58),
    ("Staff_Pose_or_Dandasana_", "staff_pose", "Staff Pose", "Dandasana", 1, 7, 59),
    ("Standing_Forward_Bend_pose_or_Uttanasana_", "standing_forward_bend_pose", "Standing Forward Bend Pose", "Uttanasana", 0, 3, 60),
    ("Standing_Split_pose_or_Urdhva_Prasarita_Eka_Padasana_", "standing_split_pose", "Standing Split Pose", "Urdhva Prasarita Eka Padasana", 0, 3, 61),
    ("Standing_big_toe_hold_pose_or_Utthita_Padangusthasana", "standing_big_toe_hold_pose", "Standing Big Toe Hold Pose", "Utthita Padangusthasana", 0, 2, 62),
    ("Supported_Headstand_pose_or_Salamba_Sirsasana_", "supported_headstand_pose", "Supported Headstand Pose", "Salamba Sirsasana", 3, 12, 63),
    ("Supported_Shoulderstand_pose_or_Salamba_Sarvangasana_", "supported_shoulderstand_pose", "Supported Shoulderstand Pose", "Salamba Sarvangasana", 3, 11, 64),
    ("Supta_Baddha_Konasana_", "reclining_bound_angle_pose", "Reclining Bound Angle Pose", "Supta Baddha Konasana", 5, 19, 65),
    ("Supta_Virasana_Vajrasana", "reclining_hero_pose", "Reclining Hero Pose", "Supta Virasana", 5, 19, 66),
    ("Tortoise_Pose", "tortoise_pose", "Tortoise Pose", "Kurmasana", 1, 6, 67),
    ("Tree_Pose_or_Vrksasana_", "tree_pose", "Tree Pose", "Vrksasana", 0, 0, 68),
    ("Upward_Bow_(Wheel)_Pose_or_Urdhva_Dhanurasana_", "wheel_pose", "Wheel Pose", "Urdhva Dhanurasana", 5, 17, 69),
    ("Upward_Facing_Two-Foot_Staff_Pose_or_Dwi_Pada_Viparita_Dandasana_", "upward_two_foot_staff_pose", "Upward Two-Foot Staff Pose", "Dwi Pada Viparita Dandasana", 5, 17, 70),
    ("Upward_Plank_Pose_or_Purvottanasana_", "upward_plank_pose", "Upward Plank Pose", "Purvottanasana", 5, 17, 71),
    ("Virasana_or_Vajrasana", "hero_pose", "Hero Pose", "Virasana", 1, 4, 72),
    ("Warrior_I_Pose_or_Virabhadrasana_I_", "warrior_i", "Warrior I Pose", "Virabhadrasana I", 0, 1, 73),
    ("Warrior_II_Pose_or_Virabhadrasana_II_", "warrior_ii", "Warrior II Pose", "Virabhadrasana II", 0, 2, 74),
    ("Warrior_III_Pose_or_Virabhadrasana_III_", "warrior_iii", "Warrior III Pose", "Virabhadrasana III", 0, 2, 75),
    ("Wide-Angle_Seated_Forward_Bend_pose_or_Upavistha_Konasana_", "wide_angle_seated_bend_pose", "Wide-Angle Seated Forward Bend Pose", "Upavistha Konasana", 1, 6, 76),
    ("Wide-Legged_Forward_Bend_pose_or_Prasarita_Padottanasana_", "wide_legged_forward_bend_pose", "Wide-Legged Forward Bend Pose", "Prasarita Padottanasana", 0, 3, 77),
    ("Wild_Thing_pose_or_Camatkarasana_", "wild_thing_pose", "Wild Thing Pose", "Camatkarasana", 2, 10, 78),
    ("Wind_Relieving_pose_or_Pawanmuktasana", "wind_relieving_pose", "Wind Relieving Pose", "Pawanmuktasana", 5, 19, 79),
    ("Yogic_sleep_pose", "yogic_sleep_pose", "Yogic Sleep Pose", "Yoga Nidrasana", 1, 6, 80),
    ("viparita_virabhadrasana_or_reverse_warrior_pose", "reverse_warrior_pose", "Reverse Warrior Pose", "Viparita Virabhadrasana", 0, 1, 81),
]

# Build registry
for folder, key, eng, san, c6, c20, c82 in _POSE_DEFS:
    POSE_REGISTRY[key] = PoseInfo(
        key=key,
        english_name=eng,
        sanskrit_name=san,
        class_82_id=c82,
        class_20_id=c20,
        class_6_id=c6,
        dataset_folder=folder,
    )

# Special fallback entry for unrecognized poses
POSE_REGISTRY["unknown_pose"] = PoseInfo(
    key="unknown_pose",
    english_name="Unrecognized Pose",
    sanskrit_name="",
    class_82_id=-1,
    class_20_id=-1,
    class_6_id=-1,
    dataset_folder="",
)

# Reverse lookups
_FOLDER_TO_KEY = {p.dataset_folder: p.key for p in POSE_REGISTRY.values()}
_CLASS82_TO_KEY = {p.class_82_id: p.key for p in POSE_REGISTRY.values()}
_NAME_TO_KEY: dict[str, str] = {}
for p in POSE_REGISTRY.values():
    _NAME_TO_KEY[p.english_name.lower()] = p.key
    _NAME_TO_KEY[p.sanskrit_name.lower()] = p.key
    _NAME_TO_KEY[p.key] = p.key


def get_pose_info(identifier: str | int) -> PoseInfo | None:
    """Look up pose by key, English name, Sanskrit name, folder, or class_82 ID."""
    if isinstance(identifier, int):
        key = _CLASS82_TO_KEY.get(identifier)
        return POSE_REGISTRY.get(key) if key else None
    s = str(identifier)
    # Direct key
    if s in POSE_REGISTRY:
        return POSE_REGISTRY[s]
    # Folder name
    key = _FOLDER_TO_KEY.get(s)
    if key:
        return POSE_REGISTRY[key]
    # Name lookup
    key = _NAME_TO_KEY.get(s.lower())
    if key:
        return POSE_REGISTRY[key]
    return None


def get_all_pose_keys() -> list[str]:
    """Return all canonical pose keys sorted."""
    return sorted(POSE_REGISTRY.keys())


def get_all_pose_names() -> list[tuple[str, str, str]]:
    """Return (key, english_name, sanskrit_name) for all poses."""
    return [(p.key, p.english_name, p.sanskrit_name) for p in POSE_REGISTRY.values()]


def get_class82_to_key_map() -> dict[int, str]:
    """Map from Yoga-82 class index to canonical key."""
    return dict(_CLASS82_TO_KEY)


def get_folder_to_key_map() -> dict[str, str]:
    """Map from dataset folder name to canonical key."""
    return dict(_FOLDER_TO_KEY)
