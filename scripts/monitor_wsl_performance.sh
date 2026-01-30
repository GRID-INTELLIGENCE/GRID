#!/bin/bash

# WSL Performance Monitoring Dashboard for GRID
# Real-time performance metrics and bottleneck detection
#
# Usage: ./scripts/monitor_wsl_performance.sh
#        ./scripts/monitor_wsl_performance.sh --interval 2
#        ./scripts/monitor_wsl_performance.sh --log performance.log

set -euo pipefail

# Configuration
INTERVAL="${1:-5}"  # Update interval in seconds
LOG_FILE="${2:-}"   # Optional log file
GRID_PROJECT_PATH="${GRID_ROOT:-$HOME/projects/grid}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        --log)
            LOG_FILE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --interval SECONDS  Update interval (default: 5)"
            echo "  --log FILE         Log metrics to file"
            echo "  --help             Show this help"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# Check if required tools are available
check_dependencies() {
    local missing=()

    for cmd in free df ps awk sed; do
        if ! command -v $cmd &> /dev/null; then
            missing+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "${RED}Error: Missing required commands: ${missing[*]}${NC}"
        exit 1
    fi
}

# Get memory usage
get_memory_usage() {
    local mem_info=$(free -m | awk 'NR==2')
    local total=$(echo $mem_info | awk '{print $2}')
    local used=$(echo $mem_info | awk '{print $3}')
    local available=$(echo $mem_info | awk '{print $7}')
    local percent=$(awk "BEGIN {printf \"%.1f\", ($used/$total)*100}")

    echo "$used|$total|$available|$percent"
}

# Get swap usage
get_swap_usage() {
    local swap_info=$(free -m | awk 'NR==3')
    local total=$(echo $swap_info | awk '{print $2}')
    local used=$(echo $swap_info | awk '{print $3}')

    if [ "$total" -eq 0 ]; then
        echo "0|0|0.0"
    else
        local percent=$(awk "BEGIN {printf \"%.1f\", ($used/$total)*100}")
        echo "$used|$total|$percent"
    fi
}

# Get CPU usage
get_cpu_usage() {
    local cpu_idle=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    echo "$cpu_idle"
}

# Get disk I/O stats
get_disk_io() {
    if [ -d "$GRID_PROJECT_PATH" ]; then
        local disk_info=$(df -h "$GRID_PROJECT_PATH" | awk 'NR==2')
        local total=$(echo $disk_info | awk '{print $2}')
        local used=$(echo $disk_info | awk '{print $3}')
        local available=$(echo $disk_info | awk '{print $4}')
        local percent=$(echo $disk_info | awk '{print $5}' | tr -d '%')
        echo "$used|$total|$available|$percent"
    else
        echo "N/A|N/A|N/A|0"
    fi
}

# Get process count
get_process_count() {
    ps aux | wc -l
}

# Get top memory processes
get_top_memory_processes() {
    ps aux --sort=-%mem | head -6 | tail -5 | awk '{printf "%-20s %6s %6s\n", substr($11,1,20), $3, $4}'
}

# Get top CPU processes
get_top_cpu_processes() {
    ps aux --sort=-%cpu | head -6 | tail -5 | awk '{printf "%-20s %6s %6s\n", substr($11,1,20), $3, $4}'
}

# Get network connections
get_network_stats() {
    local established=$(ss -tan state established 2>/dev/null | wc -l)
    local listening=$(ss -tln 2>/dev/null | wc -l)
    echo "$((established-1))|$((listening-1))"
}

# Check if path is in WSL or Windows filesystem
check_filesystem_location() {
    if [ -d "$GRID_PROJECT_PATH" ]; then
        if [[ "$GRID_PROJECT_PATH" =~ ^/mnt/ ]]; then
            echo "Windows (SLOW)"
        else
            echo "WSL (FAST)"
        fi
    else
        echo "Not Found"
    fi
}

# Get git status time
benchmark_git_status() {
    if [ -d "$GRID_PROJECT_PATH/.git" ]; then
        local start=$(date +%s%N)
        (cd "$GRID_PROJECT_PATH" && git status > /dev/null 2>&1)
        local end=$(date +%s%N)
        local elapsed=$(( (end - start) / 1000000 )) # Convert to milliseconds
        echo "${elapsed}ms"
    else
        echo "N/A"
    fi
}

# Performance rating
get_performance_rating() {
    local cpu_usage=$1
    local mem_percent=$2
    local disk_percent=$3

    local score=100

    # Deduct points for high usage
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        score=$((score - 30))
    elif (( $(echo "$cpu_usage > 60" | bc -l) )); then
        score=$((score - 15))
    fi

    if (( $(echo "$mem_percent > 80" | bc -l) )); then
        score=$((score - 30))
    elif (( $(echo "$mem_percent > 60" | bc -l) )); then
        score=$((score - 15))
    fi

    if (( $(echo "$disk_percent > 80" | bc -l) )); then
        score=$((score - 20))
    elif (( $(echo "$disk_percent > 60" | bc -l) )); then
        score=$((score - 10))
    fi

    if [ $score -ge 80 ]; then
        echo -e "${GREEN}Excellent ($score/100)${NC}"
    elif [ $score -ge 60 ]; then
        echo -e "${YELLOW}Good ($score/100)${NC}"
    elif [ $score -ge 40 ]; then
        echo -e "${YELLOW}Fair ($score/100)${NC}"
    else
        echo -e "${RED}Poor ($score/100)${NC}"
    fi
}

# Draw progress bar
draw_bar() {
    local percent=$1
    local width=40
    local filled=$(awk "BEGIN {printf \"%.0f\", ($percent/100)*$width}")
    local empty=$((width - filled))

    local color=$GREEN
    if (( $(echo "$percent > 80" | bc -l) )); then
        color=$RED
    elif (( $(echo "$percent > 60" | bc -l) )); then
        color=$YELLOW
    fi

    printf "${color}"
    printf '█%.0s' $(seq 1 $filled)
    printf "${NC}"
    printf '░%.0s' $(seq 1 $empty)
    printf " %5.1f%%" "$percent"
}

# Clear screen and draw dashboard
draw_dashboard() {
    clear

    # Header
    echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${BLUE}║                   WSL Performance Monitor - GRID Project                     ║${NC}"
    echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Timestamp
    echo -e "${CYAN}Last Update: $(date '+%Y-%m-%d %H:%M:%S')${NC}  (Press Ctrl+C to exit)"
    echo ""

    # System Resources
    echo -e "${BOLD}${MAGENTA}■ SYSTEM RESOURCES${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Memory
    local mem_data=$(get_memory_usage)
    local mem_used=$(echo $mem_data | cut -d'|' -f1)
    local mem_total=$(echo $mem_data | cut -d'|' -f2)
    local mem_available=$(echo $mem_data | cut -d'|' -f3)
    local mem_percent=$(echo $mem_data | cut -d'|' -f4)

    echo -en "${CYAN}Memory:${NC}     "
    draw_bar "$mem_percent"
    echo -e "  ${mem_used}MB / ${mem_total}MB (${mem_available}MB available)"

    # Swap
    local swap_data=$(get_swap_usage)
    local swap_used=$(echo $swap_data | cut -d'|' -f1)
    local swap_total=$(echo $swap_data | cut -d'|' -f2)
    local swap_percent=$(echo $swap_data | cut -d'|' -f3)

    echo -en "${CYAN}Swap:${NC}       "
    draw_bar "$swap_percent"
    echo -e "  ${swap_used}MB / ${swap_total}MB"

    # CPU
    local cpu_usage=$(get_cpu_usage)
    echo -en "${CYAN}CPU:${NC}        "
    draw_bar "$cpu_usage"
    echo ""

    # Disk
    local disk_data=$(get_disk_io)
    local disk_used=$(echo $disk_data | cut -d'|' -f1)
    local disk_total=$(echo $disk_data | cut -d'|' -f2)
    local disk_available=$(echo $disk_data | cut -d'|' -f3)
    local disk_percent=$(echo $disk_data | cut -d'|' -f4)

    echo -en "${CYAN}Disk:${NC}       "
    draw_bar "$disk_percent"
    echo -e "  ${disk_used} / ${disk_total} (${disk_available} available)"

    echo ""

    # Project Location
    echo -e "${BOLD}${MAGENTA}■ PROJECT STATUS${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local fs_location=$(check_filesystem_location)
    if [[ "$fs_location" == "WSL (FAST)" ]]; then
        echo -e "${CYAN}Location:${NC}   ${GREEN}✓ $fs_location${NC}"
    else
        echo -e "${CYAN}Location:${NC}   ${RED}✗ $fs_location${NC} ${YELLOW}(Consider moving to WSL filesystem)${NC}"
    fi

    echo -e "${CYAN}Path:${NC}       $GRID_PROJECT_PATH"

    local git_time=$(benchmark_git_status)
    if [[ "$git_time" != "N/A" ]]; then
        local git_ms=$(echo $git_time | sed 's/ms//')
        if [ "$git_ms" -lt 500 ]; then
            echo -e "${CYAN}Git Status:${NC} ${GREEN}✓ $git_time${NC}"
        elif [ "$git_ms" -lt 2000 ]; then
            echo -e "${CYAN}Git Status:${NC} ${YELLOW}⚠ $git_time${NC}"
        else
            echo -e "${CYAN}Git Status:${NC} ${RED}✗ $git_time (SLOW)${NC}"
        fi
    fi

    echo ""

    # Process Information
    echo -e "${BOLD}${MAGENTA}■ PROCESS INFORMATION${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    local process_count=$(get_process_count)
    echo -e "${CYAN}Total Processes:${NC} $process_count"

    local net_data=$(get_network_stats)
    local net_established=$(echo $net_data | cut -d'|' -f1)
    local net_listening=$(echo $net_data | cut -d'|' -f2)
    echo -e "${CYAN}Network:${NC}         $net_established established, $net_listening listening"

    echo ""

    # Top Processes
    echo -e "${BOLD}${CYAN}Top Memory Consumers:${NC}"
    echo -e "${BOLD}Process              CPU%   MEM%${NC}"
    get_top_memory_processes

    echo ""
    echo -e "${BOLD}${CYAN}Top CPU Consumers:${NC}"
    echo -e "${BOLD}Process              CPU%   MEM%${NC}"
    get_top_cpu_processes

    echo ""

    # Performance Rating
    echo -e "${BOLD}${MAGENTA}■ PERFORMANCE RATING${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -en "${CYAN}Overall:${NC}    "
    get_performance_rating "$cpu_usage" "$mem_percent" "$disk_percent"

    echo ""
    echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"

    # Log to file if specified
    if [ -n "$LOG_FILE" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S'),CPU:$cpu_usage,MEM:$mem_percent,DISK:$disk_percent,GIT:$git_time" >> "$LOG_FILE"
    fi
}

# Trap Ctrl+C
trap 'echo -e "\n${YELLOW}Monitoring stopped.${NC}"; exit 0' INT TERM

# Main loop
main() {
    check_dependencies

    echo -e "${GREEN}Starting WSL Performance Monitor...${NC}"
    sleep 1

    while true; do
        draw_dashboard
        sleep "$INTERVAL"
    done
}

main
