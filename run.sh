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
    if ! timeout "$stage_timeout" claude -p "$(cat "$prompt_file")" --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent" 2>&1 | tee "state/${stage_label}_output.log"; then
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
    if ! claude -p "$(cat "$mem_file")" --allowedTools "Bash,Read,Write,Edit,Glob,Grep" 2>&1 | tee "state/${stage_label}_memory.log"; then
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
    if ! claude -p "$(cat "$judge_file")" --allowedTools "Bash,Read,Write,Glob,Grep" 2>&1 | tee "state/${stage_label}_judge.log"; then
        echo "[$(timestamp)] Judge execution returned non-zero"
    fi
    rm -f "$judge_file"

    # State Guardian: advance or fail based on judge result
    echo "[$(timestamp)] Evaluating judge result..."
    python3 scripts/state_guard.py advance --stage "$guard_stage"
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
    if ! claude -p "$(cat "$hw_file")" --allowedTools "Bash,Read,Write,Glob,Grep" 2>&1 | tee "state/hardware_detect.log"; then
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
        pipeline_loop
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
        echo "Usage: ./run.sh {start|resume|status|reset <stage>}"
        echo ""
        echo "  start          Start from Phase 0 (direction alignment)"
        echo "  resume         Resume from current stage"
        echo "  status         Show pipeline status"
        echo "  reset <stage>  Reset a stage (P0|S0|S1|...|S8)"
        ;;
esac
