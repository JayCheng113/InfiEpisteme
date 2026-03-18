# LaTeX Debugging Quick Reference

> Adapted from [latex-document-skill](https://github.com/ndpvt-web/latex-document-skill) debugging guide and long-form best practices.

## Reading Error Messages

LaTeX errors follow a 3-line structure:
1. `!` line: error type
2. `l.` line: line number where detected (not necessarily where the mistake is)
3. Context: shows processed vs unprocessed text

**Find errors in log**: `grep "^!" paper/main.log`

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Undefined control sequence` | Missing `\usepackage` or typo | Add package or fix command name |
| `Missing $ inserted` | Math outside math mode, or unescaped `_`, `%`, `&` | Wrap in `$...$` or escape with `\` |
| `Missing \begin{document}` | Stray character or encoding issue before `\begin{document}` | Check for BOM or hidden characters |
| `Environment ... undefined` | Missing package | Add required `\usepackage` |
| `Unbalanced braces` | Mismatched `{` and `}` | Count braces; use editor matching |
| `File not found` | Wrong path to figure or input file | Check relative paths from main.tex |
| `Overfull \hbox` | Content too wide for column | Resize figure, reword text, or add `\allowbreak` |
| `Option clash for package` | Package loaded twice with different options | Use `\PassOptionsToPackage` before `\documentclass` |
| `Extra alignment tab` | Wrong number of `&` in tabular | Match `&` count to column spec |
| `Missing \endgroup` | Unclosed environment or group | Find unmatched `\begin` |
| `Lonely \item` | `\item` outside list environment | Wrap in `itemize` or `enumerate` |
| `Float too large` | Figure/table exceeds page dimensions | Reduce size or use `[p]` placement |
| `Citation undefined` | `\cite{key}` not in `.bib` or bibtex not run | Run bibtex/biber; check key spelling |
| `Reference undefined` | `\ref{label}` target missing | Run LaTeX twice; check `\label` exists |

## Silent Failures (compiles but wrong output)

| Symptom | Cause | Fix |
|---------|-------|-----|
| `<` shows as `¡`, `>` as `¿` | Angle brackets in T1 text mode | Use `$<$`, `$>$` or `\textless`, `\textgreater` |
| Bibliography empty | bibtex/biber not run | Run: pdflatex → bibtex → pdflatex → pdflatex |
| Figures in wrong position | LaTeX float algorithm | Use `[htbp]` not `[H]`; `[H]` needs `float` package |
| Package silently overrides another | Load order issue | Load hyperref last |

## Debugging Strategy

1. **Fix top-to-bottom**: first error causes cascading false errors
2. **Binary search**: comment out half the document to isolate
3. **Draft mode**: `\documentclass[draft]{article}` skips images, marks overfull boxes
4. **Incremental compile**: compile after each section, not at the end

## Package Load Order

```
Font (fontspec) → Encoding (inputenc, fontenc) → Math (amsmath) →
Graphics (graphicx) → Tables (booktabs) → Bibliography (natbib/biblatex) →
Floats (float) → Other → Hyperref (LAST)
```

## Long-Form Document Rules (5+ pages)

1. **Prefer prose over bullets** — fewer than 15 itemize blocks per 40 pages
2. **Image width**: 0.75-0.85\textwidth, not 0.95
3. **Escape angle brackets**: `<` → `$<$`, `>` → `$>$` in text mode
4. **Global list compaction**: add `\setlist[itemize]{nosep}` with enumitem
5. **Vary section formats**: don't repeat bullets-only across sections
6. **Limit \newpage**: let LaTeX handle page breaks naturally
7. **Widow/orphan control**: `\widowpenalty=10000 \clubpenalty=10000`
8. **\noindent after display math** when text continues same thought

## Special Character Escaping

Always escape in text mode: `%` → `\%`, `$` → `\$`, `&` → `\&`, `#` → `\#`, `_` → `\_`, `~` → `\textasciitilde`, `{` → `\{`, `}` → `\}`

## Academic Paper Compilation Sequence

```bash
cd paper
pdflatex -interaction=nonstopmode main.tex   # first pass
bibtex main                                    # bibliography
pdflatex -interaction=nonstopmode main.tex   # resolve refs
pdflatex -interaction=nonstopmode main.tex   # final pass
```

Check `main.log` for `!` errors and `main.blg` for bibtex errors.
