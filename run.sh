#!/bin/bash
# InfiEpisteme v2 — .md-native research pipeline driver
# Usage: ./run.sh {start|resume|status|reset <stage>}

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
mkdir -p state

MAX_RETRIES=3

get_timeout() {
    case "$1" in
        P0) echo 1800 ;;      # 30m
        S0) echo 300 ;;       # 5m
        S1) echo 1200 ;;      # 20m
        S2) echo 900 ;;       # 15m
        S3) echo 1800 ;;      # 30m
        S4) echo 7200 ;;      # 120m (full S4, used as outer limit)
        S4.1) echo 10800 ;;   # 180m — root nodes need many training runs
        S4.2) echo 5400 ;;    # 90m — hyperparameter tuning
        S4.3) echo 5400 ;;    # 90m — method refinement
        S4.4) echo 3600 ;;    # 60m — ablation studies
        S5) echo 900 ;;       # 15m
        S6) echo 1500 ;;      # 25m
        S7) echo 1800 ;;      # 30m
        S8) echo 900 ;;       # 15m
        *)  echo 3600 ;;      # 60m default
    esac
}

# S4 sub-stages for checkpoint-based execution
S4_SUBSTAGES=("S4.1" "S4.2" "S4.3" "S4.4")

get_stage() {
    python3 scripts/parse_state.py current_stage
}

get_status() {
    python3 scripts/parse_state.py stage_status "$1"
}

timestamp() {
    date "+%H:%M:%S"
}

run_claude_with_retry() {
    # Wraps `claude -p` with retry logic for transient API 500 errors.
    # Usage: run_claude_with_retry <output_log> <claude_args...>
    # Returns non-zero if all retries exhausted.
    local output_log="$1"; shift
    local max_attempts=3
    local backoffs=(30 60 120)
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        attempt=$((attempt + 1))

        claude "$@" 2>&1 | tee "$output_log"
        local rc=${PIPESTATUS[0]}

        # Check for API 5xx errors or empty output
        if [ $rc -eq 0 ] && [ -s "$output_log" ] && ! grep -q "API Error: 5" "$output_log"; then
            return 0
        fi

        if [ $attempt -lt $max_attempts ]; then
            local wait=${backoffs[$((attempt - 1))]}
            echo "[$(timestamp)] WARNING: claude call failed (attempt $attempt/$max_attempts). Retrying in ${wait}s..."
            sleep "$wait"
        fi
    done

    echo "[$(timestamp)] ERROR: claude call failed after $max_attempts attempts."
    return 1
}

build_prompt_file() {
    # Build prompt into a temp file: _common.md + given skill file(s)
    # Returns path to temp file (caller must clean up)
    local tmpfile
    tmpfile=$(mktemp "${TMPDIR:-/tmp}/infi_prompt_XXXXXX.md")
    if [ -f skills/_common.md ]; then
        cat skills/_common.md >> "$tmpfile"
        printf '\n\n' >> "$tmpfile"
    fi
    for f in "$@"; do
        if [ -f "$f" ]; then
            cat "$f" >> "$tmpfile"
            printf '\n\n' >> "$tmpfile"
        fi
    done
    echo "$tmpfile"
}

run_skill_execution() {
    # Execute a skill prompt, verify, memory sync, judge, advance
    # Args: stage_label skill_files... [-- suffix_text]
    local stage_label="$1"; shift
    local guard_stage="${stage_label%%.*}"  # S4.1 -> S4 for state_guard

    local skill_files=()
    local suffix=""
    while [ $# -gt 0 ]; do
        if [ "$1" = "--" ]; then
            shift; suffix="$*"; break
        fi
        skill_files+=("$1"); shift
    done

    local prompt_file
    prompt_file="$(build_prompt_file "${skill_files[@]}")"
    if [ -n "$suffix" ]; then
        printf '\n\n%s' "$suffix" >> "$prompt_file"
    fi

    echo "[$(timestamp)] Executing skill for $stage_label..."
    local stage_timeout
    stage_timeout=$(get_timeout "$stage_label")
    if ! timeout "$stage_timeout" run_claude_with_retry "state/${stage_label}_output.log" -p "$(cat "$prompt_file")" --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent"; then
        echo "[$(timestamp)] Skill execution returned non-zero"
    fi
    rm -f "$prompt_file"

    # State Guardian: verify outputs exist
    echo "[$(timestamp)] State Guardian verifying $guard_stage outputs..."
    python3 scripts/state_guard.py verify --stage "$guard_stage"

    # Memory Sync: consolidate knowledge
    echo "[$(timestamp)] Memory Sync: consolidating knowledge from $stage_label..."
    local mem_file
    mem_file="$(build_prompt_file skills/memory_sync.md)"
    printf '\n\nStage just completed: %s' "$stage_label" >> "$mem_file"
    if ! run_claude_with_retry "state/${stage_label}_memory.log" -p "$(cat "$mem_file")" --allowedTools "Bash,Read,Write,Edit,Glob,Grep"; then
        echo "[$(timestamp)] Memory sync returned non-zero (non-fatal)"
    fi
    rm -f "$mem_file"

    # State Guardian: verify memory quality
    echo "[$(timestamp)] State Guardian verifying $guard_stage memory..."
    python3 scripts/state_guard.py verify --stage "$guard_stage"

    # LLM-as-Judge: content quality evaluation
    echo "[$(timestamp)] Running judge gate for $stage_label..."
    local judge_file
    judge_file="$(build_prompt_file skills/judge.md)"
    printf '\n\nCurrent stage to judge: %s (sub-stage: %s)' "$guard_stage" "$stage_label" >> "$judge_file"
    if ! run_claude_with_retry "state/${stage_label}_judge.log" -p "$(cat "$judge_file")" --allowedTools "Bash,Read,Write,Glob,Grep"; then
        echo "[$(timestamp)] Judge execution returned non-zero"
    fi
    rm -f "$judge_file"

    # State Guardian: advance or fail based on judge result
    # Skip advance for S4 sub-stages (S4.1, S4.2, S4.3) — only advance after S4.4
    # Otherwise advancing after S4.1 marks S4 complete, and resume skips S4.2-S4.4
    if [[ "$stage_label" == S4.* && "$stage_label" != "S4.4" ]]; then
        echo "[$(timestamp)] Sub-stage $stage_label — skipping advance (S4 advances after S4.4 only)"
    else
        echo "[$(timestamp)] Evaluating judge result..."
        python3 scripts/state_guard.py advance --stage "$guard_stage"
    fi
}

run_s4_with_checkpoints() {
    # S4 special handling: execute 4 sub-stages with checkpoint between each
    local common="skills/_common.md"
    local s4_main="skills/S4_experiments.md"
    local s4_node="skills/S4_run_node.md"

    for substage in "${S4_SUBSTAGES[@]}"; do
        # Check if this sub-stage is already complete
        local tree_complete
        tree_complete=$(python3 -c "
import json, pathlib
tree = json.loads(pathlib.Path('experiment_tree.json').read_text()) if pathlib.Path('experiment_tree.json').exists() else {}
done = tree.get('metadata', {}).get('current_stage', '4.0')
target = '${substage}'.replace('S4.', '4.')
# Compare as floats to avoid lexicographic issues (e.g., 4.10 > 4.2)
print('done' if float(done) >= float(target) + 0.1 else 'pending')
" 2>/dev/null || echo "pending")

        if [ "$tree_complete" = "done" ]; then
            echo "[$(timestamp)] Sub-stage $substage already complete, skipping."
            continue
        fi

        echo "[$(timestamp)] ─── S4 Checkpoint: $substage ───"

        # Execute sub-stage with targeted instruction
        local suffix="EXECUTE ONLY sub-stage ${substage}. Read experiment_tree.json to determine current progress. Complete this sub-stage, update experiment_tree.json, then STOP. Do not proceed to the next sub-stage."

        # Note: if run_skill_execution fails (judge says retry), we return 1.
        # The outer pipeline_loop will retry run_stage("S4"), which re-enters
        # run_s4_with_checkpoints. The Python check above skips already-completed
        # sub-stages based on experiment_tree.json metadata.current_stage, so
        # only the failing sub-stage and later ones will re-run.
        if ! run_skill_execution "$substage" "$s4_main" "$s4_node" -- "$suffix"; then
            echo "[$(timestamp)] Sub-stage $substage FAILED"
            return 1
        fi

        echo "[$(timestamp)] Sub-stage $substage checkpoint saved."
    done
    return 0
}

has_novel_methods() {
    # Check if experiment_tree.json has any nodes with design_spec
    # On error (file missing/malformed), default to triggering checkpoint (safe side)
    python3 -c "
import json, sys
try:
    tree = json.load(open('experiment_tree.json'))
    has_spec = any(n.get('design_spec') for n in tree.get('nodes', []))
    sys.exit(0 if has_spec else 1)
except Exception as e:
    print(f'WARNING: could not check design_spec: {e}', file=sys.stderr)
    sys.exit(0)  # default to checkpoint on error (safer than skipping)
" 2>/dev/null
}

needs_human_checkpoint() {
    # P0 and S2: always checkpoint
    # S3: checkpoint only if novel methods exist (have design_spec)
    case "$1" in
        P0|S2) return 0 ;;
        S3)    has_novel_methods && return 0 || return 1 ;;
        *)     return 1 ;;
    esac
}

run_human_checkpoint() {
    local stage="$1"
    echo ""
    echo "[$(timestamp)] ═══════════════════════════════════════"
    echo "[$(timestamp)] HUMAN CHECKPOINT: $stage"
    echo "[$(timestamp)] ═══════════════════════════════════════"

    # Generate checkpoint document using checkpoint.md skill
    local ckpt_file
    ckpt_file="$(build_prompt_file skills/checkpoint.md)"
    printf '\n\nGenerate checkpoint for stage: %s' "$stage" >> "$ckpt_file"
    if ! run_claude_with_retry "state/${stage}_checkpoint.log" -p "$(cat "$ckpt_file")" --allowedTools "Bash,Read,Write,Glob,Grep"; then
        echo "[$(timestamp)] Checkpoint generation failed (non-fatal, pausing anyway)"
    fi
    rm -f "$ckpt_file"

    echo ""
    echo "[$(timestamp)] Human review required before proceeding."
    echo "[$(timestamp)] Review: state/CHECKPOINT_${stage}.md"
    echo ""
    echo "  ./run.sh approve                          — approve and continue"
    echo "  ./run.sh approve --with 'your changes'    — approve with modifications"
    echo ""

    # Set registry to awaiting_human and exit pipeline.
    # User resumes via ./run.sh approve after reviewing the checkpoint.
    python3 scripts/update_state.py set_awaiting_human "$stage"
    exit 0  # Intentional: pauses pipeline until human approves
}

check_awaiting_human() {
    # Check if we're waiting for human approval
    local status
    status=$(python3 -c "
import yaml, pathlib
r = yaml.safe_load(pathlib.Path('registry.yaml').read_text())
print(r.get('status', ''))
" 2>/dev/null || echo "")
    [ "$status" = "awaiting_human" ]
}

handle_approve() {
    local modifications="${1:-}"
    if ! check_awaiting_human; then
        echo "No pending checkpoint to approve."
        exit 1
    fi

    local stage
    stage=$(python3 -c "
import yaml, pathlib
r = yaml.safe_load(pathlib.Path('registry.yaml').read_text())
print(r.get('checkpoint_stage', ''))
" 2>/dev/null)

    if [ -n "$modifications" ]; then
        echo "[$(timestamp)] Approved with modifications: $modifications"
        echo "Human modifications: $modifications" > "state/HUMAN_RESPONSE_${stage}.md"
        echo "[$(timestamp)] Re-running $stage with modifications..."
        # Reset clears checkpoint fields and resets stage to pending
        python3 scripts/update_state.py reset "$stage"
        pipeline_loop
    else
        echo "[$(timestamp)] Approved. Continuing pipeline."
        python3 scripts/update_state.py clear_checkpoint "$stage"
        pipeline_loop
    fi
}

run_stage() {
    local stage="$1"

    # S4 uses checkpoint-based execution with sub-stages
    if [ "$stage" = "S4" ]; then
        run_s4_with_checkpoints
        return $?
    fi

    # Find skill file(s) for this stage
    local skill_files=()
    for f in skills/${stage}*.md; do
        [ -f "$f" ] && skill_files+=("$f")
    done

    if [ ${#skill_files[@]} -eq 0 ]; then
        echo "[$(timestamp)] ERROR: No skill file for stage $stage"
        return 1
    fi

    run_skill_execution "$stage" "${skill_files[@]}"
}

run_hardware_detection() {
    echo "[$(timestamp)] Detecting hardware capabilities..."
    local hw_file
    hw_file="$(build_prompt_file skills/S0_hardware.md)"
    if ! run_claude_with_retry "state/hardware_detect.log" -p "$(cat "$hw_file")" --allowedTools "Bash,Read,Write,Glob,Grep"; then
        echo "[$(timestamp)] Hardware detection returned non-zero (non-fatal, continuing)"
    fi
    rm -f "$hw_file"
    if [ -f "hardware_profile.json" ]; then
        echo "[$(timestamp)] Hardware profile created successfully."
    else
        echo "[$(timestamp)] WARNING: hardware_profile.json not created. Skills will proceed without hardware constraints."
    fi
}

pipeline_loop() {
    # Hardware detection (runs once at pipeline start or when profile is missing)
    if [ ! -f "hardware_profile.json" ] || [ "${1:-}" = "fresh" ]; then
        run_hardware_detection
    fi

    local stage
    stage=$(get_stage)

    while [ "$stage" != "COMPLETE" ]; do
        local attempt=0
        local passed=false

        while [ $attempt -lt $MAX_RETRIES ] && [ "$passed" = "false" ]; do
            attempt=$((attempt + 1))
            echo ""
            echo "[$(timestamp)] ═══════════════════════════════════════"
            echo "[$(timestamp)] Stage $stage (attempt $attempt/$MAX_RETRIES)"
            echo "[$(timestamp)] ═══════════════════════════════════════"

            python3 scripts/update_state.py set_running "$stage"

            if run_stage "$stage"; then
                passed=true
                # Human checkpoint for critical decision stages
                if needs_human_checkpoint "$stage"; then
                    run_human_checkpoint "$stage"
                    # run_human_checkpoint exits the script; pipeline resumes via ./run.sh approve
                fi
            else
                echo "[$(timestamp)] Stage $stage FAILED (attempt $attempt)"
            fi
        done

        if [ "$passed" = "false" ]; then
            echo ""
            echo "[$(timestamp)] ✗ Stage $stage failed after $MAX_RETRIES attempts."
            echo "[$(timestamp)] Pipeline paused. Fix issues and run: ./run.sh resume"
            python3 scripts/update_state.py fail "$stage"
            exit 1
        fi

        stage=$(get_stage)
    done

    echo ""
    echo "[$(timestamp)] ✓ Pipeline complete! Check DELIVERY/"
}

case "${1:-help}" in
    start)
        python3 scripts/update_state.py reset_all
        pipeline_loop fresh
        ;;
    resume)
        if check_awaiting_human; then
            echo "Pipeline is waiting for human approval."
            echo "Review: state/CHECKPOINT_$(python3 -c "import yaml,pathlib;print(yaml.safe_load(pathlib.Path('registry.yaml').read_text()).get('checkpoint_stage',''))" 2>/dev/null).md"
            echo "Run: ./run.sh approve"
            exit 0
        fi
        pipeline_loop
        ;;
    approve)
        shift
        if [ "${1:-}" = "--with" ]; then
            shift
            handle_approve "$*"
        else
            handle_approve
        fi
        ;;
    status)
        python3 scripts/parse_state.py status
        ;;
    reset)
        python3 scripts/update_state.py reset "${2:?Usage: ./run.sh reset <stage>}"
        echo "Reset complete. Run ./run.sh resume to continue."
        ;;
    *)
        echo "InfiEpisteme v2.1 — Automated Research Pipeline"
        echo ""
        echo "Usage: ./run.sh {start|resume|approve|status|reset <stage>}"
        echo ""
        echo "  start                        Start from Phase 0"
        echo "  resume                       Resume from current stage"
        echo "  approve                      Approve human checkpoint and continue"
        echo "  approve --with 'changes'     Approve with modifications"
        echo "  status                       Show pipeline status"
        echo "  reset <stage>                Reset a stage (P0|S0|S1|...|S8)"
        ;;
esac
