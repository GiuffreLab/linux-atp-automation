#!/usr/bin/env python3
import json
import pandas as pd
import re

# File paths
sbom_txt_path = "/tmp/syft.txt"
grype_json_path = "/tmp/grype.json"
output_excel_path = "/tmp/security-report.xlsx"

# Severity sort order
severity_order = ["Critical", "High", "Medium", "Low", "Negligible"]

def severity_sort_key(severity):
    return severity_order.index(severity) if severity in severity_order else len(severity_order)

def parse_syft_table(filepath):
    """Parse syft output in table format into a DataFrame."""
    records = []
    with open(filepath, "r") as f:
        for line in f:
            # Skip empty and header lines
            if not line.strip() or line.strip().startswith("NAME"):
                continue
            # Split by 2+ spaces
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) == 3:
                records.append({
                    "Package": parts[0],
                    "Version": parts[1],
                    "Type": parts[2]
                })
    return pd.DataFrame(records)

def parse_grype_json(filepath):
    """Parse Grype JSON and return a sorted DataFrame."""
    with open(filepath, "r") as f:
        data = json.load(f)

    rows = []
    for match in data.get("matches", []):
        vuln = match.get("vulnerability", {})
        artifact = match.get("artifact", {})
        rows.append({
            "Package": artifact.get("name"),
            "Version": artifact.get("version"),
            "CVE": vuln.get("id"),
            "Fixed In": vuln.get("fix", {}).get("versions", [""])[0] if vuln.get("fix") else
