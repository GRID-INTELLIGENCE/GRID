# Network Activity Report
**Generated:** 2026-02-06 16:44:46

---

## Capture Summary
| Directory | Capture File | Status |
|-----------|-------------|--------|| Wellness | activity_20260206.pcapng | Captured (1 file(s)) |
| Grid | traffic_20260206.pcapng | Captured (1 file(s)) |
| Coinbase | monitoring_20260206.pcapng | Captured (1 file(s)) |
| SSL | dns_queries_20260206.pcapng | Captured (2 file(s)) |

---

## Parsed Results

### Wellness: parsed_wellness_20260206.json
```json
{
  "protocol": "Wellness",
  "source_file": "activity_20260206.pcapng",
  "parsed_at": "2026-02-06T16:45:08.795740",
  "http_requests": [
    {
      "timestamp": "2026-02-06 16:44:49.030694",
      "method": "GET",
      "url": "/",
      "full_uri": "http://example.com/"
    },
    {
      "timestamp": "2026-02-06 16:44:49.044523"
    },
    {
      "timestamp": "2026-02-06 16:44:55.596840",
      "method": "GET",
      "url": "/",
      "full_uri": "http://example.com/"
    },
    {
      "timestamp": "2026-02-06 16:44:55.608052"
    },
    {
      "timestamp": "2026-02-06 16:44:59.765578",
      "method": "GET",
      "url": "/",
      "full_uri": "http://example.com/"
    },
    {
      "timestamp": "2026-02-06 16:44:59.793907"
    }
  ],
  "dns_queries": [],
  "tcp_stats": {
    "total_packets": 181,
    "total_bytes": 48816,
    "top_source_ips": [
      {
        "ip": "172.27.250.38",
        "count": 101
      },
      {
        "ip": "104.18.26.120",
        "count": 39
      },
      {
        "ip": "172.64.152.241",
        "count": 18
      },
      {
        "ip": "104.18.27.120",
        "count": 12
      },
      {
        "ip": "104.18.35.15",
        "count": 11
      }
    ],
    "top_destination_ips": [
      {
        "ip": "172.27.250.38",
        "count": 80
      },
      {
        "ip": "104.18.26.120",
        "count": 46
      },
      {
        "ip": "172.64.152.241",
        "count": 25
      },
      {
        "ip": "104.18.27.120",
        "count": 16
      },
      {
        "ip": "104.18.35.15",
        "count": 14
      }
    ]
  },
  "tls_handshakes": [
    {
      "timestamp": "2026-02-06 16:44:49.059163",
      "src_ip": "172.27.250.38",
      "dst_ip": "104.18.26.120",
      "server_name": "example.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:49.064407",
      "src_ip": "104.18.26.120",
      "dst_ip": "172.27.250.38",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:49.106779",
      "src_ip": "172.27.250.38",
      "dst_ip": "172.64.152.241",
      "server_name": "api.coinbase.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:49.115123",
      "src_ip": "172.64.152.241",
      "dst_ip": "172.27.250.38",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:55.622969",
      "src_ip": "172.27.250.38",
      "dst_ip": "104.18.26.120",
      "server_name": "example.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:55.633490",
      "src_ip": "104.18.26.120",
      "dst_ip": "172.27.250.38",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:55.666952",
      "src_ip": "172.27.250.38",
      "dst_ip": "172.64.152.241",
      "server_name": "api.coinbase.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:55.670901",
      "src_ip": "172.64.152.241",
      "dst_ip": "172.27.250.38",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:59.808649",
      "src_ip": "172.27.250.38",
      "dst_ip": "104.18.26.120",
      "server_name": "example.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:59.816641",
      "src_ip": "104.18.26.120",
      "dst_ip": "172.27.250.38",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:59.847104",
      "src_ip": "172.27.250.38",
      "dst_ip": "104.18.35.15",
      "server_name": "api.coinbase.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:59.853502",
      "src_ip": "104.18.35.15",
      "dst_ip": "172.27.250.38",
      "tls_version": "0x0303"
    }
  ],
  "alerts": [
    {
      "severity": "INFO",
      "type": "all_clear",
      "message": "No anomalies detected. All traffic within normal thresholds.",
      "timestamp": "2026-02-06T16:45:10.019596"
    }
  ],
  "guardrail_thresholds": {
    "max_packets_per_minute": 5000,
    "max_unique_dst_ips": 50,
    "max_unique_dst_ports": 30,
    "max_dns_queries_per_minute": 200,
    "max_dns_query_length": 80,
    "max_failed_tls_handshakes": 10,
    "max_http_error_rate": 0.5,
    "suspicious_ports": [
      4444,
      5555,
      6666,
      6667,
      1337,
      31337,
      12345,
      65535
    ],
    "max_single_ip_packet_pct": 0.8,
    "max_payload_bytes_per_packet": 65000
  }
}
```

### Grid: parsed_grid_20260206.json
```json
{
  "protocol": "Grid",
  "source_file": "traffic_20260206.pcapng",
  "parsed_at": "2026-02-06T16:45:06.378515",
  "http_requests": [],
  "dns_queries": [],
  "tcp_stats": {
    "total_packets": 0,
    "total_bytes": 0,
    "top_source_ips": [],
    "top_destination_ips": []
  },
  "tls_handshakes": [],
  "alerts": [
    {
      "severity": "INFO",
      "type": "all_clear",
      "message": "No anomalies detected. All traffic within normal thresholds.",
      "timestamp": "2026-02-06T16:45:07.274766"
    }
  ],
  "guardrail_thresholds": {
    "max_packets_per_minute": 5000,
    "max_unique_dst_ips": 50,
    "max_unique_dst_ports": 30,
    "max_dns_queries_per_minute": 200,
    "max_dns_query_length": 80,
    "max_failed_tls_handshakes": 10,
    "max_http_error_rate": 0.5,
    "suspicious_ports": [
      4444,
      5555,
      6666,
      6667,
      1337,
      31337,
      12345,
      65535
    ],
    "max_single_ip_packet_pct": 0.8,
    "max_payload_bytes_per_packet": 65000
  }
}
```

### Coinbase: parsed_coinbase_20260206.json
```json
{
  "protocol": "Coinbase",
  "source_file": "monitoring_20260206.pcapng",
  "parsed_at": "2026-02-06T16:45:07.449629",
  "http_requests": [],
  "dns_queries": [],
  "tcp_stats": {
    "total_packets": 141,
    "total_bytes": 43425,
    "top_source_ips": [
      {
        "ip": "172.27.250.38",
        "count": 78
      },
      {
        "ip": "104.18.26.120",
        "count": 34
      },
      {
        "ip": "172.64.152.241",
        "count": 18
      },
      {
        "ip": "104.18.35.15",
        "count": 11
      }
    ],
    "top_destination_ips": [
      {
        "ip": "172.27.250.38",
        "count": 63
      },
      {
        "ip": "104.18.26.120",
        "count": 39
      },
      {
        "ip": "172.64.152.241",
        "count": 25
      },
      {
        "ip": "104.18.35.15",
        "count": 14
      }
    ]
  },
  "tls_handshakes": [
    {
      "timestamp": "2026-02-06 16:44:49.059163",
      "src_ip": "172.27.250.38",
      "dst_ip": "104.18.26.120",
      "server_name": "example.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:49.064407",
      "src_ip": "104.18.26.120",
      "dst_ip": "172.27.250.38",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:49.106779",
      "src_ip": "172.27.250.38",
      "dst_ip": "172.64.152.241",
      "server_name": "api.coinbase.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:49.115123",
      "src_ip": "172.64.152.241",
      "dst_ip": "172.27.250.38",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:55.622969",
      "src_ip": "172.27.250.38",
      "dst_ip": "104.18.26.120",
      "server_name": "example.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:55.633490",
      "src_ip": "104.18.26.120",
      "dst_ip": "172.27.250.38",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:55.666952",
      "src_ip": "172.27.250.38",
      "dst_ip": "172.64.152.241",
      "server_name": "api.coinbase.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:55.670901",
      "src_ip": "172.64.152.241",
      "dst_ip": "172.27.250.38",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:59.808649",
      "src_ip": "172.27.250.38",
      "dst_ip": "104.18.26.120",
      "server_name": "example.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:59.816641",
      "src_ip": "104.18.26.120",
      "dst_ip": "172.27.250.38",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:59.847104",
      "src_ip": "172.27.250.38",
      "dst_ip": "104.18.35.15",
      "server_name": "api.coinbase.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:59.853502",
      "src_ip": "104.18.35.15",
      "dst_ip": "172.27.250.38",
      "tls_version": "0x0303"
    }
  ],
  "alerts": [
    {
      "severity": "INFO",
      "type": "all_clear",
      "message": "No anomalies detected. All traffic within normal thresholds.",
      "timestamp": "2026-02-06T16:45:08.611292"
    }
  ],
  "guardrail_thresholds": {
    "max_packets_per_minute": 5000,
    "max_unique_dst_ips": 50,
    "max_unique_dst_ports": 30,
    "max_dns_queries_per_minute": 200,
    "max_dns_query_length": 80,
    "max_failed_tls_handshakes": 10,
    "max_http_error_rate": 0.5,
    "suspicious_ports": [
      4444,
      5555,
      6666,
      6667,
      1337,
      31337,
      12345,
      65535
    ],
    "max_single_ip_packet_pct": 0.8,
    "max_payload_bytes_per_packet": 65000
  }
}
```

### SSL: parsed_dns_20260206.json
```json
{
  "protocol": "DNS",
  "source_file": "dns_queries_20260206.pcapng",
  "parsed_at": "2026-02-06T16:45:10.204068",
  "http_requests": [],
  "dns_queries": [],
  "tcp_stats": {
    "total_packets": 0,
    "total_bytes": 0,
    "top_source_ips": [],
    "top_destination_ips": []
  },
  "tls_handshakes": [],
  "alerts": [
    {
      "severity": "INFO",
      "type": "all_clear",
      "message": "No anomalies detected. All traffic within normal thresholds.",
      "timestamp": "2026-02-06T16:45:11.060480"
    }
  ],
  "guardrail_thresholds": {
    "max_packets_per_minute": 5000,
    "max_unique_dst_ips": 50,
    "max_unique_dst_ports": 30,
    "max_dns_queries_per_minute": 200,
    "max_dns_query_length": 80,
    "max_failed_tls_handshakes": 10,
    "max_http_error_rate": 0.5,
    "suspicious_ports": [
      4444,
      5555,
      6666,
      6667,
      1337,
      31337,
      12345,
      65535
    ],
    "max_single_ip_packet_pct": 0.8,
    "max_payload_bytes_per_packet": 65000
  }
}
```

### SSL: parsed_ssl_20260206.json
```json
{
  "protocol": "SSL",
  "source_file": "network_traffic_20260206.pcapng",
  "parsed_at": "2026-02-06T16:45:05.176347",
  "http_requests": [
    {
      "timestamp": "2026-02-06 16:44:49.030694",
      "method": "GET",
      "url": "/",
      "full_uri": "http://example.com/"
    },
    {
      "timestamp": "2026-02-06 16:44:55.596840",
      "method": "GET",
      "url": "/",
      "full_uri": "http://example.com/"
    },
    {
      "timestamp": "2026-02-06 16:44:59.765578",
      "method": "GET",
      "url": "/",
      "full_uri": "http://example.com/"
    }
  ],
  "dns_queries": [],
  "tcp_stats": {
    "total_packets": 101,
    "total_bytes": 11751,
    "top_source_ips": [
      {
        "ip": "172.27.250.38",
        "count": 101
      }
    ],
    "top_destination_ips": [
      {
        "ip": "104.18.26.120",
        "count": 46
      },
      {
        "ip": "172.64.152.241",
        "count": 25
      },
      {
        "ip": "104.18.27.120",
        "count": 16
      },
      {
        "ip": "104.18.35.15",
        "count": 14
      }
    ]
  },
  "tls_handshakes": [
    {
      "timestamp": "2026-02-06 16:44:49.059163",
      "src_ip": "172.27.250.38",
      "dst_ip": "104.18.26.120",
      "server_name": "example.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:49.106779",
      "src_ip": "172.27.250.38",
      "dst_ip": "172.64.152.241",
      "server_name": "api.coinbase.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:55.622969",
      "src_ip": "172.27.250.38",
      "dst_ip": "104.18.26.120",
      "server_name": "example.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:55.666952",
      "src_ip": "172.27.250.38",
      "dst_ip": "172.64.152.241",
      "server_name": "api.coinbase.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:59.808649",
      "src_ip": "172.27.250.38",
      "dst_ip": "104.18.26.120",
      "server_name": "example.com",
      "tls_version": "0x0303"
    },
    {
      "timestamp": "2026-02-06 16:44:59.847104",
      "src_ip": "172.27.250.38",
      "dst_ip": "104.18.35.15",
      "server_name": "api.coinbase.com",
      "tls_version": "0x0303"
    }
  ],
  "alerts": [
    {
      "severity": "INFO",
      "type": "all_clear",
      "message": "No anomalies detected. All traffic within normal thresholds.",
      "timestamp": "2026-02-06T16:45:06.183033"
    }
  ],
  "guardrail_thresholds": {
    "max_packets_per_minute": 5000,
    "max_unique_dst_ips": 50,
    "max_unique_dst_ports": 30,
    "max_dns_queries_per_minute": 200,
    "max_dns_query_length": 80,
    "max_failed_tls_handshakes": 10,
    "max_http_error_rate": 0.5,
    "suspicious_ports": [
      4444,
      5555,
      6666,
      6667,
      1337,
      31337,
      12345,
      65535
    ],
    "max_single_ip_packet_pct": 0.8,
    "max_payload_bytes_per_packet": 65000
  }
}
```

---

## Debug Cleanup Policy
Cleanup is a **debugging feature** that scans all directories.
It ONLY removes corrupt/broken files:
- 0-byte .pcapng files (failed captures)
- Malformed .json files (invalid JSON)
- 0-byte .yaml/.yml files (empty configs)

**NEVER removed:** .py, .ps1, .sh, .md, .txt, and all other dev files.
Run with `-DebugCleanup` to activate. Requires `-SkipCleanup` to be OFF.

