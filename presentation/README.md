# Team Kern · SIH 2026 deck

`Team-Kern-SIH2026-Sovereign-AI.pptx` is the 10-slide pitch for problem statement SIH26117. It borrows the Circle infographic template's turning wheel, set in an industrial palette: graphite and bone, with safety orange as the only accent.

Open it in **PowerPoint 2019 or Microsoft 365** and present from slide 1. Every slide uses a Morph transition, and the content builds in automatically after each morph lands. Older PowerPoint versions and Google Slides fall back to a fade.

`Team-Kern-SIH2026-Sovereign-AI-preview.pdf` is a static preview with no motion. It was rendered with substitute fonts.

## Editing

The pieces that morph share a name on every slide: `!!band`, `!!wheel`, `!!ringA`, `!!ringB`, `!!ghost` and `!!title`. To edit or rearrange one, open Home → Arrange → Selection Pane. Keep the names, or Morph will stop matching the shapes from slide to slide.

Headings use Arial Black and body text uses Calibri, both set in the theme. To use League Spartan instead, change the heading font once under Design → Variants → Fonts.

## Rebuilding

```bash
npm install pptxgenjs react-icons react react-dom sharp   # in any folder; point NODE_PATH at its node_modules
node generator/assets.cjs                                  # wheel, glow and icon PNGs
node generator/build.cjs deck.raw.pptx                     # slides, plus anim.json and theme.json
python generator/postprocess.py deck.raw.pptx anim.json deck.pptx   # Morph, entrance animations, theme colours
```

The palette is defined once, in `THEME` at the top of `build.cjs`.
