#!/usr/bin/env bash
# =============================================
# WSL Network Firewall Rules (iptables)
# =============================================
# Tailored firewall for the Wireshark monitoring environment.
# Enforces least-privilege network access per directory/service.
#
# Usage:
#   sudo bash firewall_rules.sh [apply|status|reset|dry-run]
#
# Requires: root/sudo in WSL
# =============================================

set -euo pipefail

IFACE="eth0"
WSL_SUBNET="172.27.240.0/20"
LOG_PREFIX="[WSL-FW] "
RATE_LIMIT="25/minute"
RATE_BURST="50"
CONN_LIMIT_PER_IP=100
NEW_CONN_RATE="30/second"

# --- Allowed outbound ports (whitelist approach) ---
# DNS
ALLOWED_UDP_OUT="53"
# HTTP, HTTPS, SSH, MySQL, PostgreSQL, Redis, MongoDB, Docker, K8s API,
# Bitcoin P2P, Ethereum P2P/RPC, Coinbase API range, NTP
ALLOWED_TCP_OUT_1="22,53,80,443,3000:3010,3306,5432,6379,6443,8080"
ALLOWED_TCP_OUT_2="8333,8443,8545,8546,27017,30303"

# --- Known suspicious/blocked ports ---
BLOCKED_PORTS="4444,5555,6666,6667,1337,12345,31337,65535"

# --- Rate limit thresholds per service ---
# Format: port:rate:burst
RATE_LIMITS=(
    "53:50/minute:100"     # DNS
    "80:100/minute:200"    # HTTP
    "443:200/minute:400"   # HTTPS
    "22:10/minute:20"      # SSH
    "3306:30/minute:60"    # MySQL
    "8333:20/minute:40"    # Bitcoin P2P
)

print_header() {
    echo "============================================="
    echo " WSL Network Firewall — $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================="
}

apply_rules() {
    local DRY_RUN="${1:-false}"
    local CMD="iptables"
    if [ "$DRY_RUN" = "true" ]; then
        CMD="echo [DRY-RUN] iptables"
    fi

    print_header
    echo "[*] Applying firewall rules (dry_run=$DRY_RUN)..."

    # --- Flush existing rules ---
    echo "[1/8] Flushing existing rules..."
    $CMD -F
    $CMD -X
    $CMD -t nat -F
    $CMD -t mangle -F

    # --- Default policies ---
    echo "[2/8] Setting default policies..."
    $CMD -P INPUT DROP
    $CMD -P FORWARD DROP
    $CMD -P OUTPUT DROP

    # --- Loopback (always allow) ---
    echo "[3/8] Allowing loopback..."
    $CMD -A INPUT -i lo -j ACCEPT
    $CMD -A OUTPUT -o lo -j ACCEPT

    # --- Established/related connections ---
    echo "[4/8] Allowing established connections..."
    $CMD -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    $CMD -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

    # --- Block known malicious ports ---
    echo "[5/8] Blocking suspicious ports..."
    IFS=',' read -ra BPORTS <<< "$BLOCKED_PORTS"
    for port in "${BPORTS[@]}"; do
        $CMD -A INPUT -p tcp --dport "$port" -j DROP
        $CMD -A OUTPUT -p tcp --dport "$port" -j DROP
        $CMD -A INPUT -p tcp --sport "$port" -j DROP
        $CMD -A OUTPUT -p tcp --sport "$port" -j DROP
    done
    echo "  Blocked: $BLOCKED_PORTS"

    # --- Rate limiting per service ---
    echo "[6/8] Applying rate limits..."
    for entry in "${RATE_LIMITS[@]}"; do
        IFS=':' read -r port rate burst <<< "$entry"
        $CMD -A OUTPUT -p tcp --dport "$port" -m limit --limit "$rate" --limit-burst "$burst" -j ACCEPT
        echo "  Port $port: $rate (burst: $burst)"
    done

    # --- Allowed outbound TCP (split into 2 rules for multiport limit) ---
    echo "[7/8] Allowing whitelisted outbound TCP..."
    $CMD -A OUTPUT -p tcp -m multiport --dports "$ALLOWED_TCP_OUT_1" -m conntrack --ctstate NEW -j ACCEPT
    $CMD -A OUTPUT -p tcp -m multiport --dports "$ALLOWED_TCP_OUT_2" -m conntrack --ctstate NEW -j ACCEPT
    echo "  TCP: $ALLOWED_TCP_OUT_1,$ALLOWED_TCP_OUT_2"

    # --- Allowed outbound UDP (DNS, NTP) ---
    $CMD -A OUTPUT -p udp --dport 53 -m limit --limit 50/minute --limit-burst 100 -j ACCEPT
    $CMD -A OUTPUT -p udp --dport 123 -j ACCEPT
    echo "  UDP: 53 (rate-limited), 123 (NTP)"

    # --- ICMP (ping) with rate limit ---
    $CMD -A OUTPUT -p icmp --icmp-type echo-request -m limit --limit 10/minute --limit-burst 20 -j ACCEPT
    $CMD -A INPUT -p icmp --icmp-type echo-reply -j ACCEPT
    echo "  ICMP: echo-request (10/min), echo-reply allowed"

    # --- Connection limit per source IP ---
    echo "[8/8] Applying connection limits..."
    $CMD -A INPUT -p tcp --syn -m connlimit --connlimit-above "$CONN_LIMIT_PER_IP" -j DROP
    echo "  Max $CONN_LIMIT_PER_IP concurrent connections per source IP"

    # --- New connection rate limit ---
    $CMD -A INPUT -p tcp --syn -m limit --limit "$NEW_CONN_RATE" --limit-burst 60 -j ACCEPT
    echo "  New connection rate: $NEW_CONN_RATE (burst: 60)"

    # --- Log dropped packets (last rules before default DROP) ---
    $CMD -A INPUT -j LOG --log-prefix "${LOG_PREFIX}DROP-IN: " --log-level 4 -m limit --limit 5/minute
    $CMD -A OUTPUT -j LOG --log-prefix "${LOG_PREFIX}DROP-OUT: " --log-level 4 -m limit --limit 5/minute

    echo ""
    echo "[OK] Firewall rules applied successfully."
    echo "  Default policy: DROP (whitelist mode)"
    echo "  Allowed TCP out: $ALLOWED_TCP_OUT_1,$ALLOWED_TCP_OUT_2"
    echo "  Blocked ports: $BLOCKED_PORTS"
    echo "  Rate limits: ${#RATE_LIMITS[@]} service-specific rules"
}

show_status() {
    print_header
    echo "[*] Current iptables rules:"
    echo ""
    echo "--- INPUT chain ---"
    iptables -L INPUT -n -v --line-numbers 2>/dev/null || echo "  (requires root)"
    echo ""
    echo "--- OUTPUT chain ---"
    iptables -L OUTPUT -n -v --line-numbers 2>/dev/null || echo "  (requires root)"
    echo ""
    echo "--- FORWARD chain ---"
    iptables -L FORWARD -n -v --line-numbers 2>/dev/null || echo "  (requires root)"
}

reset_rules() {
    print_header
    echo "[*] Resetting firewall to permissive defaults..."
    iptables -F
    iptables -X
    iptables -t nat -F
    iptables -t mangle -F
    iptables -P INPUT ACCEPT
    iptables -P FORWARD ACCEPT
    iptables -P OUTPUT ACCEPT
    echo "[OK] All rules flushed. Default policy: ACCEPT (permissive)."
}

# --- Main ---
case "${1:-status}" in
    apply)
        if [ "$(id -u)" -ne 0 ]; then
            echo "ERROR: Must run as root (use sudo)." >&2
            exit 1
        fi
        apply_rules "false"
        ;;
    dry-run)
        apply_rules "true"
        ;;
    status)
        show_status
        ;;
    reset)
        if [ "$(id -u)" -ne 0 ]; then
            echo "ERROR: Must run as root (use sudo)." >&2
            exit 1
        fi
        reset_rules
        ;;
    *)
        echo "Usage: $0 [apply|status|reset|dry-run]"
        echo "  apply   - Apply firewall rules (requires root)"
        echo "  dry-run - Show what would be applied without changing anything"
        echo "  status  - Show current iptables rules"
        echo "  reset   - Reset to permissive defaults (requires root)"
        exit 1
        ;;
esac
