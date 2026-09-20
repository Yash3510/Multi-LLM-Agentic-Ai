# Demo script

Seven prompts, in order, each chosen because it evidences a different thing the
problem statement asks for. Every one has been run against this build; the
timings are measured on an RTX 4050 laptop (6 GB) with both models loaded at
8192 context.

Run `python 4ce/preflight.py --fix` first. If it does not say **Ready**, do not
start — the most common failure is LM Studio having quietly reloaded a model at
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

Keep code prompts simple. The small model handles this reliably; asked for
something like an ISO 10816 zone converter it produced prose and no code at all.

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

Be ready for the obvious question, and answer it before it is asked: this reads
configuration, not packets. A process could open a socket it never declared.
`SECURITY.md` states that limit. For proof rather than assurance, pull the
network cable and re-run the demo — it still works.

---

## P6 · Whatever file type was asked for

> Give me the P-101B readings as a CSV file: seal leak 18 drops/min, vibration 7.1 mm/s, bearing temperature 71 C.

**~38 s.** Produces a real `.csv`, named `p101b_readings_as_a_csv.csv`. Worth
opening: the last column carries the SOP
verdict the deterministic tool decided, so the spreadsheet inherits the
clause-cited assessment rather than the model's opinion.

Say: the type follows the request — `.py`, `.sql`, `.csv`, `.json`, `.md` and
the rest. Set `output_dir` on the tool and every released file also lands in a
folder you choose, such as an inspection share.

---

## P7 · Multimodal, on the real artefact

Attach `4ce/demo/samples/inspection_report_P-101B.png`, then:

> Read this scanned inspection report and list every measured value.

**~36 s.** Extracts discharge pressure 18.6 bar g, minimum measured wall
thickness 11.2 mm against a 9.5 mm retirement thickness, bearing housing
temperature 71 °C against an 80 °C alarm limit, vibration 4.1 mm/s in ISO 10816
zone B, and the missing coupling guard fastener.

Say: a scanned page, read on the machine, by an open-weight model, with nothing
leaving the building.

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

The one failure seen in rehearsal that neither command prevents is a code answer
truncated mid-block: the per-agent token ceiling is `max_tokens` (900) in the
orchestrator's valves, and a model that reasons at length before answering can
run out of room. It shows as an unterminated code fence and an ULTRON failure.
Re-running the prompt is usually enough; raising the valve trades speed for
headroom.
