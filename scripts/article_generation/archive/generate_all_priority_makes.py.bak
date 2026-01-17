#!/usr/bin/env python3
"""
Batch generate insights for priority makes.
Run this to pre-generate JSON for high-traffic article candidates.
"""

import subprocess
import sys
from pathlib import Path

# Priority makes by article potential
PRIORITY_MAKES = [
    # Tier 1: High search volume, strong brand recognition
    "TOYOTA",      # 1.6M tests, reliable brand, high search
    "HONDA",       # 927K tests, reliability reputation
    "BMW",         # 1.8M tests, premium segment
    "FORD",        # 4.4M tests, UK's most common
    "VOLKSWAGEN",  # 2.9M tests, mainstream + GTI interest
    "AUDI",        # 1.6M tests, premium segment
    "MERCEDES-BENZ",  # 1.6M tests, premium segment

    # Tier 2: Good volume, interesting stories
    "MAZDA",       # 518K tests, "zoom-zoom" reliability angle
    "KIA",         # 886K tests, warranty story
    "HYUNDAI",     # 858K tests, value reliability story
    "NISSAN",      # 1.6M tests, Qashqai disaster story
    "VAUXHALL",    # 3M tests, common UK brand

    # Tier 3: Niche but engaged audiences
    "MINI",        # Enthusiast audience
    "VOLVO",       # Safety + reliability angle
    "SUZUKI",      # Value reliability
    "SKODA",       # VW underpinnings story
    "LAND ROVER",  # Reliability myths to bust
    "JAGUAR",      # British premium
    "LEXUS",       # Reliability champion
    "PORSCHE",     # Enthusiast + reliability
]

def main():
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent.parent / "data" / "make_insights"
    output_dir.mkdir(parents=True, exist_ok=True)

    generate_script = script_dir / "generate_make_insights.py"

    print(f"Generating insights for {len(PRIORITY_MAKES)} makes...")
    print(f"Output directory: {output_dir}\n")

    results = {"success": [], "failed": []}

    for make in PRIORITY_MAKES:
        output_file = output_dir / f"{make.lower().replace('-', '_')}_insights.json"
        print(f"  {make}...", end=" ", flush=True)

        try:
            result = subprocess.run(
                [sys.executable, str(generate_script), make,
                 "--output", str(output_file), "--pretty"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0 and output_file.exists():
                size = output_file.stat().st_size
                print(f"OK ({size:,} bytes)")
                results["success"].append(make)
            else:
                print(f"FAILED: {result.stderr[:100]}")
                results["failed"].append(make)

        except Exception as e:
            print(f"ERROR: {e}")
            results["failed"].append(make)

    print(f"\n{'='*50}")
    print(f"Completed: {len(results['success'])} success, {len(results['failed'])} failed")

    if results["failed"]:
        print(f"Failed: {', '.join(results['failed'])}")

    print(f"\nFiles saved to: {output_dir}")


if __name__ == "__main__":
    main()
