"""
Baseline Groups for Known Issues Detection

Defects in the same group share a combined baseline for ratio calculation.
This prevents baseline fragmentation from inflating ratios artificially.

Groups are defined by regex patterns that match component keywords in defect
descriptions. This approach is self-maintaining - new MOT wording variants
automatically match if they contain the component keywords.

Defects NOT matching any pattern use their individual baseline (unchanged behaviour).

Generated: 17 January 2026
"""

import re
from functools import lru_cache

# Pattern -> Group mapping
# Order matters: more specific patterns must come before general ones
COMPONENT_PATTERNS: list[tuple[str, str]] = [
    # ==========================================================================
    # BRAKES - specific patterns first
    # ==========================================================================
    (r'brake[s]?\s+imbalance|braking\s+effort', 'brake_imbalance_effort'),
    (r'parking\s+brake', 'parking_brake'),
    (r'service\s+brake', 'service_brake'),
    (r'brake\s+hose|flexible\s+brake\s+hose', 'brake_hose'),
    (r'brake\s+pipe', 'brake_pipe'),
    (r'brake\s+disc|brake\s+drum', 'brake_disc_drum'),
    (r'brake\s+lining|brake\s+pad', 'brake_lining_pad'),
    (r'brake\s+pedal', 'brake_pedal'),
    (r'brake\s+actuator|actuator', 'brake_actuator'),
    (r'brake\s+fluid', 'brake_fluid'),
    (r'esc\s+mil', 'esc_system'),
    (r'brake.*binding|no\s+brake\s+applied.*binding', 'brake_binding'),
    (r'brake.*warning|warning\s+device.*malfunction', 'brake_warning'),
    (r'fluctuation\s+in\s+brake', 'brake_disc_drum'),  # Usually warped disc
    (r'lag\s+in\s+brake', 'brake_hydraulic'),
    (r'brake.*grab', 'brake_grab'),
    (r'brake\s+performance\s+unable', 'brake_test_issue'),
    (r'cable\s+damaged|cable\s+knotted', 'brake_cable'),
    (r'restriction.*braking\s+system', 'brake_hydraulic'),

    # ==========================================================================
    # SUSPENSION
    # ==========================================================================
    (r'shock\s+absorber', 'shock_absorber'),
    (r'wheel\s+bearing', 'wheel_bearing'),
    (r'suspension\s+pin|suspension\s+bush|suspension\s+joint', 'suspension_bush_joint'),
    (r'suspension\s+component', 'suspension_component'),
    (r'stub\s+axle', 'stub_axle'),
    (r'a\s+spring|spring\s+component|spring\s+main\s+leaf|spring\s+insecure|'
     r'spring\s+with\s+fixings|spring\s+missing|spring\s+modified', 'spring'),

    # ==========================================================================
    # STEERING
    # ==========================================================================
    (r'steering\s+ball\s+joint', 'steering_ball_joint'),
    (r'steering\s+rack', 'steering_rack'),
    (r'power\s+steering', 'power_steering'),
    (r'steering\s+linkage', 'steering_linkage'),
    (r'free\s+play.*steering', 'steering_freeplay'),
    (r'steering\s+column', 'steering_column'),
    (r'steering.*roughness|roughness.*steering', 'steering_roughness'),

    # ==========================================================================
    # LAMPS - specific lamp types first, then general
    # ==========================================================================
    (r'headlamp', 'headlamp'),
    (r'stop\s+lamp', 'stop_lamp'),
    (r'fog\s+lamp', 'fog_lamp'),
    (r'direction\s+indicator|indicator.*switch|hazard\s+warning\s+switch', 'direction_indicator'),
    (r'registration\s+plate\s+lamp', 'registration_plate_lamp'),
    (r'reversing\s+lamp', 'reversing_lamp'),
    (r'position\s+lamp', 'position_lamp'),
    (r'reflector', 'reflector'),
    (r'a\s+lamp|lamp\s+missing|lamp\s+inoperative|lamp\s+emitted|'
     r'lamp\s+not\s+securely|lamp\s+showing', 'lamp_general'),
    (r'light\s+source', 'lamp_general'),
    (r'lens\s+defective', 'lamp_lens'),
    (r'audible\s+warning|horn', 'horn'),
    (r'battery\s+insecure', 'battery'),

    # ==========================================================================
    # TYRES
    # ==========================================================================
    (r'tyre\s+tread', 'tyre_tread'),
    (r'tyre\s+pressure', 'tyre_pressure_monitoring'),
    (r'tyre.*(?:cord|damaged|lump|bulge|tear|valve|fouling|seated)', 'tyre_condition'),
    (r'tyres.*(?:same\s+axle|different\s+size|different\s+structure)', 'tyre_mismatch'),
    (r'tyre.*sidewall|recut\s+tyre|tyre.*ten\s+years', 'tyre_compliance'),

    # ==========================================================================
    # EMISSIONS
    # ==========================================================================
    (r'engine\s+mil', 'engine_mil'),
    (r'lambda|emissions\s+level', 'emissions'),
    (r'smoke\s+opacity|visible\s+smoke|black\s+smoke|blue\s+smoke', 'smoke_emissions'),
    (r'emissions\s+test\s+unable|emissions\s+test\s+not\s+completed', 'emissions_test'),
    (r'emission\s+control\s+equipment', 'emissions_equipment'),
    (r'dpf|diesel\s+particulate', 'dpf'),
    (r'fluid\s+leaking.*environment|fluid\s+leaking.*safety', 'fluid_leak'),

    # ==========================================================================
    # VISIBILITY
    # ==========================================================================
    (r'windscreen\s+washer', 'windscreen_washer'),
    (r'wiper', 'wiper'),
    (r'mirror|driver.*view', 'mirror'),
    (r'windscreen.*damaged|windscreen.*tinted|window.*damaged', 'windscreen'),
    (r'bonnet.*secured|bonnet.*retaining', 'bonnet_latch'),

    # ==========================================================================
    # BODY / STRUCTURE
    # ==========================================================================
    (r'exhaust\s+system', 'exhaust_system'),
    (r'fuel\s+system|fuel\s+tank|filler\s+cap|fuel\s+pipe', 'fuel_system'),
    (r'transmission\s+shaft|cv\s+joint|transmission\s+joint|transmission\s+bearing', 'transmission'),
    (r'vehicle\s+structure\s+corroded|load\s+bearing\s+structure', 'structural_corrosion'),
    (r'body.*corroded|chassis.*corroded|cab.*corroded', 'body_corrosion'),
    (r'body\s+panel|body\s+component', 'body_panel'),
    (r'door\s+will\s+not\s+open|door.*close\s+properly', 'door'),
    (r'bumper', 'bumper'),
    (r'engine\s+mounting', 'engine_mounting'),
    (r'noise\s+suppression', 'exhaust_system'),
    (r'driver.*seat.*adjustment|seat.*adjustment', 'seat_adjustment'),
    (r'passenger\s+seat.*structure|passenger\s+seat.*backrest', 'passenger_seat'),

    # ==========================================================================
    # SAFETY SYSTEMS
    # ==========================================================================
    (r'seat\s+belt|seat\s+belt\s+anchorage', 'seat_belt'),
    (r'srs.*mil|airbag', 'srs_airbag'),

    # ==========================================================================
    # WHEELS
    # ==========================================================================
    (r'wheel.*nut|wheel.*bolt|wheel.*stud', 'wheel_fasteners'),
    (r'wheel.*fracture|wheel.*weld|wheel.*distort', 'wheel_damage'),

    # ==========================================================================
    # IDENTIFICATION
    # ==========================================================================
    (r'number\s+plate|registration.*mark', 'number_plate'),
    (r'vin|vehicle\s+identification', 'vin'),

    # ==========================================================================
    # OTHER
    # ==========================================================================
    (r'speedometer', 'speedometer'),
    (r'towbar|towing', 'towbar'),
]

# Compile patterns for performance
_COMPILED_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(pattern, re.IGNORECASE), group)
    for pattern, group in COMPONENT_PATTERNS
]


@lru_cache(maxsize=1024)
def get_baseline_group(defect_description: str) -> str | None:
    """
    Get the baseline group for a defect description.

    Returns the group name if the defect matches a component pattern,
    or None if the defect should use its individual baseline.

    Results are cached for performance.
    """
    for pattern, group in _COMPILED_PATTERNS:
        if pattern.search(defect_description):
            return group
    return None


def get_all_groups() -> set[str]:
    """Get all unique group names."""
    return {group for _, group in COMPONENT_PATTERNS}


def get_group_display_name(group: str) -> str:
    """
    Convert group ID to human-readable display name.
    e.g., 'brake_imbalance_effort' -> 'Brake Imbalance/Effort'
    """
    return group.replace('_', ' ').title().replace(' And ', ' & ')


# =============================================================================
# VALIDATION / DEBUGGING
# =============================================================================

def analyze_groupings(defect_descriptions: list[str]) -> dict:
    """
    Analyze a list of defect descriptions and return grouping statistics.
    Useful for validating the patterns against actual data.
    """
    from collections import defaultdict

    grouped = defaultdict(list)
    ungrouped = []

    for desc in defect_descriptions:
        group = get_baseline_group(desc)
        if group:
            grouped[group].append(desc)
        else:
            ungrouped.append(desc)

    return {
        'grouped_count': sum(len(v) for v in grouped.values()),
        'ungrouped_count': len(ungrouped),
        'groups': {k: len(v) for k, v in grouped.items()},
        'ungrouped': ungrouped,
    }


if __name__ == '__main__':
    # Quick test
    test_cases = [
        "Brakes imbalance across an axle such that the braking effort from any wheel is less than 50%",
        "A shock absorber damaged to the extent that it does not function",
        "A wheel bearing excessively rough",
        "Engine MIL illuminated indicating a malfunction",
        "Some random defect that should not match",
    ]

    print("Baseline Group Test:")
    print("-" * 60)
    for desc in test_cases:
        group = get_baseline_group(desc)
        print(f"{group or 'NONE':<25} | {desc[:50]}")
