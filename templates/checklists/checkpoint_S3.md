# S3 Checkpoint — Implementation Review (Novel Methods)

> This checkpoint triggers because experiment_tree.json contains novel methods (nodes with `design_spec`).
> Review the implementation before training starts to avoid wasting GPU hours.

## Fixed Checklist

### Novel Method Implementation
- [ ] Each `key_decision` from `design_spec` has a documented choice in README_code.md
- [ ] Each `invariant` from `design_spec` has been tested and passes
- [ ] Each `constraint` from `design_spec` is satisfied in the implementation
- [ ] Hyperparameter scales are appropriate for the problem domain (not blindly copied from other contexts)
- [ ] Deviations from the original design are documented and justified

### General Implementation
- [ ] All nodes in experiment_tree.json have status "runnable"
- [ ] Smoke tests pass for all methods (forward, backward, loss decreases)
- [ ] Parameter counts and memory usage are within hardware limits
- [ ] No method has significantly different parameter count without justification

## Implementation Summary

See `README_code.md` → Implementation Summary section for details.

## Raw Files for Deep Review

- `src/models/` — method implementations
- `experiment_tree.json` — node specs with `design_spec`
- `README_code.md` — implementation summary and reproduction instructions

{LLM_BRIEF}
