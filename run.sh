#!/bin/bash
# InfiEpisteme v2 — .md-native research pipeline driver
# Usage: ./run.sh {start|resume|status|reset <stage>}

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

MAX_RETRIES=3

get_stage() {
    python3 scripts/parse_state.py current_stage
}

get_status() {
    python3 scripts/parse_state.py stage_status "$1"
}

timestamp() {
    date "+%H:%M:%S"
}

run_stage() {
    local stage="$1"

    # Find skill file(s) for this stage
    local skill_files=""
    for f in skills/${stage}*.md; do
        [ -f "$f" ] && skill_files="$skill_files $f"
    done

    if [ -z "$skill_files" ]; then
        echo "[$(timestamp)] ERROR: No skill file for stage $stage"
        return 1
    fi

    # Build prompt: _common.md + stage skill(s)
    local prompt=""
    if [ -f skills/_common.md ]; then
        prompt="$(cat skills/_common.md)"$'\n\n'
    fi
    for f in $skill_files; do
        prompt="$prompt$(cat "$f")"$'\n\n'
    done

    echo "[$(timestamp)] Executing skill for $stage..."

    # THE KEY: Claude Code executes the skill
    if ! claude -p "$prompt" --allowedTools "Bash,Read,Write,Edit,Glob,Grep,Agent" 2>&1 | tee "state/${stage}_output.log"; then
        echo "[$(timestamp)] Skill execution returned non-zero"
    fi

    # State Guardian: verify outputs exist
    echo "[$(timestamp)] State Guardian verifying $stage outputs..."
    python3 scripts/state_guard.py verify --stage "$stage"

    # Memory Sync: consolidate knowledge into .ai/ (dedicated LLM call)
    echo "[$(timestamp)] Memory Sync: consolidating knowledge from $stage..."
    local mem_prompt="$(cat skills/_common.md)"$'\n\n'"$(cat skills/memory_sync.md)"$'\n\n'"Stage just completed: $stage"
    if ! claude -p "$mem_prompt" --allowedTools "Bash,Read,Write,Edit,Glob,Grep" 2>&1 | tee "state/${stage}_memory.log"; then
        echo "[$(timestamp)] Memory sync returned non-zero (non-fatal)"
    fi

    # State Guardian: verify memory quality
    echo "[$(timestamp)] State Guardian verifying $stage memory..."
    python3 scripts/state_guard.py verify --stage "$stage"

    # LLM-as-Judge: content quality evaluation
    echo "[$(timestamp)] Running judge gate for $stage..."
    local judge_prompt="$(cat skills/_common.md)"$'\n\n'"$(cat skills/judge.md)"$'\n\n'"Current stage to judge: $stage"
    if ! claude -p "$judge_prompt" --allowedTools "Bash,Read,Glob,Grep" 2>&1 | tee "state/${stage}_judge.log"; then
        echo "[$(timestamp)] Judge execution returned non-zero"
    fi

    # State Guardian: advance or fail based on judge result
    echo "[$(timestamp)] Evaluating judge result..."
    if python3 scripts/state_guard.py advance --stage "$stage"; then
        return 0
    else
        return 1
    fi
}

pipeline_loop() {
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
        pipeline_loop
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
        echo "InfiEpisteme v2 — Automated Research Pipeline"
        echo ""
        echo "Usage: ./run.sh {start|resume|status|reset <stage>}"
        echo ""
        echo "  start          Start from Phase 0 (direction alignment)"
        echo "  resume         Resume from current stage"
        echo "  status         Show pipeline status"
        echo "  reset <stage>  Reset a stage (P0|S0|S1|...|S8)"
        ;;
esac
