---
title: Demo script
type: workflow
status: active
updated: 2026-09-25
tags:
  - 4ce
  - testing
---

# Demo script

Ten prompts, in order, each chosen because it evidences a different thing the
problem statement asks for. Every one has been run against this build; the
timings are measured on an RTX 4050 laptop (6 GB) with both models loaded at
8192 context.

Run `python 4ce/preflight.py --fix` first. If it does not say **Ready**, do not
start — the most common failure is Bionic having quietly reloaded a model at
65,536 context, which makes everything four to ten times slower with no error
anywhere.

Open the interface once before the audience arrives. The first page load in dev
mode compiles for roughly twenty-five seconds.

---

## P1 · It knows when not to be an agent

> hello

**~3 s. No agent chain, no approval.**

Say: a multi-agent system that convenes a committee to say good morning is a
liability. TONY classifies first, and conversation is answered directly by the
small model. Point at the footer: `direct reply · qwen3-1.7b · no agent chain`.

This matters because the rest of the demo is slow *on purpose*, and the contrast
shows the cost is being spent deliberately.

---

## P2 · Grounded in the plant's own documents

> What is the acceptable mechanical seal leakage rate under SOP-MEC-014, and what must happen if it is exceeded?

**~115 s. The slowest prompt — set expectations before pressing enter.**

The answer quotes clause 2.1 and clause 2.2 verbatim, including the thirty-day
replacement requirement, from a document indexed locally. Open the provenance
table and point at **Grounding**: it reports the number of characters of
retrieved passages that actually reached the grounding agent - about 3,200 here.

Say: that row exists because the honest failure mode here is an answer that
looks grounded and is not. It is reported rather than assumed - and it reports
**none** rather than a number when nothing was retrieved, which is what P4 shows.
Retrieval only runs where documents can help, so a code prompt is not silently
padded with plant procedures.

If time is tight, skip this one — P3 covers document handling faster.

---

## P3 · The flagship: report in, approval note out

> Draft an approval note for the P-101B pump inspection report: mechanical seal leak measured at 18 drops per minute, vibration 7.1 mm/s RMS.

**~30–40 s, occasionally ~110 s if verification forces a replan.**

Routes to `qwen3-vl-4b`. The threshold comparison is **not** done by a model —
`check_sop_thresholds` compares against an authored rule pack and cites the
clause that decided each line. Readings with no threshold come back `NO DATA`,
never `PASS`.

Then the approval dialog appears. **Type something other than APPROVE first** and
show the deliverable withheld, with the provenance retained and no file written.
Re-run, type `APPROVE`, and the `.docx` appears with a download link.

Say: the gate fails closed. An empty box, a wrong word or a cancel all withhold.

---

## P4 · Code that is executed, not just written

> Write a Python function that returns the median of a list and print it for [5, 3, 9, 1, 7].

**~30–60 s. Routes to `qwen3-1.7b` — a different model from P3.**

Two things to point at. The sandbox block shows `--network none`, `--read-only`,
`--cap-drop ALL`, and **stdout: 5** — real output from a container, not a claim.
And after approval, a `.py` file you can download and run.

Say: this is the multi-model criterion. Same request pipeline, different task
type, different model, and the routing rationale is printed. Grounding on this
one reads **none**, which is the same row as P2 telling the truth in the other
direction.

The saved file is named after what the code defines - `calculate_median.py` -
rather than after the sentence that asked for it.

Then point at **what was checked**. The first line is 4CE's own, from the
sandbox, not a model: a crash, a failed assertion or - measured on this very
prompt - a program asked to print that printed nothing is a failure, and the
code goes back once with the real error attached. A clean run that asserts
nothing reads *could not check*, not a tick. If the chain shows "sent it back ·
2nd try", open "What changed on try 2": the objection and the fix are both
there.

ULTRON's verdict word decides, but when it passes a result and still lists
objections, the header says "Passed by ULTRON, with 1 reservation" in amber -
never a clean pass over its own problems.

Keep code prompts simple. The small model handles this reliably; asked for
something like an ISO 10816 zone converter it produced prose and no code at all.

---

## P4b · A calculation, with every step shown

> Calculate the remaining life of the P-101B discharge line as an Excel workbook: previous thickness 12.0 mm three years ago, current thickness 11.2 mm, required thickness 9.5 mm.

The arithmetic is done in code, not by a model: corrosion rate 0.267 mm/year,
remaining life 6.4 years, each step written out with its units. Then the point
worth making: half the remaining life says 3.2 years, but the margin is 1.7 mm,
and **SOP-MEC-014 §4.2** requires a six-month interval below 2.0 mm - so the
next measurement is **6 months**, and the working says which rule set it. The
SOP rule pack found §4.2; the calculation took it as its maximum; the model
only quoted the result.

Open the workbook. *Remaining life* is live formulas over blue input cells:
change the current thickness and the corrosion rate, remaining life and next
measurement recalculate in Excel.

---

## P5 · The sovereignty claim, evidenced

> Prove nothing leaves the premises - audit the running configuration.

**~30 s.**

`verify_sovereignty` reads the *running* configuration and returns a pass/fail
table — 18 of 18 on this build. It is not the model describing what it imagines
the configuration to be.

The eighteen cover the model and embedding endpoints, the extraction engine,
telemetry, update checks, community sharing, web search, **web page fetching,
image generation and editing, speech to text, text to speech, external tool
servers and terminal servers**. The last seven were added after an audit that
read 11 of 11 turned out not to be looking at them — the interface still offered
"Attach Webpage", which hands the server a URL and has it fetch the page. That
action is now withdrawn, and the audit checks that it is.

Then show that the claim is observed, not just configured. The navbar has
carried the egress count since the first click; open it - the Sovereignty page.

- **The number.** External connections from the workbench's own processes -
  backend, model server, frontend, 16 processes on the demo box - counted every
  250 ms since the window opened. Start a new window before the demo, so the
  count covers exactly the session the judges watch.
- **The canary.** Press it. It tries a TCP handshake from the backend to a
  public address. *Blocked* is the control demonstrated rather than described;
  *reachable* says plainly that nothing on this host stops a connection.
- **Every answer's receipt** now reads "0 external calls, observed" - counted
  over that run - where it used to print a constant.

Answer the obvious question before it is asked: this samples sockets, it does
not capture packets, and the page lists what it cannot see. For the last word,
pull the network cable and re-run the demo — it still works.

**Before the day:** the monitor caught Bionic contacting a Cloudflare address to
check for its own updates. Add the egress rule for `Bionic.exe` (see "Making it
physical" in `HOW_TO_RUN.md`), run the canary until it reads *Blocked*, then
start a new window. Otherwise the count will not read zero on stage, and
that will be the truth.

---

## P6 · Whatever file type was asked for

> Give me the P-101B readings as a CSV file: seal leak 18 drops/min, vibration 7.1 mm/s, bearing temperature 71 C.

**~38 s.** Produces a real `.csv`, named `p101b_readings_as_a_csv.csv`. Worth
opening: the last column carries the SOP
verdict the deterministic tool decided, so the spreadsheet inherits the
clause-cited assessment rather than the model's opinion.

Say: the type follows the request — `.py`, `.sql`, `.csv`, `.json`, `.md` and
the rest, and an **Excel workbook** or a **PowerPoint deck** by name:

> Give me the P-101B readings as an Excel workbook: seal leak 18 drops/min, vibration 7.1 mm/s, bearing temperature 71 C.

Worth opening. Each table in the answer is a sheet, with numbers stored as
numbers and units moved into the headers; a stated total is a live `SUM`, and
only once it has been checked to add up. A sheet called *SOP rule pack
verdicts* is the deterministic table verbatim - "below 5 drops/min", not a
model's paraphrase of it - and *About this workbook* carries the same approval
record as the chat. "Make a short PowerPoint deck on replacing the P-101B
seal…" gives a deck with a slide per section, the verdict table as a native
table slide, speaker notes, and a closing "How this was produced" slide.

Measured on this build: 18 drops/min comes back REVIEW under §2.2 - supervisor
concurrence and replacement within 30 days - and 7.1 mm/s is reported as given
but not assessed, because SOP-MEC-014 states vibration as ISO 10816 zones whose
boundaries depend on the machine class. Neither is a model's guess. Set `output_dir` on the tool and every released file also lands in a
folder you choose, such as an inspection share.

---

## P7 · Multimodal: a scan, a handwritten log, a drawing

Three images, one path. Each is read once into numbered fields - the value, its
unit, how sure the model is, and a box on the image where it was read - before
FRIDAY analyses it. The table and a copy of the image with every field boxed go
into the draft you approve, the answer and the Word report.

**The handwritten shift log.** Attach `4ce/demo/samples/shift_log_P-101.png`:

> Here is last night's handwritten shift log for the P-101 pumps. Read the readings and tell me what needs action before the day shift.

**~70 s; about two minutes when ULTRON sends the draft back.** All five readings
come back, each boxed on the page: seal weeping on P-101B, discharge pressure
and vibration on P-101A, bearing temperature, the missing guard bolt. The
leakage figure is smudged on purpose. It is boxed in orange, marked **check**
in the table and listed under the checks as read with less than full
confidence. The rule pack takes the readings as it takes a request's own:
6 drops/min is REVIEW under §2.2, the missing guard bolt FAIL under §5.1.

Say: the model says how sure it is, and 4CE shows where it looked. The reviewer
compares box 1 with the smudge before approving - a model's word is not a
reading.

**The P&ID.** Attach `4ce/demo/samples/pid_P-101_excerpt.png`:

> Extract every tag and line number from this P&ID excerpt and describe how the pumps connect to E-101.

**~2-3 min.** All fifteen tags, in a register grouped by type: T-101, both pump
trains with their isolation and non-return valves, PT-101, FE-101, FT-101,
FIC-101, FV-101, both line numbers and E-101. The type comes from the tag's
ISA 5.1 letters, not the model - FE-101 is an instrument even when the model
files it as equipment. FRIDAY then traces the flow: tank, suction header, the
pumps in parallel, the common discharge header, the flow loop, E-101.

Say: on a drawing the boxes are approximate - most sit on their tag, one or two
beside it. The register is what you check; the box says where to look.

**The scanned report.** Attach `4ce/demo/samples/inspection_report_P-101B.png`:

> Read this scanned inspection report and list every measured value.

**~2 min; about four when ULTRON sends the draft back.** The reading pass
takes about a minute and returns thirteen fields, the report's header among
them: seal weeping 3 to 4 drops/min, bearing housing temperature 71 °C,
vibration 4.1 mm/s RMS, the coupling guard fastener missing at position 3 of
4, suction and discharge pressure 2.4 and 18.6 bar g, and minimum wall
thickness 11.2 mm against a 9.5 mm retirement thickness - each boxed on the
page.

Say: a scanned page, a handwritten note and a drawing, read on the machine by
an open-weight model, with nothing leaving the building - and every value
shown where it was read.

Answer keys for the log and the P&ID sit beside them in `4ce/demo/samples/`, and
`4ce/eval_vision.py` scores the reading pass against them - see "Reading images"
in `HOW_TO_RUN.md`.

---

## P8 · A new model, without a code change

The statement asks that new open-weight models be "addable later without
redesigning the system". Show it rather than say it.

Open the Sovereignty page, *Models on this machine*: every model the router
chooses between, its capabilities, context, weights and licence, and whether
it is served. Point at the routing line under it - `code` needs `coding`, and
so on. Then open `4ce/models.json`, add an entry (the one in "Adding a model"
in `HOW_TO_RUN.md` uses a model already on the demo box), run `install.py`,
and refresh: it is in the table. Ask anything and the routing line in the
answer's provenance lists it among the candidates - chosen, "lacks coding",
or "not served" - with no code touched.

---

## P9 · A spreadsheet, changed only in a copy - and the trail it leaves

Attach `4ce/demo/samples/thickness_survey_P-101B.xlsx`, then:

> Add the corrosion rate and remaining life for each location to this thickness survey.

**~1 min; about two when the draft is sent back.** The workbook is read by a
tool, cell by cell with its formulas, and its five locations go to the SOP
rule pack one by one: four have less than 2.0 mm of margin, so SOP-MEC-014
§4.2's six months caps their next inspection - on the shell east, 0.5 years
where half the remaining life alone would say 3.2. The calculation works
every location in code.

Before you approve, point at **The workbook, on approval** at the end of the
draft: the four columns a copy will get - corrosion rate, remaining life, the
SOP interval, next inspection - as formulas, and what Excel will calculate
them to. Approve, and the copy appears as a download; the file that was
attached is not changed. Open it in Excel: the formulas are live, and change a
reading to see them recalculate.

Say: the reviewer approved exactly what was written, and the original was
never at risk. A formula that could reach outside the workbook - a web
service, another file - is refused.

Then open the Sovereignty page, **Audit trail**. The run's entries are at the
top: the request, the sources, the sheet read with its SHA-256, each rule-pack
check, each model call with the hashes of what went in and out, the verdict,
your approval, the copy written, and the release, whose fingerprint is the
receipt's. Press **Verify the whole chain**.

Say: each entry is sealed with the hash of the one before. Change or remove
one, and the chain breaks at that entry - this page and preflight both say
where.

---

## Questions worth pre-empting

**"Is the verification real, or is it marking its own homework?"** Open the
provenance table. ULTRON runs on a different model from JARVIS by default —
code routes to `qwen3-1.7b` and ULTRON crosses to `qwen3-vl-4b`, and the reverse
for documents. That is the default, not a configured special case.

**"What happens when it gets something wrong?"** It has. Before the threshold
tool was wired in, the verifier read a 6.2 mm wall against a 6.0 mm retirement
limit as a breach — the comparison inverted. That is why the arithmetic is now
done by an authored rule pack and not by a model.

**"How do you know nothing leaves?"** P5, plus the honest limit stated with it.

**"Can we see it fail safely?"** The withheld-deliverable path in P3, and the
Stop button mid-run, which records what completed and states that nothing was
released.

---

## Reading the provenance table

Two rows say something specific, and a sharp reader will test them.

**Elapsed** is *working* time. The wait while a reviewer reads the deliverable
and types APPROVE is excluded, because that is the reviewer's time and counting
it made a forty-second task report two minutes.

**Tools run** lists only the tools that acted on this request. The SOP rule pack
runs when the request carries measurements, or when a scanned page supplies
them; it does not run on a sovereignty audit, which has nothing to compare.

## If something looks wrong on the day

`python 4ce/preflight.py --fix` restores the model loads. `python 4ce/install.py`
restores the plugins, the tool attachment, and the restricted model picker - the
last of those lives in the application database rather than in the repository,
so a rebuilt database needs it.

If someone pastes a long document into the prompt, the turn fails and says so:
*"returned no content — request (10258 tokens) exceeds the available context
size (8192 tokens)"*. That is the models being loaded at 8192 on purpose, not a
fault. Attach the file instead of pasting it — retrieval sends only the passages
that matter, which is the whole point of P2.

The one failure seen in rehearsal that neither command prevents is a code answer
truncated mid-block: the per-agent token ceiling is `max_tokens` (900) in the
orchestrator's valves, and a model that reasons at length before answering can
run out of room. It shows as an unterminated code fence and an ULTRON failure.
Re-running the prompt is usually enough; raising the valve trades speed for
headroom.
