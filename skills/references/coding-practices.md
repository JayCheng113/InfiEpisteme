# Coding Practices for Research Implementation

> Adapted from [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills): test-driven-development, lint-and-validate, debugging-strategies, acceptance-orchestrator.

## Core Principle

**Verify as you build, not after.** GPU hours are expensive. A bug discovered during training wastes hours. A bug caught during implementation wastes minutes.

## Incremental Build-and-Verify

Write code in layers. After each layer, verify it works before building the next layer on top.

```
Layer 1: Foundation (data loading, base model)
  → verify: forward pass produces correct shapes, loss computes

Layer 2: Each method/variant (one at a time)
  → verify: output shape matches baseline, loss decreases over a few steps

Layer 3: Training loop
  → verify: checkpointing works, metrics log correctly, resumption works

Layer 4: Evaluation
  → verify: metrics compute correctly on known inputs
```

**Why this order matters**: If Layer 1 has a silent bug (e.g., wrong normalization), every method built on top inherits the bug. You won't know until training produces nonsensical results — after burning GPU hours.

## Verification Strategies

### Smoke Tests (fast, run always)

Every implemented component should pass a basic smoke test:
- Does it run without errors?
- Are output shapes correct?
- Does loss decrease over a handful of steps?

Run these after implementing each component, not after implementing everything.

### Invariant Checks (correctness)

For methods with known properties, verify them:
- A method that should reduce to baseline under certain parameters — does it?
- A method that should be equivalent to another under specific settings — is it?
- Gradient norms should be finite and non-zero after a forward-backward pass.

### Regression Checks (nothing broke)

After adding a new method, re-run smoke tests for all previously implemented methods. New code should not break existing code.

## Validation After Every Change

> Adapted from lint-and-validate: "No code should be committed or reported as 'done' without passing checks."

After each implementation unit:
1. **Run**: Execute the smoke test for the new component
2. **Check**: Verify output is correct (shapes, values, gradients)
3. **Regression**: Confirm previously working components still work

Do not batch all testing to the end. If something breaks, you want to know immediately — not after 7 methods are built on a broken foundation.

## Systematic Debugging

> Adapted from debugging-strategies.

When a test fails or training produces unexpected results:

1. **Reproduce**: Isolate the minimal input that triggers the issue
2. **Hypothesize**: Form specific theories about what's wrong (not "something is broken")
3. **Binary search**: If the bug is in a complex pipeline, comment out half to narrow scope
4. **Compare**: If a reference implementation exists, compare intermediate values tensor-by-tensor
5. **Document**: Record what was wrong and why — this goes to `negative-results.md`

## Definition of Done

A component is "done" when:
- [ ] It runs without errors on the target hardware
- [ ] Output shapes match the specification
- [ ] Loss decreases over a few training steps (gradient flow is healthy)
- [ ] It does not break any previously implemented component
- [ ] Edge cases from the paper/design are handled (e.g., first layer has no preceding layers)

An entire implementation stage (S3) is "done" when:
- [ ] All methods in experiment_tree.json have status "runnable"
- [ ] Each method passes its smoke test independently
- [ ] The training script runs end-to-end for a few steps with each method
- [ ] The evaluation script produces metrics on test data
