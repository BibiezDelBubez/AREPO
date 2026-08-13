"""
Data Exporter Module for AREPO.
Exports extracted syntagms, rebus solutions, and word lists to CSV, JSON, or TXT.
"""

import json
import csv
from typing import List, Dict, Any


class DataExporter:
    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]], output_filepath: str) -> bool:
        if not data:
            return False

        fieldnames = list(data[0].keys())
        with open(output_filepath, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        return True

    @staticmethod
    def export_to_json(data: List[Dict[str, Any]], output_filepath: str) -> bool:
        if not data:
            return False

        with open(output_filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True

    @staticmethod
    def export_to_txt(lines: List[str], output_filepath: str) -> bool:
        if not lines:
            return False

        with open(output_filepath, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(str(line) + "\n")
        return True
