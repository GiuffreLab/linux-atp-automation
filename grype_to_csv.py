#!/usr/bin/env python3
import json
import csv
import sys

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low", "Negligible"]

def severity_rank(severity):
    return SEVERITY_ORDER.index(severity) if severity in SEVERITY_ORDER else len(SEVERITY_ORDER)

def main():
    with open("/tmp/grype.json", "r") as f:
        data = json.load(f)

    vulnerabilities = []
    for match in data.get("matches", []):
        vuln = match.get("vulnerability", {})
        artifact = match.get("artifact", {})
        vulnerabilities.append({
            "Package": artifact.get("name"),
            "Version": artifact.get("version"),
            "CVE": vuln.get("id"),
            "Fixed In": vuln.get("fix", {}).get("versions", [""])[0] if vuln.get("fix") else "",
            "Severity": vuln.get("severity"),
            "Type": artifact.get("type")
        })

    vulnerabilities.sort(key=lambda x: severity_rank(x["Severity"]))

    with open("/tmp/security-report.csv", "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["Package", "Version", "CVE", "Fixed In", "Severity", "Type"])
        writer.writeheader()
        for row in vulnerabilities:
            writer.writerow(row)

if __name__ == "__main__":
    main()
