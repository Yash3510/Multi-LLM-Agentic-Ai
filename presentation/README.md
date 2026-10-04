# 4CE deck · Team Kern

`4CE-Sovereign-AI-Workbench.pptx` is the 10-slide pitch for 4CE, the sovereign on-premise agentic AI workbench. It uses the 4CE chat UI's own design system, taken from the demo video and the app source:

- **Colours:** chat-page grey `#171717`, cards `#262626`, light canvas `#EEEFF1`, muted greys `#9B9B9B` (on dark) and `#666666` (on light), and violet `#7C3AED` / `#A78BFA` as the only accent. Green `#34D399` means passed or observed, and amber `#FBBF24` means checked, as they do in the app.
- **Scenes:** dark chat-UI slides alternate with light statement slides, like the demo.
- **Components:** the chat input box, the TONY → FRIDAY → JARVIS → ULTRON → YOU stepper, status chips, the approval bar, file cards, the checklist and the pixel-block wave. The 4CE mark is drawn as a vector shape from `4ce/branding/logo-mark.svg`.

Open it in **PowerPoint 2019 or Microsoft 365** and present from slide 1. Every slide uses a Morph transition: the light canvas sweeps across between dark and light slides, the violet pixel blocks drift and the 4CE mark turns. Content builds in automatically after each morph lands. Older PowerPoint versions and Google Slides fall back to a fade.

`4CE-Sovereign-AI-Workbench-static.pptx` is the same deck with no motion at all: no Morph transitions and no entrance animations. Every slide appears complete when you advance to it. Use it where animations misbehave, for printing, or for sharing as a document.

`4CE-Sovereign-AI-Workbench.html` is the fallback if PowerPoint misbehaves. It is one self-contained file, with fonts, icons and images embedded, that opens offline in any modern browser. It has the same slides with the same motion: the shared shapes glide between slides as they do with Morph, and content builds in after each move. Controls:

- **→, Space, Page Down or a click:** next slide (a clicker works too)
- **←:** previous slide
- **F:** full screen
- **N:** speaker notes
- **M:** motion on or off
- **?:** help

Add `?static` to the address to open it with no motion. Printing from the browser gives one slide per page.

`4CE-Sovereign-AI-Workbench-preview.pdf` and `preview.jpg` are static previews with no motion. They were rendered with the deck's own fonts.

## Fonts

The deck uses the chat UI's own fonts (`src/tailwind.css`, `src/app.css`): **Inter** for all text, and **JetBrains Mono** for the sandbox flags. Both are free and open-licensed. Office doesn't include them, so install them on the machine you present from (Google Fonts has both). The app also ships Inter as `static/assets/fonts/Inter-Variable.ttf`. Without them, PowerPoint substitutes Arial and a monospace face. If you can't install fonts at the venue, export a video from a machine that has them (File → Export → MP4). The video keeps both the fonts and the Morph motion.

## Editing

The shapes that morph share a name on every slide: `!!canvas`, `!!glow`, `!!px1`–`!!px7`, `!!mark`, `!!eyebrow` and `!!title`. To edit or rearrange one, open Home → Arrange → Selection Pane. Keep the names, or Morph will stop matching the shapes from slide to slide.

## Rebuilding

```bash
npm install pptxgenjs react-icons react react-dom sharp   # in any folder; point NODE_PATH at its node_modules
node generator/assets.cjs                                  # icons, glow, pixel wave, logo outline
node generator/build.cjs deck.raw.pptx                     # slides, plus anim.json and theme.json
python generator/postprocess.py deck.raw.pptx anim.json deck.pptx   # Morph, entrance animations, theme colours
python generator/postprocess.py deck.raw.pptx anim.json deck-static.pptx --static   # the no-motion version
node generator/html.cjs deck.html                          # the browser version (also needs @fontsource/jetbrains-mono)
```

`html.cjs` draws the same slides as `build.cjs`: it loads `build.cjs` with a stand-in for pptxgenjs and renders each shape as HTML. It trims the app's Inter font to the deck's characters with Python's fontTools (with `brotli` installed), and embeds the whole font if fontTools is missing.

The palette is defined once, in `THEME` at the top of `build.cjs`.
