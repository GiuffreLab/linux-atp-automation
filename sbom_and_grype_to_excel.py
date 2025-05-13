#!/usr/bin/env python3
import json
import pandas as pd
import re
import sys
import traceback

# File paths
sbom_txt_path = "/tmp/syft.txt"
grype_json_path = "/tmp/grype.json"
output_excel_path = "/tmp/security-report.xlsx"

severity_order = ["Critical", "High", "Medium", "Low", "Negligible"]

def severity_sort_key(severity):
    return severity_order.index(severity) if severity in severity_order else len(severity_order)

def parse_syft_table(filepath):
    print(f"🔍 Parsing SBOM from: {filepath}")
    records = []
    try:
        with open(filepath, "r") as f:
            for line in f:
                if not line.strip() or line.strip().startswith("NAME"):
                    continue
                parts = re.split(r'\s{2,}', line.strip())
                if len(parts) == 3:
                    records.append({
                        "Package": parts[0],
                        "Version": parts[1],
                        "Type": parts[2]
                    })
                else:
                    print(f"⚠️ Skipping malformed line: {line.strip()}")
        print(f"✅ Parsed {len(records)} SBOM entries")
        return pd.DataFrame(records)
    except Exception as e:
        sys.stderr.write(f"❌ Error reading SBOM file: {e}\n")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

def parse_grype_json(filepath):
    print(f"🔍 Parsing vulnerability scan from: {filepath}")
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except Exception as e:
        sys.stderr.write(f"❌ Failed to parse Grype JSON: {e}\n")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    rows = []
    for match in data.get("matches", []):
        vuln = match.get("vulnerability", {})
        artifact = match.get("artifact", {})
        fix_versions = vuln.get("fix", {}).get("versions", [])
        fixed_in = fix_versions[0] if fix_versions else ""
        rows.append({
            "Package": artifact.get("name"),
            "Version": artifact.get("version"),
            "CVE": vuln.get("id"),
            "Fixed In": fixed_in,
            "Severity": vuln.get("severity"),
            "Type": artifact.get("type")
        })

    print(f"✅ Parsed {len(rows)} vulnerabilities")
    if not rows:
        print("ℹ️ No vulnerabilities found")

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["SeverityRank"] = df["Severity"].map(severity_sort_key)
    return df.sort_values(by="SeverityRank").drop(columns="SeverityRank")

def main():
    print("🚀 Starting SBOM + Vulnerability report generation...")

    try:
        df_sbom = parse_syft_table(sbom_txt_path)
        df_vulns = parse_grype_json(grype_json_path)
    except Exception as e:
        sys.stderr.write(f"❌ Fatal error during parsing: {e}\n")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    try:
        with pd.ExcelWriter(output_excel_path, engine="xlsxwriter") as writer:
            df_sbom.to_excel(writer, index=False, sheet_name="SBOM")
            df_vulns.to_excel(writer, index=False, sheet_name="Vulnerabilities")
        print(f"📦 Excel report written to: {output_excel_path}")
    except Exception as e:
        sys.stderr.write(f"❌ Failed to write Excel report: {e}\n")
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    print("✅ Report generation complete.")

if __name__ == "__main__":
    main()
