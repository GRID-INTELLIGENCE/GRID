#!/usr/bin/env python3
"""
Parse Wireshark/tshark PCAP captures and output structured JSON.

Usage:
    python3 parse_traffic.py <pcap_file> --output <output.json> --protocol <protocol_name>

Requires: pyshark (pip install pyshark)
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

try:
    import pyshark
except ImportError:
    print("ERROR: pyshark not installed. Run: pip install pyshark", file=sys.stderr)
    sys.exit(1)


def parse_http(pcap_file: str) -> list[dict]:
    """Parse HTTP requests from a PCAP file."""
    cap = pyshark.FileCapture(pcap_file, display_filter="http")
    results = []
    try:
        for packet in cap:
            entry = {"timestamp": str(packet.sniff_time)}
            if hasattr(packet, "http"):
                http = packet.http
                if hasattr(http, "request_method"):
                    entry["method"] = http.request_method
                if hasattr(http, "request_uri"):
                    entry["url"] = http.request_uri
                if hasattr(http, "request_full_uri"):
                    entry["full_uri"] = http.request_full_uri
                if hasattr(http, "content_length"):
                    entry["bytes"] = int(http.content_length)
                results.append(entry)
    except Exception as e:
        print(f"Warning: Error during HTTP parsing: {e}", file=sys.stderr)
    finally:
        cap.close()
    return results


def parse_dns(pcap_file: str) -> list[dict]:
    """Parse DNS queries from a PCAP file."""
    cap = pyshark.FileCapture(pcap_file, display_filter="dns")
    results = []
    try:
        for packet in cap:
            entry = {"timestamp": str(packet.sniff_time)}
            if hasattr(packet, "dns"):
                dns = packet.dns
                if hasattr(dns, "qry_name"):
                    entry["query_name"] = dns.qry_name
                if hasattr(dns, "qry_type"):
                    entry["query_type"] = dns.qry_type
                if hasattr(dns, "a"):
                    entry["response_ip"] = dns.a
                results.append(entry)
    except Exception as e:
        print(f"Warning: Error during DNS parsing: {e}", file=sys.stderr)
    finally:
        cap.close()
    return results


def parse_tcp_stats(pcap_file: str) -> dict:
    """Collect basic TCP traffic statistics."""
    cap = pyshark.FileCapture(pcap_file, display_filter="tcp")
    total_bytes = 0
    packet_count = 0
    src_ips = {}
    dst_ips = {}
    try:
        for packet in cap:
            packet_count += 1
            if hasattr(packet, "ip"):
                src = packet.ip.src
                dst = packet.ip.dst
                src_ips[src] = src_ips.get(src, 0) + 1
                dst_ips[dst] = dst_ips.get(dst, 0) + 1
            if hasattr(packet, "length"):
                total_bytes += int(packet.length)
    except Exception as e:
        print(f"Warning: Error during TCP stats: {e}", file=sys.stderr)
    finally:
        cap.close()

    # Top 10 source/destination IPs
    top_src = sorted(src_ips.items(), key=lambda x: x[1], reverse=True)[:10]
    top_dst = sorted(dst_ips.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_packets": packet_count,
        "total_bytes": total_bytes,
        "top_source_ips": [{"ip": ip, "count": c} for ip, c in top_src],
        "top_destination_ips": [{"ip": ip, "count": c} for ip, c in top_dst],
    }


def parse_ssl_tls(pcap_file: str) -> list[dict]:
    """Parse TLS/SSL handshake information."""
    cap = pyshark.FileCapture(pcap_file, display_filter="tls.handshake")
    results = []
    try:
        for packet in cap:
            entry = {"timestamp": str(packet.sniff_time)}
            if hasattr(packet, "ip"):
                entry["src_ip"] = packet.ip.src
                entry["dst_ip"] = packet.ip.dst
            if hasattr(packet, "tls"):
                tls = packet.tls
                if hasattr(tls, "handshake_extensions_server_name"):
                    entry["server_name"] = tls.handshake_extensions_server_name
                if hasattr(tls, "handshake_version"):
                    entry["tls_version"] = tls.handshake_version
            results.append(entry)
    except Exception as e:
        print(f"Warning: Error during TLS parsing: {e}", file=sys.stderr)
    finally:
        cap.close()
    return results


# =============================================
# Guardrails: Anomaly Detection & Alert Engine
# =============================================
ALERT_THRESHOLDS = {
    "max_packets_per_minute": 5000,
    "max_unique_dst_ips": 50,
    "max_unique_dst_ports": 30,
    "max_dns_queries_per_minute": 200,
    "max_dns_query_length": 80,
    "max_failed_tls_handshakes": 10,
    "max_http_error_rate": 0.5,
    "suspicious_ports": [4444, 5555, 6666, 6667, 1337, 31337, 12345, 65535],
    "max_single_ip_packet_pct": 0.80,
    "max_payload_bytes_per_packet": 65000,
}


def detect_anomalies(result: dict) -> list[dict]:
    """Run anomaly detection across all parsed data and return alerts."""
    alerts = []
    now = datetime.now().isoformat()

    tcp = result.get("tcp_stats", {})
    http = result.get("http_requests", [])
    dns = result.get("dns_queries", [])
    tls = result.get("tls_handshakes", [])

    # --- Rate limiting: packets per minute ---
    total_packets = tcp.get("total_packets", 0)
    if total_packets > ALERT_THRESHOLDS["max_packets_per_minute"]:
        alerts.append({
            "severity": "HIGH",
            "type": "rate_limit_exceeded",
            "message": f"Packet rate exceeded threshold: {total_packets} packets (limit: {ALERT_THRESHOLDS['max_packets_per_minute']})",
            "timestamp": now,
        })

    # --- Port scan detection: too many unique destination ports ---
    dst_ips = tcp.get("top_destination_ips", [])
    unique_dst_count = len(dst_ips)
    if unique_dst_count > ALERT_THRESHOLDS["max_unique_dst_ips"]:
        alerts.append({
            "severity": "HIGH",
            "type": "possible_port_scan",
            "message": f"Unusually high number of unique destination IPs: {unique_dst_count} (limit: {ALERT_THRESHOLDS['max_unique_dst_ips']})",
            "timestamp": now,
        })

    # --- Suspicious port activity ---
    suspicious = ALERT_THRESHOLDS["suspicious_ports"]
    for req in http:
        url = req.get("full_uri", "")
        for port in suspicious:
            if f":{port}" in url:
                alerts.append({
                    "severity": "CRITICAL",
                    "type": "suspicious_port",
                    "message": f"Traffic detected on suspicious port {port}: {url}",
                    "timestamp": now,
                })

    # --- DNS exfiltration detection: long query names ---
    for query in dns:
        qname = query.get("query_name", "")
        if len(qname) > ALERT_THRESHOLDS["max_dns_query_length"]:
            alerts.append({
                "severity": "HIGH",
                "type": "dns_exfiltration_suspect",
                "message": f"Unusually long DNS query ({len(qname)} chars): {qname[:60]}...",
                "timestamp": now,
            })

    # --- DNS volume spike ---
    if len(dns) > ALERT_THRESHOLDS["max_dns_queries_per_minute"]:
        alerts.append({
            "severity": "MEDIUM",
            "type": "dns_volume_spike",
            "message": f"High DNS query volume: {len(dns)} queries (limit: {ALERT_THRESHOLDS['max_dns_queries_per_minute']})",
            "timestamp": now,
        })

    # --- Single IP dominance (possible C2 beaconing) ---
    if total_packets > 0 and dst_ips:
        top_dst_count = dst_ips[0].get("count", 0)
        pct = top_dst_count / total_packets
        if pct > ALERT_THRESHOLDS["max_single_ip_packet_pct"] and total_packets > 50:
            alerts.append({
                "severity": "MEDIUM",
                "type": "single_ip_dominance",
                "message": f"Single destination IP {dst_ips[0]['ip']} accounts for {pct:.0%} of all traffic ({top_dst_count}/{total_packets} packets)",
                "timestamp": now,
            })

    # --- TLS handshake failures ---
    tls_without_sni = [h for h in tls if not h.get("server_name")]
    if len(tls_without_sni) > ALERT_THRESHOLDS["max_failed_tls_handshakes"]:
        alerts.append({
            "severity": "MEDIUM",
            "type": "tls_anomaly",
            "message": f"{len(tls_without_sni)} TLS handshakes without SNI (possible encrypted C2 or misconfiguration)",
            "timestamp": now,
        })

    # --- HTTP error rate ---
    if http:
        errors = [r for r in http if r.get("status_code", 200) >= 400]
        error_rate = len(errors) / len(http) if http else 0
        if error_rate > ALERT_THRESHOLDS["max_http_error_rate"] and len(http) > 10:
            alerts.append({
                "severity": "MEDIUM",
                "type": "http_error_spike",
                "message": f"HTTP error rate {error_rate:.0%} exceeds threshold ({len(errors)}/{len(http)} requests)",
                "timestamp": now,
            })

    # --- Clean bill of health ---
    if not alerts:
        alerts.append({
            "severity": "INFO",
            "type": "all_clear",
            "message": "No anomalies detected. All traffic within normal thresholds.",
            "timestamp": now,
        })

    return alerts


def main():
    parser = argparse.ArgumentParser(description="Parse Wireshark PCAP captures to JSON.")
    parser.add_argument("pcap_file", help="Path to the .pcapng capture file")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument(
        "--protocol",
        default="SSL",
        help="Protocol label (SSL, Grid, Coinbase, Wellness, DNS)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.pcap_file):
        print(f"ERROR: File not found: {args.pcap_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing [{args.protocol}]: {args.pcap_file}")

    result = {
        "protocol": args.protocol,
        "source_file": os.path.basename(args.pcap_file),
        "parsed_at": datetime.now().isoformat(),
        "http_requests": [],
        "dns_queries": [],
        "tcp_stats": {},
        "tls_handshakes": [],
        "alerts": [],
        "guardrail_thresholds": ALERT_THRESHOLDS,
    }

    # Parse all layers
    print("  Parsing HTTP requests...")
    result["http_requests"] = parse_http(args.pcap_file)
    print(f"    Found {len(result['http_requests'])} HTTP request(s)")

    print("  Parsing DNS queries...")
    result["dns_queries"] = parse_dns(args.pcap_file)
    print(f"    Found {len(result['dns_queries'])} DNS quer(ies)")

    print("  Collecting TCP stats...")
    result["tcp_stats"] = parse_tcp_stats(args.pcap_file)
    print(f"    Total packets: {result['tcp_stats'].get('total_packets', 0)}")

    print("  Parsing TLS/SSL handshakes...")
    result["tls_handshakes"] = parse_ssl_tls(args.pcap_file)
    print(f"    Found {len(result['tls_handshakes'])} TLS handshake(s)")

    # Run anomaly detection guardrails
    print("  Running anomaly detection...")
    result["alerts"] = detect_anomalies(result)
    alert_counts = Counter(a["severity"] for a in result["alerts"])
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "INFO"]:
        if alert_counts.get(sev, 0) > 0:
            color = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "INFO": "🟢"}.get(sev, "")
            print(f"    {color} {sev}: {alert_counts[sev]} alert(s)")

    # Write output
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)

    print(f"  Output saved → {args.output}")


if __name__ == "__main__":
    main()
