# Quick Starter Checklist

One-shot setup guide for the Evolution Agent system.

## Prerequisites

- Python 3.11+
- Git repository with GRID codebase
- Access to CI/CD system (GitHub Actions, GitLab CI, etc.)

## Setup Steps

### 1. Install System Prompt

Drop the System Prompt into your agent runtime as the system message.

**File**: `tools/agent_prompts/system_prompt.md`

**Action**: Copy contents to your agent's system prompt configuration.

---

### 2. Add Supporting Scripts

Add these scripts to `tools/`:

- **`tools/inventory.py`** - System inventory script (see `tools/agent_prompts/ci_automation.md` for reference)
- **`tools/agent_validate.py`** - Agent output validation script (see below)

**Action**: Create scripts or adapt existing validation patterns.

---

### 3. Create Agent Prompts Package

Create `tools/agent_prompts/agent_prompts.json` containing the role prompts and machine-readable package.

**File**: `tools/agent_prompts/agent_prompts.json` (already created)

**Action**: Verify file exists and is valid JSON.

---

### 4. Set Up CI Workflow

Create a GitHub Actions workflow using the CI snippets.

**File**: `.github/workflows/agent_validation.yml`

**Action**: Create workflow file (see `tools/agent_prompts/ci_automation.md` for template).

---

### 5. Run Initial Inventory

Run the inventory prompt and review the System State Report.

**Command**:
```
/inventory root=.
```

**Action**:
- Execute inventory command
- Review generated `inventory.json`
- Verify all modules, tests, and CI configs are discovered

---

### 6. Test Full Flow

Approve one low-risk change to test the full flow.

**Example**: Add missing `interface_schema` stub for a module.

**Action**:
1. Run `/gapanalysis` on inventory
2. Select a low-risk gap (e.g., missing interface_schema for non-critical module)
3. Run `/execute story=<story_id>`
4. Review generated artifacts
5. Approve and create PR
6. Verify CI runs successfully

---

## Verification Checklist

After setup, verify:

- [ ] System prompt loaded in agent
- [ ] `tools/inventory.py` exists and runs
- [ ] `tools/agent_validate.py` exists and runs
- [ ] `tools/agent_prompts/agent_prompts.json` exists and is valid
- [ ] `.github/workflows/agent_validation.yml` exists
- [ ] Inventory command produces valid JSON
- [ ] Gap analysis identifies at least one gap
- [ ] Planning produces backlog with stories
- [ ] Execution produces PR-ready artifacts
- [ ] CI workflow runs on PR

---

## Next Steps

Once setup is complete:

1. **Regular Inventory**: Run `/inventory` weekly to track system state
2. **Gap Tracking**: Run `/gapanalysis` after major changes
3. **Backlog Management**: Use `/plan` to prioritize evolution work
4. **Automated Execution**: Integrate with CI for automated validation

---

## Troubleshooting

### Inventory Script Not Found

**Solution**: Create `tools/inventory.py` using reference from `tools/agent_prompts/ci_automation.md`

### CI Workflow Not Running

**Solution**:
- Check workflow file syntax (YAML)
- Verify workflow is in `.github/workflows/` directory
- Check GitHub Actions permissions

### Agent Output Not Validating

**Solution**:
- Check `tools/agent_prompts/schema.json` is valid
- Verify agent output matches expected schema
- Run `python tools/agent_validate.py --check-schema <output.json>`

### Missing Interface Schemas

**Solution**:
- Run `/gapanalysis` to identify gaps
- Use `/execute` to generate schema stubs
- Follow contract change process in `tools/agent_prompts/governance.md`

---

## Quick Reference

| Command | Purpose | Output |
|---------|---------|--------|
| `/inventory root=<path>` | System discovery | inventory.json |
| `/gapanalysis {inventory}` | Identify gaps | gaps.json |
| `/plan {gaps} constraints={...}` | Create backlog | backlog.json |
| `/execute story=<id>` | Generate artifacts | executor_output.json |
| `/validate task=<id>` | Validate change | validation_report.json |
| `/safety review change=<id>` | Safety review | governance_document.json |

---

## Support

For detailed documentation, see:
- `docs/AGENT_EVOLUTION_SYSTEM.md` - Complete system documentation
- `tools/agent_prompts/` - All prompt files and schemas
- `tools/agent_prompts/example_dialogue.md` - Example usage
