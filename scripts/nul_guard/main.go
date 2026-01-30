package main

import (
    "context"
    "encoding/json"
    "errors"
    "flag"
    "fmt"
    "io/fs"
    "log"
    "os"
    "path/filepath"
    "strings"
    "sync"
    "time"
)

// Occurrence captures a single nul artifact discovery.
type Occurrence struct {
    Path   string `json:"path"`
    Parent string `json:"parent"`
    Top    string `json:"top"`
}

// BlocklistReport stores enforcement metadata for future scans.
type BlocklistReport struct {
    GeneratedAt time.Time        `json:"generated_at"`
    Patterns    []string         `json:"patterns"`
    Sources     map[string]int   `json:"sources"`
    Instances   map[string]int64 `json:"instances"`
}

func main() {
    root := flag.String("root", ".", "Root directory to inspect")
    blocklistPath := flag.String("blocklist", "reports/nul_blocklist.json", "Where to persist blocklist metadata")
    dryRun := flag.Bool("dry-run", false, "Scan without deleting any files")
    concurrency := flag.Int("workers", 8, "Maximum concurrent removals")
    flag.Parse()

    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    occs, err := scanForNul(ctx, *root)
    if err != nil {
        log.Fatalf("scan failed: %v", err)
    }

    if len(occs) == 0 {
        log.Println("✅ No nul artifacts detected.")
        if err := ensureBlocklist(*root, *blocklistPath, nil); err != nil {
            log.Printf("warning: unable to refresh blocklist metadata: %v", err)
        }
        if err := ensureGitExclude(*root); err != nil {
            log.Printf("warning: unable to enforce git exclude: %v", err)
        }
        return
    }

    log.Printf("Detected %d nul artifacts\n", len(occs))
    summarizeSources(occs)

    if *dryRun {
        log.Println("Dry-run enabled; no files will be deleted.")
    } else {
        if err := removeOccurrences(ctx, occs, *concurrency); err != nil {
            log.Fatalf("failed to remove nul artifacts: %v", err)
        }
        log.Println("All nul artifacts removed.")
    }

    if err := ensureBlocklist(*root, *blocklistPath, occs); err != nil {
        log.Fatalf("blocklist update failed: %v", err)
    }
    if err := ensureGitExclude(*root); err != nil {
        log.Fatalf("failed to enforce git exclude: %v", err)
    }
}

func scanForNul(ctx context.Context, root string) ([]Occurrence, error) {
    var occs []Occurrence
    err := filepath.WalkDir(root, func(path string, d fs.DirEntry, walkErr error) error {
        if walkErr != nil {
            return walkErr
        }
        select {
        case <-ctx.Done():
            return ctx.Err()
        default:
        }

        if d == nil {
            return nil
        }
        if !strings.EqualFold(d.Name(), "nul") {
            return nil
        }

        rel, err := filepath.Rel(root, path)
        if err != nil {
            rel = path
        }
        parent := filepath.Dir(rel)
        if parent == "." {
            parent = root
        }
        top := rootComponent(rel)
        occs = append(occs, Occurrence{Path: path, Parent: parent, Top: top})
        return nil
    })
    return occs, err
}

func rootComponent(rel string) string {
    rel = filepath.ToSlash(rel)
    if idx := strings.Index(rel, "/"); idx > 0 {
        return rel[:idx]
    }
    return rel
}

func summarizeSources(occs []Occurrence) {
    sourceCount := make(map[string]int)
    parents := make(map[string]int)
    for _, occ := range occs {
        sourceCount[occ.Top]++
        parents[occ.Parent]++
    }

    log.Println("Top-level sources:")
    for top, count := range sourceCount {
        log.Printf("  %s -> %d", top, count)
    }

    log.Println("Heaviest parent directories:")
    for parent, count := range parents {
        if count > 10 {
            log.Printf("  %s -> %d", parent, count)
        }
    }
}

func removeOccurrences(ctx context.Context, occs []Occurrence, maxWorkers int) error {
    if maxWorkers < 1 {
        maxWorkers = 1
    }

    jobs := make(chan Occurrence)
    var wg sync.WaitGroup
    errChan := make(chan error, maxWorkers)

    worker := func() {
        defer wg.Done()
        for occ := range jobs {
            select {
            case <-ctx.Done():
                return
            default:
            }
            if err := os.RemoveAll(occ.Path); err != nil && !errors.Is(err, os.ErrNotExist) {
                errChan <- fmt.Errorf("remove %s: %w", occ.Path, err)
                return
            }
        }
    }

    wg.Add(maxWorkers)
    for i := 0; i < maxWorkers; i++ {
        go worker()
    }

    for _, occ := range occs {
        jobs <- occ
    }
    close(jobs)
    wg.Wait()

    select {
    case err := <-errChan:
        return err
    default:
        return nil
    }
}

func ensureBlocklist(root, blocklistPath string, occs []Occurrence) error {
    report := BlocklistReport{
        GeneratedAt: time.Now().UTC(),
        Patterns:    []string{"**/nul"},
        Sources:     map[string]int{},
        Instances:   map[string]int64{},
    }

    if data, err := os.ReadFile(blocklistPath); err == nil {
        _ = json.Unmarshal(data, &report)
    }

    ensurePattern(&report, "**/nul")
    ensurePattern(&report, "**/nul/*")

    for _, occ := range occs {
        report.Sources[occ.Top]++
        report.Instances[occ.Parent]++
    }

    if err := os.MkdirAll(filepath.Dir(blocklistPath), 0o755); err != nil {
        return err
    }
    data, err := json.MarshalIndent(report, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile(blocklistPath, data, 0o644)
}

func ensurePattern(report *BlocklistReport, pattern string) {
    for _, existing := range report.Patterns {
        if existing == pattern {
            return
        }
    }
    report.Patterns = append(report.Patterns, pattern)
}

func ensureGitExclude(root string) error {
    excludePath := filepath.Join(root, ".git", "info", "exclude")
    if _, err := os.Stat(excludePath); err != nil {
        // If repo metadata is unavailable, silently skip.
        return nil
    }

    data, err := os.ReadFile(excludePath)
    if err != nil {
        return err
    }

    content := string(data)
    additions := []string{"**/nul", "**/nul/*"}
    var builder strings.Builder
    builder.WriteString(content)

    changed := false
    for _, add := range additions {
        if !strings.Contains(content, add) {
            if !strings.HasSuffix(builder.String(), "\n") {
                builder.WriteString("\n")
            }
            builder.WriteString(add)
            builder.WriteString("\n")
            changed = true
        }
    }

    if !changed {
        return nil
    }
return os.WriteFile(excludePath, []byte(builder.String()), 0o644)
}
