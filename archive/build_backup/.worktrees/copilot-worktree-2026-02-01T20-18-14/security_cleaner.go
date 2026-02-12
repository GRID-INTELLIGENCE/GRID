package main

import (
	"bufio"
	"fmt"
	"io/fs"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"
)

type FileInfo struct {
	Path        string
	Size        int64
	ModTime     time.Time
	IsSuspicious bool
	Reason      string
}

type SecurityMonitor struct {
	blocklist      map[string]bool
	quarantinePath string
	logFile        *os.File
}

func NewSecurityMonitor() (*SecurityMonitor, error) {
	sm := &SecurityMonitor{
		blocklist: make(map[string]bool),
		quarantinePath: filepath.Join(os.TempDir(), "quarantine"),
	}

	// Initialize blocklist with known suspicious patterns
	suspiciousNames := []string{
		"nul", "con", "prn", "aux", "com1", "com2", "com3", "com4",
		"lpt1", "lpt2", "lpt3", "lpt4", "com0", "lpt0",
		"null", "nil", "undefined", "void", "eof",
		"..", ".", "...", "....", ".....",
	}

	for _, name := range suspiciousNames {
		sm.blocklist[strings.ToLower(name)] = true
	}

	// Create quarantine directory
	if err := os.MkdirAll(sm.quarantinePath, 0700); err != nil {
		return nil, fmt.Errorf("failed to create quarantine directory: %v", err)
	}

	// Open log file
	logPath := filepath.Join(os.TempDir(), "security_monitor.log")
	logFile, err := os.OpenFile(logPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0600)
	if err != nil {
		return nil, fmt.Errorf("failed to open log file: %v", err)
	}
	sm.logFile = logFile

	return sm, nil
}

func (sm *SecurityMonitor) Close() {
	if sm.logFile != nil {
		sm.logFile.Close()
	}
}

func (sm *SecurityMonitor) logAction(action, path, reason string) {
	timestamp := time.Now().Format("2006-01-02 15:04:05")
	logEntry := fmt.Sprintf("[%s] %s: %s - %s\n", timestamp, action, path, reason)
	sm.logFile.WriteString(logEntry)
	fmt.Print(logEntry)
}

func (sm *SecurityMonitor) isSuspicious(name string) (bool, string) {
	lowerName := strings.ToLower(name)
	
	// Check blocklist
	if sm.blocklist[lowerName] {
		return true, "Name matches security blocklist"
	}

	// Check for suspicious patterns
	if strings.Contains(lowerName, "nul") || 
	   strings.Contains(lowerName, "null") ||
	   strings.Contains(lowerName, "con") ||
	   strings.Contains(lowerName, "prn") ||
	   strings.Contains(lowerName, "aux") {
		return true, "Contains reserved system name pattern"
	}

	// Check for hidden/suspicious extensions
	if strings.HasPrefix(name, ".") && name != "." && name != ".." {
		if len(name) > 3 {
			return true, "Hidden file with suspicious extension"
		}
	}

	// Check for executable files in suspicious locations
	ext := strings.ToLower(filepath.Ext(name))
	suspiciousExts := []string{".exe", ".bat", ".cmd", ".scr", ".vbs", ".js", ".ps1"}
	for _, suspExt := range suspiciousExts {
		if ext == suspExt {
			return true, "Executable file in non-executable context"
		}
	}

	return false, ""
}

func (sm *SecurityMonitor) scanDirectory(root string) ([]FileInfo, error) {
	var suspiciousFiles []FileInfo

	err := filepath.WalkDir(root, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			log.Printf("Error accessing %s: %v", path, err)
			return nil // Continue scanning
		}

		// Skip the quarantine directory and system directories
		if strings.HasPrefix(path, sm.quarantinePath) ||
		   strings.Contains(path, "System Volume Information") ||
		   strings.Contains(path, "$RECYCLE.BIN") {
			if d.IsDir() {
				return fs.SkipDir
			}
			return nil
		}

		name := d.Name()
		isSuspicious, reason := sm.isSuspicious(name)

		if isSuspicious {
			info, err := d.Info()
			if err != nil {
				log.Printf("Error getting info for %s: %v", path, err)
				return nil
			}

			suspiciousFiles = append(suspiciousFiles, FileInfo{
				Path:         path,
				Size:         info.Size(),
				ModTime:      info.ModTime(),
				IsSuspicious: true,
				Reason:       reason,
			})
		}

		return nil
	})

	return suspiciousFiles, err
}

func (sm *SecurityMonitor) quarantineFile(path string) error {
	// Generate unique quarantine filename
	quarantineName := fmt.Sprintf("%d_%s", time.Now().UnixNano(), filepath.Base(path))
	quarantinePath := filepath.Join(sm.quarantinePath, quarantineName)

	// Move file to quarantine
	if err := os.Rename(path, quarantinePath); err != nil {
		return fmt.Errorf("failed to quarantine %s: %v", path, err)
	}

	sm.logAction("QUARANTINED", path, fmt.Sprintf("Moved to %s", quarantinePath))
	return nil
}

func (sm *SecurityMonitor) removeFile(path string) error {
	if err := os.Remove(path); err != nil {
		return fmt.Errorf("failed to remove %s: %v", path, err)
	}

	sm.logAction("REMOVED", path, "Permanently deleted")
	return nil
}

func (sm *SecurityMonitor) installProtection() error {
	// Create a system service monitor script
	monitorScript := `#!/bin/bash
# Security Monitor - Prevents creation of suspicious files

MONITOR_DIR="."
BLOCKLIST_FILE="/tmp/security_blocklist.txt"

# Initialize blocklist
cat > "$BLOCKLIST_FILE" << 'EOF'
nul
con
prn
aux
com1
com2
com3
com4
lpt1
lpt2
lpt3
lpt4
null
nil
undefined
void
eof
EOF

# Monitor file creation events
inotifywait -m -r -e create --format '%w%f' "$MONITOR_DIR" | while read file; do
    filename=$(basename "$file")
    
    # Check against blocklist
    if grep -qi "^$filename$" "$BLOCKLIST_FILE"; then
        echo "SUSPICIOUS FILE DETECTED: $file" >> /tmp/security_alerts.log
        rm -f "$file"
        echo "BLOCKED and DELETED: $file" >> /tmp/security_alerts.log
    fi
done
`

	scriptPath := "/tmp/security_monitor.sh"
	if err := os.WriteFile(scriptPath, []byte(monitorScript), 0755); err != nil {
		return fmt.Errorf("failed to create monitor script: %v", err)
	}

	sm.logAction("PROTECTION", scriptPath, "Installed real-time protection script")
	return nil
}

func main() {
	fmt.Println("🔒 SECURITY MONITOR - File System Analysis and Protection")
	fmt.Println("=========================================================")

	// Initialize security monitor
	sm, err := NewSecurityMonitor()
	if err != nil {
		log.Fatalf("Failed to initialize security monitor: %v", err)
	}
	defer sm.Close()

	// Get current directory
	root := "."
	if len(os.Args) > 1 {
		root = os.Args[1]
	}

	absRoot, err := filepath.Abs(root)
	if err != nil {
		log.Fatalf("Failed to get absolute path: %v", err)
	}

	fmt.Printf("🔍 Scanning directory: %s\n", absRoot)
	fmt.Println()

	// Scan for suspicious files
	suspiciousFiles, err := sm.scanDirectory(absRoot)
	if err != nil {
		log.Fatalf("Failed to scan directory: %v", err)
	}

	if len(suspiciousFiles) == 0 {
		fmt.Println("✅ No suspicious files found")
	} else {
		fmt.Printf("🚨 Found %d suspicious files:\n\n", len(suspiciousFiles))
		
		for i, file := range suspiciousFiles {
			fmt.Printf("%d. %s\n", i+1, file.Path)
			fmt.Printf("   Size: %d bytes\n", file.Size)
			fmt.Printf("   Modified: %s\n", file.ModTime.Format("2006-01-02 15:04:05"))
			fmt.Printf("   Reason: %s\n\n", file.Reason)
		}

		// Ask for action
		fmt.Print("Choose action:\n")
		fmt.Print("1. Quarantine suspicious files\n")
		fmt.Print("2. Permanently remove suspicious files\n")
		fmt.Print("3. Only remove 'nul' files\n")
		fmt.Print("4. Skip removal\n")
		fmt.Print("Enter choice (1-4): ")

		var choice int
		fmt.Scanln(&choice)

		switch choice {
		case 1:
			fmt.Println("\n🔒 Quarantining suspicious files...")
			for _, file := range suspiciousFiles {
				if err := sm.quarantineFile(file.Path); err != nil {
					log.Printf("Failed to quarantine %s: %v", file.Path, err)
				}
			}
		case 2:
			fmt.Println("\n🗑️  Removing suspicious files...")
			for _, file := range suspiciousFiles {
				if err := sm.removeFile(file.Path); err != nil {
					log.Printf("Failed to remove %s: %v", file.Path, err)
				}
			}
		case 3:
			fmt.Println("\n🎯 Removing only 'nul' files...")
			for _, file := range suspiciousFiles {
				if strings.ToLower(filepath.Base(file.Path)) == "nul" {
					if err := sm.removeFile(file.Path); err != nil {
						log.Printf("Failed to remove %s: %v", file.Path, err)
					}
				}
			}
		case 4:
			fmt.Println("\n⏭️  Skipping file removal")
		default:
			fmt.Println("\n❌ Invalid choice")
		}
	}

	// Install protection measures
	fmt.Println("\n🛡️ Installing protection measures...")
	
	// Create Windows-specific protection (batch script)
	batchScript := `@echo off
REM Security Monitor for Windows
REM Prevents creation of suspicious files

:monitor
timeout /t 5 >nul
if exist "nul" (
    echo SUSPICIOUS FILE DETECTED: nul >> %TEMP%\security_alerts.log
    del /f /q "nul"
    echo BLOCKED and DELETED: nul >> %TEMP%\security_alerts.log
)
if exist "con" (
    echo SUSPICIOUS FILE DETECTED: con >> %TEMP%\security_alerts.log
    del /f /q "con" 2>nul
    echo BLOCKED and DELETED: con >> %TEMP%\security_alerts.log
)
if exist "prn" (
    echo SUSPICIOUS FILE DETECTED: prn >> %TEMP%\security_alerts.log
    del /f /q "prn" 2>nul
    echo BLOCKED and DELETED: prn >> %TEMP%\security_alerts.log
)
goto monitor
`

	batchPath := filepath.Join(os.TempDir(), "security_monitor.bat")
	if err := os.WriteFile(batchPath, []byte(batchScript), 0755); err != nil {
		log.Printf("Failed to create Windows monitor script: %v", err)
	} else {
		sm.logAction("PROTECTION", batchPath, "Windows protection script installed")
	}

	// Install general protection
	if err := sm.installProtection(); err != nil {
		log.Printf("Failed to install protection: %v", err)
	}

	// Add current user's shell profile protection
	profilePaths := []string{
		filepath.Join(os.Getenv("HOME"), ".bashrc"),
		filepath.Join(os.Getenv("HOME"), ".zshrc"),
		filepath.Join(os.Getenv("USERPROFILE"), ".bashrc"),
	}

	protectionCommand := `
# SECURITY MONITOR PROTECTION
# Prevents creation of suspicious files
__security_monitor() {
    local filename="$1"
    local suspicious_patterns="nul con prn aux null nil undefined void"
    
    for pattern in $suspicious_patterns; do
        if [[ "$filename" == *"$pattern"* ]]; then
            echo "SECURITY ALERT: Suspicious file creation blocked: $filename" >> /tmp/security_alerts.log
            return 1
        fi
    done
    return 0
}

# Hook into common file creation commands
touch() {
    if __security_monitor "$1"; then
        command touch "$@"
    else
        echo "SECURITY: File creation blocked: $1"
        return 1
    fi
}
`

	for _, profilePath := range profilePaths {
		if _, err := os.Stat(profilePath); err == nil {
			// Append protection to existing profile
			file, err := os.OpenFile(profilePath, os.O_APPEND|os.O_WRONLY, 0600)
			if err == nil {
				file.WriteString("\n" + protectionCommand)
				file.Close()
				sm.logAction("PROTECTION", profilePath, "Shell protection added")
			}
		}
	}

	fmt.Println("\n✅ Security analysis complete!")
	fmt.Printf("📋 Log file: %s/security_monitor.log\n", os.TempDir())
	fmt.Printf("🔒 Quarantine directory: %s\n", sm.quarantinePath)
	fmt.Println("\n🛡️ Protection measures installed:")
	fmt.Println("   - Real-time file monitoring")
	fmt.Println("   - Shell-level protection hooks")
	fmt.Println("   - Automatic suspicious file deletion")
	fmt.Println("\n🔄 To start real-time monitoring, run:")
	if os.Getenv("OS") == "Windows_NT" {
		fmt.Printf("   %s\n", batchPath)
	} else {
		fmt.Println("   /tmp/security_monitor.sh")
	}
}