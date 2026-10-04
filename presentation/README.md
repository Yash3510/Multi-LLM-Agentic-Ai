# 4CE deck · Team Kern

`4CE-Sovereign-AI-Workbench.pptx` is the 10-slide pitch for 4CE, the sovereign on-premise agentic AI workbench. It uses the 4CE chat UI's own design system, taken from the demo video and the app source:

- **Colours:** chat-page grey `#171717`, cards `#262626`, light canvas `#EEEFF1`, muted greys `#9B9B9B` (on dark) and `#666666` (on light), and violet `#7C3AED` / `#A78BFA` as the only accent. Green `#34D399` means passed or observed, and amber `#FBBF24` means checked, as they do in the app.
- **Scenes:** dark chat-UI slides alternate with light statement slides, like the demo.
- **Components:** the chat input box, the TONY → FRIDAY → JARVIS → ULTRON → YOU stepper, status chips, the approval bar, file cards, the checklist and the pixel-block wave. The 4CE mark is drawn as a vector shape from `4ce/branding/logo-mark.svg`.

Open it in **PowerPoint 2019 or Microsoft 365** and present from slide 1. Every slide uses a Morph transition: the light canvas sweeps across between dark and light slides, the violet pixel blocks drift and the 4CE mark turns. Content builds in automatically after each morph lands. Older PowerPoint versions and Google Slides fall back to a fade.

`4CE-Sovereign-AI-Workbench-preview.pdf` and `preview.jpg` are static previews with no motion. They were rendered with stand-in fonts.

## Fonts

All the fonts are Apple's, set from the theme and the generator:

- **SF Pro Display** for headings
- **SF Pro Text** for body text
- **New York** italic for the violet emphasis words
- **SF Mono** for the sandbox flags

Office doesn't include them, so install them from developer.apple.com/fonts on the machine you present from. Without them, PowerPoint substitutes the nearest kind of font: Arial, a serif and a monospace. If you can't install fonts at the venue, export a video from a machine that has them (File → Export → MP4). The video keeps both the fonts and the Morph motion.

## Editing

The shapes that morph share a name on every slide: `!!canvas`, `!!glow`, `!!px1`–`!!px7`, `!!mark`, `!!eyebrow` and `!!title`. To edit or rearrange one, open Home → Arrange → Selection Pane. Keep the names, or Morph will stop matching the shapes from slide to slide.

## Rebuilding

```bash
npm install pptxgenjs react-icons react react-dom sharp   # in any folder; point NODE_PATH at its node_modules
node generator/assets.cjs                                  # icons, glow, pixel wave, logo outline
node generator/build.cjs deck.raw.pptx                     # slides, plus anim.json and theme.json
python generator/postprocess.py deck.raw.pptx anim.json deck.pptx   # Morph, entrance animations, theme colours
```

The palette is defined once, in `THEME` at the top of `build.cjs`.
