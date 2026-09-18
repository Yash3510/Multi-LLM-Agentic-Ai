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

**~100 s. The slowest prompt — set expectations before pressing enter.**

The answer quotes clause 2.1 and clause 2.2 verbatim, including the thirty-day
replacement requirement, from a document indexed locally. Open the provenance
table and point at **Grounding**: it reports the number of characters of
retrieved context that actually reached the grounding agent.

Say: that row exists because the honest failure mode here is an answer that
looks grounded and is not. It is reported rather than assumed.

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

**~20–50 s. Routes to `qwen3-1.7b` — a different model from P3.**

Two things to point at. The sandbox block shows `--network none`, `--read-only`,
`--cap-drop ALL`, and **stdout: 5** — real output from a container, not a claim.
And after approval, a `.py` file you can download and run.

Say: this is the multi-model criterion. Same request pipeline, different task
type, different model, and the routing rationale is printed.

Keep code prompts simple. The small model handles this reliably; asked for
something like an ISO 10816 zone converter it produced prose and no code at all.

---

## P5 · The sovereignty claim, evidenced

> Prove nothing leaves the premises - audit the running configuration.

**~30 s.**

`verify_sovereignty` reads the *running* configuration and returns a pass/fail
table — 11 of 11 on this build. It is not the model describing what it imagines
the configuration to be.

Be ready for the obvious question, and answer it before it is asked: this reads
configuration, not packets. A process could open a socket it never declared.
`SECURITY.md` states that limit. For proof rather than assurance, pull the
network cable and re-run the demo — it still works.

---

## P6 · Whatever file type was asked for

> Give me the P-101B readings as a CSV file: seal leak 18 drops/min, vibration 7.1 mm/s, bearing temperature 71 C.

**~30 s.** Produces a real `.csv`. Worth opening: the last column carries the SOP
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
