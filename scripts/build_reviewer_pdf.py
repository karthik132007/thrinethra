"""Build the reviewer handbook with ReportLab (document tooling, not app runtime).

Run with a Python environment containing reportlab. No application state is changed.
"""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    Image, Preformatted, Flowable,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf/TRINETHRA_Reviewer_Handbook.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)
NAVY = colors.HexColor("#14272c")
GOLD = colors.HexColor("#a47a30")
INK = colors.HexColor("#24363b")
MUTED = colors.HexColor("#5a6b71")
PALE = colors.HexColor("#eef3f3")
LINE = colors.HexColor("#d6dfdf")
W, H = A4
CW = W - 96

font_root = Path("/usr/share/fonts/noto")
fallback = Path("/usr/share/fonts/truetype/dejavu")
for name, filename, alt in (
    ("Body", "NotoSans-Regular.ttf", "DejaVuSans.ttf"),
    ("BodyBold", "NotoSans-Bold.ttf", "DejaVuSans-Bold.ttf"),
    ("BodyItalic", "NotoSans-Italic.ttf", "DejaVuSans-Oblique.ttf"),
):
    path = font_root / filename
    if not path.exists():
        path = fallback / alt
    pdfmetrics.registerFont(TTFont(name, str(path)))
mono = Path.home() / ".local/share/fonts/JetBrainsMono-2.304/fonts/ttf/JetBrainsMono-Regular.ttf"
if not mono.exists():
    mono = fallback / "DejaVuSansMono.ttf"
pdfmetrics.registerFont(TTFont("Code", str(mono)))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyBold", italic="BodyItalic", boldItalic="BodyBold")
S = {}
S["body"] = ParagraphStyle("body", fontName="Body", fontSize=9.2, leading=13.6, textColor=INK, spaceAfter=7)
S["small"] = ParagraphStyle("small", parent=S["body"], fontSize=8, leading=11.3, spaceAfter=5)
S["h1"] = ParagraphStyle("h1", fontName="BodyBold", fontSize=21, leading=26, textColor=NAVY, spaceAfter=13)
S["h2"] = ParagraphStyle("h2", fontName="BodyBold", fontSize=11.3, leading=15, textColor=NAVY, spaceBefore=9, spaceAfter=6, keepWithNext=True)
S["label"] = ParagraphStyle("label", fontName="BodyBold", fontSize=8.2, leading=11, textColor=GOLD, spaceAfter=7)
S["cell"] = ParagraphStyle("cell", parent=S["small"], fontSize=8, leading=11.2, spaceAfter=0, splitLongWords=True)
S["th"] = ParagraphStyle("th", parent=S["cell"], fontName="BodyBold", textColor=colors.white)
S["code"] = ParagraphStyle("code", fontName="Code", fontSize=7.35, leading=10.6, textColor=NAVY, backColor=PALE, borderPadding=9, spaceBefore=4, spaceAfter=12)
S["caption"] = ParagraphStyle("caption", parent=S["small"], textColor=MUTED, fontSize=7.6, leading=10.5)
story = []
sections = []


def p(text, style="body"):
    story.append(Paragraph(text, S[style]))


def h(text):
    p(text, "h2")


def code(text):
    for line in text.strip("\n").splitlines():
        if pdfmetrics.stringWidth(line, "Code", S["code"].fontSize) > CW - 22:
            raise ValueError("Code line is too wide: " + line)
    story.append(Preformatted(text.strip("\n"), S["code"]))


def note(title, text):
    cells = [[Paragraph(title, S["label"])], [Paragraph(text, S["small"])]]
    t = Table(cells, colWidths=[CW - 20])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE), ("BOX", (0, 0), (-1, -1), 0.5, LINE), ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.extend([t, Spacer(1, 9)])


def table(headers, rows, widths=None):
    data = [[Paragraph(str(x), S["th"]) for x in headers]]
    data += [[Paragraph(str(x), S["cell"]) for x in row] for row in rows]
    t = Table(data, colWidths=[CW * x for x in widths] if widths else None, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.35, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([t, Spacer(1, 9)])


def start(number, title, subtitle):
    if story:
        story.append(PageBreak())
    sections.append((number, title))
    p(f"REVIEWER HANDBOOK / {number:02d}", "label")
    heading = Paragraph(f'<a name="section-{number}"/>{title}', S["h1"])
    heading.section = (number, title)
    story.append(heading)
    p(subtitle, "small")
    story.append(Spacer(1, 5))


def screenshot(name, width=CW, max_height=390):
    img = Image(str(ROOT / "docs/screenshots" / name))
    scale = min(width / img.imageWidth, max_height / img.imageHeight)
    img.drawWidth, img.drawHeight = img.imageWidth * scale, img.imageHeight * scale
    img.hAlign = "CENTER"
    story.extend([img, Spacer(1, 7)])


class Architecture(Flowable):
    def __init__(self):
        super().__init__()
        self.width, self.height = CW, 205

    def draw(self):
        c = self.canv
        c.scale(1, 205 / 247)
        boxes = [
            (0, 183, CW, 45, "REAL SOURCES", "Local / uploaded video, webcam, opt-in RTSP"),
            (0, 117, 237, 48, "PER-CAMERA WORKERS", "Decoder > frame queue (1) > YOLO + ByteTrack"),
            (263, 117, CW - 263, 48, "TEMPORAL INTELLIGENCE", "ROI features, events, forecast, risk, graph"),
            (0, 49, 237, 49, "LOCAL PERSISTENCE", "SQLite / PostgreSQL; evidence JPEGs + reports"),
            (263, 49, CW - 263, 49, "READ-ONLY INVESTIGATION", "LangGraph + local Qwen / explicit fallback"),
            (0, 0, CW, 31, "FASTAPI / REST + WEBSOCKET > NEXT.JS > HUMAN REVIEW", ""),
        ]
        for x, y, w, hh, title, sub in boxes:
            c.setFillColor(PALE); c.setStrokeColor(LINE)
            c.roundRect(x, y, w, hh, 5, fill=1, stroke=1)
            c.setFillColor(NAVY); c.setFont("BodyBold", 8.3)
            c.drawString(x + 10, y + hh - 16, title)
            if sub:
                c.setFillColor(MUTED); c.setFont("Body", 7.0)
                c.drawString(x + 10, y + 10, sub)
        c.setStrokeColor(GOLD); c.setLineWidth(1.3)
        for x1, y1, x2, y2 in [(118, 183, 118, 165), (237, 141, 263, 141), (118, 117, 118, 98), (381, 117, 381, 98), (118, 49, 118, 31), (381, 49, 381, 31)]:
            c.line(x1, y1, x2, y2)


# 1
start(1, "TRINETHRA", "The Third Eye for Public Safety")
p("Reviewer handbook", "h1")
p("Download, install, run, inspect and reproduce the local research application.")
note("EDITION / 25 NOVEMBER 2026", "Application baseline: <b>9afc1fa</b>, branch <b>codex/trinethra-mvp</b>. This guide documents the local real-video revision. Remote availability of this revision has not been verified; use the matching archive or revision supplied by the author.")
screenshot("real-command-centre.jpg", max_height=338)
p("Actual browser capture of the real-recording workspace. Displayed readings are one historical run, not expected constants or promised outcomes.", "caption")
p("<b>What reviewers can run:</b> pretrained YOLO detection, anonymous local tracking, temporal crowd/road baselines, evidence-backed incidents, aggregate relationships, count forecasts, local language-model investigations and audited operator review.")
p("<b>Status:</b> working local experimental application. Measured detection errors and unverified deployment/hardware paths are documented. No paid API key is required.", "small")

# 2
start(2, "How to use this handbook", "Start with the fresh-install path; return to technical sections when assessing the implementation.")
table(["Review path", "Read / do"], [
    ("First-time reviewer", "Pages 3-6: prepare tools, obtain the right source, install assets, start services and follow the walkthrough."),
    ("Technical evaluator", "Pages 8-12 and 16-18: source provenance, modules, algorithms, reproducible tests, results and storage/security."),
    ("Operator / integrator", "Pages 7 and 13-15: interface guide, environment settings, custom video and API examples."),
    ("Setup failure", "Page 19: symptoms, checks and recovery. Page 20: optional containers. Page 22: quick commands and references."),
], [0.29, 0.71])
toc = [
    (3, "Requirements and tool installation"), (4, "Obtain the source and install"),
    (5, "Local model, startup and shutdown"), (6, "A reviewer walkthrough"),
    (7, "Interface and evidence inspection"), (8, "Videos, weights and permissions"),
    (9, "Architecture and repository map"), (10, "Vision and temporal analytics"),
    (11, "Forecast, risk and event correlation"), (12, "Investigation and human review"),
    (13, "Environment and settings reference"), (14, "Use your own video and ROI"),
    (15, "API and asynchronous jobs"), (16, "Reproduce tests and experiments"),
    (17, "Measured results and performance"), (18, "Storage, authentication and privacy"),
    (19, "Troubleshooting and recovery"), (20, "Optional Docker / PostgreSQL path"),
    (21, "Review checklist and limitations"), (22, "References and command card"),
]
for n, title in toc:
    p(f'<link href="#section-{n}" color="#14272c"><b>{n:02d}</b> / {title}</link>', "small")
note("READ THE SIGNAL LABELS", "<b>video_inference</b> means observations derived from actual model execution. <b>synthetic</b> means an opt-in regression fixture. Risk scores and model hypotheses are interpretations, not measured danger probabilities. A working UI or passing unit test is not real-world accuracy validation.")

# 3
start(3, "Requirements and tools", "Reference commands use Bash on Linux. Run commands from the project root unless a different terminal is specified.")
table(["Item", "Requirement / status"], [
    ("Operating system", "Linux x86_64 CPU execution was exercised. Ubuntu/Debian commands below are installation guidance. Native Windows and macOS application runs were not verified."),
    ("Python", "3.12 recommended; project metadata supports >=3.12 and <3.15. Captured environment: Python 3.12.16."),
    ("Node.js + npm", "Node 24 is the configured CI target; the currently captured local toolchain is Node 26.13.1 / npm 12.2.3. Use the committed package-lock.json with npm ci."),
    ("Required tools", "uv, GNU Make, FFmpeg and Git (Git is optional when using a supplied ZIP). Internet is needed for initial packages, weights and footage."),
    ("Optional tools", "Ollama for local generative reports; Chromium for browser acceptance tests; Docker Compose only for the optional container route."),
    ("Resource planning", "No validated minimum hardware specification. The host exposes 12 logical CPUs and about 14.9 GiB RAM. Four CPU detector workers and Qwen generation can compete for memory/compute."),
], [0.26, 0.74])
h("Linux prerequisite example")
code("""sudo apt-get update
sudo apt-get install -y git make curl ffmpeg libgl1 libglib2.0-0
# Install Node.js from the official download page [R2].
# Install uv using its official instructions [R1].
uv python install 3.12
uv --version
node --version
npm --version
ffmpeg -version""")
p("Official installers are linked on page 22. If uv is not found after installation, reopen the terminal or add its installation directory to PATH. Keep Python in a persistent location; do not install its base interpreter under /tmp.")
h("Windows and macOS")
p("On Windows, WSL2 with Ubuntu is the suggested Linux-compatible route, not a tested support claim. Microsoft documents <font name='Code'>wsl --install</font> in an administrator PowerShell [R4]. Open Ubuntu and perform all project commands there; do not mix Windows and Linux virtual environments. Install and run Ollama inside that same environment for the simplest loopback configuration.")
p("macOS users need matching Python/Node/FFmpeg/Make tools and platform-compatible Torch wheels. The Makefile selects the official CPU wheel index used on Linux; a platform-specific Torch install may be needed. This path was not validated.", "small")

# 4
start(4, "Obtain the source and install", "Use an archive containing the real-video revision. A download of an older default branch can contain the earlier synthetic demonstration.")
h("1 / Obtain and identify the correct package")
p("Extract the archive supplied by the author into a writable directory. Open a terminal in the extracted folder containing Makefile, pyproject.toml and apps/. The repository name is <b>thrinethra</b>; the product name is <b>Trinethra</b>. If using Git, obtain the branch/tag specified by the author and confirm the application revision. The configured origin is linked on page 22; this guide does not assert that local commit 9afc1fa has been published there.")
code("""cd /path/to/extracted/thrinethra
test -f Makefile
test -f configs/assets.json
test -f configs/cameras.real.yaml
# For a Git checkout only:
git log -1 --oneline""")
h("2 / Fresh setup")
code("""# Do this once, in a fresh checkout without an existing .env:
cp .env.example .env
uv python install 3.12
make setup
make migrate""")
p("<b>Expected result:</b> a local .venv, npm dependencies, downloaded/verified footage and weights, extracted MOT annotations, WebM previews and four configured recording sources. SQLite is the default; no database server is required. Existing cameras/history are preserved rather than reset. Do not overwrite an existing .env during an upgrade.")
h("3 / Browser tests are optional for ordinary use")
code("""make browser-install
# If Chromium reports missing Linux libraries:
cd apps/frontend
PLAYWRIGHT_BROWSERS_PATH=../../runtime/browsers \\
  npx playwright install --with-deps chromium
cd ../..""")
p("Browser dependencies may require administrator access. They are needed by automated tests, not by your normal web browser. App startup is on page 5.")
note("DOWNLOAD AND DISK EXPECTATIONS", "Pinned footage, annotations and detector weights total <b>314,735,826 bytes</b> (about 300 MiB), excluding previews and dependencies. Qwen adds about 986 MB. This installed checkout used roughly 1.7 GiB for .venv, 501 MiB for node_modules and 700 MiB for test browsers. These are observed sizes, not minimum storage requirements; reserve additional room for caches, builds and evidence.")

# 5
start(5, "Start the application", "Three local services: Next.js on 3000, FastAPI on 8000 and the project Ollama endpoint on 11435.")
h("Optional local language model - first download")
p("Install Ollama from the official instructions [R3]. The detector, analytics, evidence and human review do not require it. To exercise actual generative reasoning, use two terminals in the project root:")
code("""# Terminal A: keep this running
make llm

# Terminal B: download into the project model store
make llm-model
OLLAMA_HOST=127.0.0.1:11435 ollama list""")
p("Expected model: qwen2.5:1.5b. The recorded download was Q4_K_M, 986,061,892 bytes. Model tags can change upstream; compare the digest in docs/real-video-evaluation.md when reproducing the exact run. The project port is 11435, separate from Ollama's common 11434 default.")
h("Start and confirm")
code("""# Terminal B, after the model pull completes:
make run

# Terminal C: optional health check
curl -fsS http://127.0.0.1:8000/api/v1/health""")
p("Open <link href='http://127.0.0.1:3000' color='#a47a30'>http://127.0.0.1:3000</link>. Expected health fields include status=ok, database=connected, model_available=true and inference_size=960. A camera can separately report starting, online, ended, disabled or error. First detector/model loading takes time; an ended short file is normal.")
h("Without a language model")
p("Set <font name='Code'>LLM_PROVIDER=none</font> in .env before startup. Reports then explicitly use the evidence-only fallback. An unavailable or invalid model response is also labeled; it is never presented as a successful generated answer.")
h("Production frontend and shutdown")
code("""# With previous app processes stopped:
make build
.venv/bin/python scripts/run.py --production""")
p("Press Ctrl+C in the launcher terminal to stop the backend/frontend that it started. Stop Terminal A separately if you started Ollama there; reused model servers are not owned by the launcher. Do not run make run and separate make backend/make frontend commands at the same time. Restart with the same command; use Replay recordings to start new tracking runs.")
note("NETWORK / OFFLINE USE", "After packages, source assets and model blobs are present, the normal local recording workflow needs no paid service or external model API. Keep loopback bindings for the reference review. Initial installation and missing downloads require Internet access.")

# 6
start(6, "A reviewer walkthrough", "Allow approximately 10-15 minutes for inspection after installation; CPU generation and slow hardware can take longer.")
table(["Action", "What to inspect / expected behavior"], [
    ("1. Open Overview", "Confirm the green REAL VIDEO INFERENCE banner and model name. The source graph is a relationship layout, not verified GPS. No SIMULATION banner should appear."),
    ("2. Replay recordings", "Enabled file sources restart with new camera-local tracking state. Deliberately stopped sources remain stopped; use Start on those sources if you want all four."),
    ("3. Open Surveillance", "Frames come from actual recordings. Boxes, anonymous IDs, counts, media progress, compute time, processed frames and dropped frames should update. A busy CPU may skip frames."),
    ("4. Inspect a source", "Open the source recording/metadata panel. Play the browser preview and inspect publisher URL, verified SHA-256 and crop information."),
    ("5. Open Intelligence", "Wait for at least five current observations. Review historical counts, selected baseline, forecast uncertainty and any estimated capacity crossing. The method and values can change with observations."),
    ("6. Open Incidents", "Inspect a measured sustained-threshold event when one occurs. Read factors, onset/update times, provenance and evidence frames. A single crowded frame should not trigger an immediate persistent event."),
    ("7. Investigate", "Ask: 'What measured evidence supports this alert, and what remains uncertain?' Wait for the background job. Inspect citations, missing information, hypotheses and explicit model/fallback mode."),
    ("8. Human review", "Add a note and choose Verify, Dismiss or Resolve as appropriate. Inspect the changed timeline and audit history. These actions store review decisions; they do not dispatch anything."),
], [0.25, 0.75])
h("If no incident appears")
p("Real inference is not scripted to guarantee a particular alert. Check that sources are enabled, playback is running, the ROI contains the objects, and count/capacity thresholds persist. Inspect the configured capacity in Settings/zone editing. For a repeatable mechanics experiment, run make physical-evaluate (page 16); its low three-object threshold is explicitly a test setting.")
h("What is not an acceptance failure")
p("A source ending after 13-35 seconds, an empty road-incident list on ordinary traffic, slightly different counts between machines, or an explicit evidence-only fallback are explainable behaviors. A false synthetic label, invented detections, missing evidence for a factual claim, or a silent source/model failure should be investigated.")

# 7
start(7, "Interface and evidence inspection", "The six connected views read backend data. This historical capture shows actual detections, not a fixed target screen.")
screenshot("real-surveillance.jpg", max_height=300)
p("Surveillance acceptance capture. Full-size original: docs/screenshots/real-surveillance.jpg. Compare activity and timestamps rather than trying to match these counts.", "caption")
table(["View", "Reviewer focus"], [
    ("Overview", "Source health, current aggregate readings, incident summaries and explicitly labeled source relationships."),
    ("Surveillance", "Annotated feeds, source inspection/playback, Start/Stop, upload/add/edit camera, ROI and measured processing counters."),
    ("Incidents", "Search/filter, lifecycle timeline, evidence JPEGs, report generation and human verification/dismissal/resolution."),
    ("Intelligence", "Detector-derived history, chosen forecast method, intervals, zone scores and explained event relationships."),
    ("Investigations", "Stored structured reports, grounded observations, hypothesis labels, reference links and limitations."),
    ("Settings", "Validated intelligence parameters, source/zone configuration, capabilities and audit-related controls."),
], [0.23, 0.77])
p("An ended feed can retain its last frame and count. Use the observed timestamp and source health to distinguish historical readings from current activity. Counts are per source/zone; summing views is not a verified unique-person count.", "small")

# 8
start(8, "Videos, models and permissions", "Assets are downloaded locally, checksum-verified and ignored by Git. configs/assets.json is the source manifest.")
table(["Asset", "Role / observed properties"], [
    ("people-walking.mp4", "Supervision publisher example; 341 frames, 1920 x 1080, 25 FPS, 13.64 s. Default pedestrian source."),
    ("vehicles.mp4", "Supervision publisher example; 538 frames, 3840 x 2160, approximately 25 FPS / 21.52 s. Default road source."),
    ("MOT17-04 raw preview", "Official MOTChallenge night crowd; 1,050 frames, 960 x 540, 30 FPS / 35 s. Two non-overlapping cropped views form the default linked pair."),
    ("MOT17-09 raw preview", "Official MOTChallenge pedestrian sequence; 525 frames, 960 x 540, 30 FPS / 17.5 s. Used in annotated model evaluation."),
    ("EPFL 4p-c0 / 4p-c1", "Two different publisher-synchronized physical cameras; each 3,915 frames, 360 x 288, 25 FPS / 156.6 s. Separate correlation experiment, not default UI cameras."),
    ("MOT17Labels.zip", "Official valid pedestrian annotations for matching/count evaluation. Only the needed sequence labels and seqinfo.ini entries are extracted."),
    ("EPFL calibration", "Publisher calibration reference is retained for provenance. The app does not infer physical density/speed from this file."),
    ("YOLO11n / YOLO11s", "Pretrained Ultralytics weights; approximately 5.6 / 19.3 MB. Nano at input size 960 is the final CPU default; small is available for comparison."),
    ("Qwen2.5 1.5B", "Local Ollama Q4_K_M language model; approximately 986 MB. It interprets structured evidence, not raw footage."),
], [0.29, 0.71])
h("Integrity and provenance")
p("Run <font name='Code'>make assets</font> to verify/retrieve the pinned files and prepare previews. Known asset attribution requires a matching file hash; a renamed or modified upload is not automatically attributed to the publisher. New observations/evidence attach detector model name, hash, device, input size and confidence threshold.")
h("Rights and attribution")
p("The source project is AGPL-3.0-or-later. Third-party footage and weights have separate terms; downloading for this review does not grant redistribution rights. EPFL explicitly permits research use and requires the cited work [R7]. Supervision and MOT assets are used for local research/demo purposes. Retain the source notices in datasets/README.md and do not republish the footage merely because this code is open source.")

# 9
start(9, "Architecture and repository map", "One FastAPI process owns the engine and persistence. Each camera has an independent decoder and detector/tracker worker.")
story.append(Architecture()); story.append(Spacer(1, 12))
p("Bounded queues keep the newest work instead of allowing unbounded lag: one decoded frame and two results per camera. Workers exchange data/status; the main engine writes observations, events and evidence. One failed source is isolated from peers.")
table(["Path", "Responsibility"], [
    ("apps/backend/trinethra/", "FastAPI, settings, SQLAlchemy models, auth, media previews, asset attribution and engine lifecycle."),
    ("apps/frontend/", "Next.js / TypeScript views, HTTP proxy, WebSocket/polling, local production launcher and browser tests."),
    ("packages/vision/ + tracking/", "Decode/sample, YOLO + ByteTrack, normalized trajectories, dwell and motion features."),
    ("packages/intelligence/", "Polygon/temporal crowd and road rules, explainable risk components."),
    ("packages/forecasting/ + correlation/", "Recent-count model selection and connected aggregate event relationships."),
    ("packages/investigation/", "Read-only LangGraph workflow and optional structured local model interpretation."),
    ("configs/ + scripts/", "Pinned asset/source configurations; install, seed, run, download and verification helpers."),
    ("tests/ + evaluations/ + docs/", "Regression/API tests, reproducible real experiments/results, screenshots and technical documentation."),
], [0.39, 0.61])
note("SCALE BOUNDARY", "Do not start multiple Uvicorn workers or backend replicas. Each would own independent inference/live state. SQLite WAL supports this local single-owner design. Synchronous database/JPEG work can delay the main event loop; multi-process inference and distributed coordination are future operational work.")

# 10
start(10, "Vision and temporal analytics", "Real detections feed interpretable rules. The rules are implemented baselines, not trained accident or crowd-danger classifiers.")
h("Detection and anonymous tracking")
p("YOLO11 filters six COCO classes: person, bicycle, car, motorcycle, bus and truck. ByteTrack links detections within a camera worker. Boxes and foot positions are normalized to image coordinates; derived features include velocity, direction, trajectory history, dwell and sudden stopping. IDs are temporary, camera-local and reset on replay. No cross-camera identity matching is performed.")
p("Playback is paced using source frame rate. The detector loads before short-file decoding starts. The default sampling request is 2 FPS, input size 960, CPU execution and two Torch threads; overloaded queues discard stale work. Source sampling rate, measured inference compute rate and end-to-end delivery latency are different quantities.")
h("Zone observations")
p("A normalized polygon selects objects by foot/center position. Crowd mode uses people; road mode uses vehicles. Measurements include count, count/capacity occupancy, recent-five-observation smoothed count, growth, mean image-plane movement, directional conflict and relative spatial concentration. No meters-per-second or people-per-square-meter claim is supported without appropriate calibration.")
table(["Rule family", "Current interpretation"], [
    ("Sustained crowd occupancy", "Smoothed occupancy above the configured fraction of object capacity. Default threshold: 0.8, with temporal persistence."),
    ("Bottleneck / sudden movement", "Bottleneck combines elevated occupancy, low movement and concentration. Sudden movement requires multiple people and high mean image-plane movement."),
    ("Stationary / restricted stop", "Vehicle tracks remain below a movement threshold for a configured duration; zone restriction chooses the event label."),
    ("Traffic congestion", "Vehicle occupancy and sustained low movement combine; normal traffic does not imply an incident."),
    ("Suspected road incident", "Multiple recent trajectory decelerations, sufficient occupancy and low post-change movement. Bounding-box overlap alone is not used to declare an accident."),
], [0.30, 0.70])
h("Lifecycle and evidence")
p("In-memory candidates must persist before activation (default six seconds). Events are deduplicated, can escalate, and resolve after conditions normalize. Closed events have a cooldown (default 30 seconds). Evidence is captured at onset and at most every 15 seconds while active. Replay resolves prior active-run events with a recorded note and clears rolling tracking/analytics windows.")
p("Object capacity is an operator test/configuration value. A threshold crossing proves that the rule fired on measured detections; it does not prove unsafe physical crowd conditions.", "small")

# 11
start(11, "Forecast, risk and correlation", "Every displayed estimate is traceable to recent measurements or explicit heuristic components.")
h("Forecasting measured counts")
p("At least five current observations are required. Up to 60 recent timestamped counts are used. Candidates are rolling linear regression, last observation and exponential smoothing (alpha 0.3). With at least 15 samples, the engine selects the candidate with the lowest recent rolling one-step MAE; shorter windows warm up with regression. Twelve future points cover the configured horizon, initially 60 seconds.")
p("Outputs include chosen method, validation errors, historical trend, forecast points, approximate lower/upper bounds, capacity and possible crossing time. Intervals are residual-based estimates; their coverage is not calibrated for safety. Forecast targets are detector-derived counts, not ground-truth danger. Adaptive selection did not beat last value in every measured case.")
h("Explainable 0-100 score")
table(["Component", "Contribution cap / rule"], [
    ("Occupancy", "Up to 35 points from current object count / configured capacity."),
    ("Temporal persistence", "Up to 15 points from sustained conditions."),
    ("Positive growth", "Up to 10 points from increasing observed occupancy."),
    ("Reduced movement", "10 points when occupancy exceeds 0.5 and mean movement is low."),
    ("Forecast contribution", "Up to 20 points from predicted peak/capacity ratio."),
    ("Connected incidents", "Up to 10 points, five per related incident."),
], [0.33, 0.67])
p("Default severity bands: normal below 25; elevated from 25; high from 50; critical from 75. High/critical thresholds are configurable. The component weights are explicit implementation constants in analytics.py, not learned or validated coefficients. Detector confidence is reported separately from estimated risk severity.")
h("Aggregate event relationships")
p("The graph requires an explicit camera connection, compatible event family, matching provenance and onset times within the default 120-second window. It reports a heuristic confidence and explanation. Directions are compared only when the views share a coordinate reference; unrelated uncalibrated camera orientations are not assumed to align.")
note("TWO DIFFERENT TESTS", "The default MOT pair is two adjacent crops of one recording. The separate EPFL experiment uses two different synchronized physical cameras. Both correlate aggregate events, never individual people. Neither verifies city GPS, causal flow between locations or regional danger accuracy.")

# 12
start(12, "Investigation and human review", "LangGraph assembles a structured evidence context. A local language model can interpret it, but cannot control cameras, enforcement or the database.")
h("What the workflow retrieves")
p("The backend retrieves the incident, retained evidence, camera/zone metadata, related events, recent observations, forecasts, risk components and reference context. Canonical facts come from stored snapshots with evidence references. Missing or expired information is reported rather than replaced with invented measurements.")
h("Local Qwen interpretation")
p("Ollama runs Qwen2.5 1.5B with a structured schema that restricts citations to available evidence. Validated responses answer questions and propose explanations/review steps as explicitly unverified hypotheses. A valid reference ID establishes linkage, not semantic truth or causation.")
table(["Report element", "How to review it"], [
    ("Summary / observations", "Compare each factual claim with stored incident factors and linked evidence, not merely plausible prose."),
    ("Related events / risk factors", "Read the relationship reasons and component contributions. A graph link is a hypothesis, not causation."),
    ("Possible explanations", "Model-generated hypotheses must be visibly labeled; they are not video inference results."),
    ("Missing information / limits", "Look for unresolved location/calibration, detector misses, unavailable evidence and unverified external context."),
    ("Recommended actions", "Human review/general assessment only. No autonomous dispatch, identification, penalty or enforcement."),
    ("References / mode", "Open retained JPEGs and confirm actual model or evidence-only fallback mode. Reference existence is checked programmatically."),
], [0.34, 0.66])
h("Why generation uses jobs")
p("A POST immediately returns a job ID; the browser polls during CPU generation. Maximum four queued/running jobs, serialized generation and 64 retained states; completed states become eligible for cleanup after 30 minutes. Restart invalidates jobs; completed reports persist in the database.")
h("Human verification")
p("Use Under review, Verify, Dismiss or Resolve with an assessment note. Verification records what the operator concluded; it is separate from automatic lifecycle normalization. Review feedback and audit records persist. Do not treat a 'verified' test incident as an independently validated real emergency.")
note("FALLBACK BEHAVIOR", "If the model is disabled, unavailable or returns an invalid response/citation, the retained evidence-only report remains usable and its mode/limitations say so. Core detection and review continue without a paid API key or successful model generation.")

# 13
start(13, "Environment and settings", "Copy .env.example once for a new checkout. Restart the affected service after changing environment variables; never commit secrets.")
table(["Variable", "Default", "Meaning"], [
    ("DEMO_MODE", "true", "Permits loopback no-token access only when OPERATOR_TOKEN is empty; does not enable simulation."),
    ("SYNTHETIC_MODE", "false", "Default real source profile. true enables explicit synthetic fixtures; use an isolated database."),
    ("OPERATOR_TOKEN", "empty", "Shared operator secret. Mandatory with DEMO_MODE=false; a nonempty value also protects demo mode."),
    ("DATABASE_URL", "sqlite:///runtime/trinethra.db", "Local SQLite by default. PostgreSQL: postgresql+psycopg://..."),
    ("RUNTIME_DIR", "runtime", "Media, evidence and model-root context. Does not independently change DATABASE_URL."),
    ("MODEL_PATH", "runtime/models/yolo11n.pt", "Existing local detector weight file; yolo11s.pt is also downloaded."),
    ("DEVICE / TORCH_THREADS", "cpu / 2", "CPU default. DEVICE=0 needs compatible CUDA Torch/hardware; not verified here."),
    ("INFERENCE_SIZE / SAMPLE_FPS", "960 / 2", "Detector input resolution and requested source sampling rate; actual throughput may be lower."),
    ("LLM_PROVIDER", "ollama", "Local generative interpretation. none explicitly selects evidence-only reports."),
    ("LLM_BASE_URL / LLM_MODEL", "127.0.0.1:11435 / qwen2.5:1.5b", "Use the full http:// prefix in LLM_BASE_URL. Match the serving port and installed tag."),
    ("ALLOW_NETWORK_STREAMS", "false", "RTSP is opt-in; local source paths remain confined to the media directory."),
    ("BLUR_EVIDENCE", "true", "Upper-person-box evidence blur; not guaranteed face anonymization."),
    ("EVIDENCE_RETENTION_DAYS / OBSERVATION_RETENTION_DAYS", "7 / 7", "Periodic retention for evidence and observations; not automatic deletion of source video."),
    ("CORS_ORIGINS / COOKIE_SECURE", "loopback:3000 / false", "Exact browser origins. Secure cookies require HTTPS; use false for the local HTTP review."),
], [0.32, 0.27, 0.41])
p("The Settings API/UI validates persistence (2-120 s), occupancy threshold (0.2-2), stationary duration (2-120 s), forecast horizon (10-600 s), high/critical score ordering, cooldown (5-600 s) and detector confidence (0.1-0.95). ROI capacity/polygon and camera kind are separate source/zone configuration.", "small")
p("Changing host/port is advanced: BACKEND_URL controls the frontend server's API target; NEXT_PUBLIC_WS_URL is a build-time browser value; CORS_ORIGINS must match the actual origin. Keep the reference ports unless necessary.", "small")

# 14
start(14, "Use your own video and ROI", "Only process media you are authorized to use. This example is a local, unauthenticated loopback review.")
h("Upload a decodable file")
code("""curl -fsS -X POST \\
  -F 'file=@/path/to/your/video.mp4' \\
  http://127.0.0.1:8000/api/v1/streams/upload""")
p("The response includes a generated source such as media:&lt;generated-name&gt;.mp4. Copy the exact source value into Add camera in Surveillance. Upload limits: 250 MiB; supported extensions are .mp4, .avi, .mov, .mkv and .webm. OpenCV must decode a frame. Invalid or oversized uploads are rejected.")
h("Create a camera through the API")
code('''# Replace the source value with the upload response.
curl -fsS -X POST http://127.0.0.1:8000/api/v1/cameras \\
  -H 'Content-Type: application/json' \\
  -d '{"id":"review-01","name":"Reviewer video",
       "lat":0,"lon":0,"kind":"crowd","enabled":true,
       "source":"media:<generated-name>.mp4"}' ''')
p("A default full-frame zone is created. Coordinates above are placeholders, not verified geography. Choose crowd for pedestrian observations or road for vehicle rules. Camera IDs are unique. Camera reads redact the source; on a metadata-only PUT, an empty source preserves the existing one.")
h("Configure the region of interest")
p("Use the zone editor or GET /api/v1/zones to find its ID. Polygons use 3-30 normalized [x,y] points in [0,1] with nonzero area. Capacity is an object count, not a calibrated physical occupancy limit. Example body for PUT /api/v1/zones/&lt;id&gt;:")
code('''{
  "camera_id": "review-01",
  "name": "Reviewer ROI",
  "capacity": 20,
  "polygon": [[0.1,0.1],[0.9,0.1],[0.9,0.9],[0.1,0.9]],
  "restricted": false
}''')
p("Zone/source edits clear rolling windows so forecasts must warm up again. Start/Stop controls only that source. A completed file plays once; Start begins a fresh tracking run.")
note("OTHER SOURCES", "Local paths must resolve inside runtime/media (or the configured media root). Webcam sources use webcam:0. RTSP requires ALLOW_NETWORK_STREAMS=true and trusted credentials. Physical devices/RTSP and CUDA were not verified on this host. Do not place credentials in names, notes or screenshots.")

# 15
start(15, "API and background jobs", "Base URL: http://127.0.0.1:8000/api/v1. Generated OpenAPI: http://127.0.0.1:8000/docs.")
table(["Operation", "Route / behavior"], [
    ("Health / live state", "GET /health and /snapshot; GET /observations supports camera_id, zone_id, since, limit and offset."),
    ("Sources / topology", "GET/POST /cameras, PUT /cameras/{id}; GET/POST /zones, PUT /zones/{id}; GET/POST /connections."),
    ("Playback / frames", "POST /recordings/replay; POST /streams/{id}/start or /stop; GET /streams/{id}/frame; GET /streams/{id}/video (?original=true for source container)."),
    ("Events / evidence", "GET /events, /incidents, /incidents/{id}, /correlations, /forecasts; GET /evidence/{id}/frame."),
    ("Review / reports", "PATCH /incidents/{id}/review; GET /investigations; POST /investigations/{incident_id}/jobs; GET /investigation-jobs/{job_id}."),
    ("Configuration / audit", "GET/PUT /settings; GET /audit. Synthetic /demo routes are disabled in the normal real profile."),
], [0.28, 0.72])
h("Start a report, then poll its returned ID")
code('''curl -fsS -X POST \\
  http://127.0.0.1:8000/api/v1/investigations/INCIDENT_ID/jobs \\
  -H 'Content-Type: application/json' \\
  -d '{"question":"What evidence supports this alert?"}'

curl -fsS \\
  http://127.0.0.1:8000/api/v1/investigation-jobs/JOB_ID''')
p("Replace INCIDENT_ID with an ID from /incidents and JOB_ID with the POST response ID. HTTP 202 means queued, not complete. Poll until complete or failed; report contains the generated result. A synchronous POST /investigations/{incident_id} remains available for direct clients with a long timeout.")
h("Authentication and response conventions")
p("When a token is configured, add an Authorization: Bearer header to requests or POST the token to /auth/session for an HttpOnly SameSite cookie. The frontend provides the sign-in flow. Use the same hostname throughout; localhost and 127.0.0.1 have different cookie scope.")
p("Timestamps are UTC Unix seconds; boxes/polygons use normalized image coordinates. Historical lists are paginated with bounded limits. Common errors: 401 auth, 404 missing resource, 409 invalid state, 410 expired evidence, 413 upload size, 422 validation, 429 throttling/queue full. Writes are limited to 30 per minute per client/path.")
p("WebSocket /ws/live is outside the /api/v1 prefix. It validates the browser origin and initial auth message, then sends snapshots at 1 Hz. The frontend reconnects and polls HTTP every five seconds when needed.", "small")

# 16
start(16, "Reproduce tests and experiments", "Run from the repository root. Retained JSON reports are recorded results; rerunning creates new outputs and can change timings/IDs.")
code("""make test
make typecheck
make build
make browser-install
make e2e
make real-evaluate
make physical-evaluate""")
table(["Check", "Purpose / boundary"], [
    ("make test", "33 Python tests passed in the recorded revision. Tests cover API/auth/source confinement, ingestion/EOF, analytics, forecasting, graph coordinate handling, assets and report grounding. Generated edge cases are explicitly regression fixtures."),
    ("typecheck / build", "TypeScript and Next.js production compilation passed. They do not measure detector or safety accuracy."),
    ("make e2e", "Three actual-recording browser tests passed. Dedicated ports 3001/8001, .next-e2e and SQLite store preserve the normal app's cameras. Covers source playback, citations, review and mobile width."),
    ("make real-evaluate", "Two detector models on four moving clips at size 640; 358 sampled frames across models. Produces real-video-results.json and frame overlays under runtime/."),
    ("make physical-evaluate", "Two actual synchronized EPFL cameras, 327 inferred samples per view, isolated database. Explicit three-object mechanics threshold, not a danger benchmark."),
], [0.28, 0.72])
h("Higher-resolution annotated comparison")
code(""".venv/bin/python evaluations/real_video.py \\
  --models yolo11n.pt --assets mot04 mot09 --size 960 \\
  --output real-video-nano-960-results.json
.venv/bin/python evaluations/real_video.py \\
  --models yolo11s.pt --assets mot04 mot09 --size 960 \\
  --output real-video-960-results.json""")
h("Full HTTP + actual local-model check")
p("scripts/verify_real_system.py requires all four default sources enabled, enough current observations, a measured incident and working local Qwen. It creates a report and verifies/resolves a test incident; it changes review state. Run it only on a disposable review instance. Extra cameras, stopped sources or auth configuration can violate its assumptions. It accepts --url for an isolated API instance.")
code(""".venv/bin/python scripts/verify_real_system.py \\
  --url http://127.0.0.1:8000/api/v1""")
p("CI installs real assets and runs tests/evaluation/build/browser checks. CI sets LLM_PROVIDER=none, so its browser run verifies fallback behavior rather than Qwen generation. A configured workflow is not evidence that remote CI has run. Synthetic suites are opt-in and never natural-video accuracy evidence.", "small")

# 17
start(17, "Measured results and performance", "Recorded on the local CPU development host, 25 November 2026. Results are development diagnostics, not official MOTChallenge scores.")
table(["Sequence / model", "Precision", "Recall", "Count MAE", "Mean ms"], [
    ("MOT04 / nano 640", "0.9008", "0.2152", "34.414", "41.881"),
    ("MOT04 / small 640", "0.8696", "0.1918", "35.243", "122.349"),
    ("MOT04 / nano 960", "0.8734", "0.3662", "26.257", "98.518"),
    ("MOT04 / small 960", "0.8955", "0.3384", "28.129", "199.010"),
    ("MOT09 / nano 640", "0.7963", "0.4886", "4.000", "41.001"),
    ("MOT09 / small 640", "0.8102", "0.4972", "4.000", "104.432"),
    ("MOT09 / nano 960", "0.8341", "0.4858", "4.257", "95.362"),
    ("MOT09 / small 960", "0.7200", "0.5114", "3.029", "177.788"),
], [0.36, 0.16, 0.14, 0.18, 0.16])
p("Ground truth: valid pedestrian records, all visibility levels. IoU matching threshold 0.5; boxes are normalized from original 1920 x 1080 annotations to 960 x 540 previews. Ignore/distractor suppression is not implemented. These are matched sampled-box precision/recall, not mAP, HOTA, MOTA or IDF1. Counting error compares tracked detections with annotated people.", "small")
note("SUBSTANTIAL MISSES", "Nano/960 night-crowd recall was only <b>0.3662</b>. Small/occluded people are frequently missed. Nano/960 was selected for its measured night-crowd count/CPU tradeoff; a larger model was not uniformly better. These results do not establish reliable crowd safety monitoring.")
h("Other recorded checks")
p("<b>Forecast examples:</b> nano/960 MOT04 adaptive MAE 2.398 versus last-value 2.362; MOT09 1.542 versus 1.652. Small/960: MOT04 2.102 versus 2.138; MOT09 1.198 versus 1.478. Targets are future detected counts; adaptive selection is not always superior.")
p("<b>Physical EPFL experiment:</b> 327 samples per view; four incidents, three relationships, eleven evidence snapshots; mean isolated inference 77.689 ms; offline processing 61.905 s. These are recording-time mechanics results, not wall-clock alert latency or correlation accuracy against labeled relationships.")
p("<b>Initial full system:</b> four concurrent small/960 sources averaged roughly 0.85-1.15 s compute per source, much slower than isolated measurements. Local Qwen completed a cited report in 22.944 s. Final nano/960 browser run: three tests in 61.96 s. Python suite: 33 tests in 50.16 s.")
p("Host context: AMD Ryzen 5 5500U, 12 logical CPUs, about 14.9 GiB RAM visible; CPU execution only. Health exposes current process memory/CPU and camera processing/drop counters. No calibrated end-to-end emergency latency, GPU throughput or minimum hardware guarantee is established. Detailed raw results: evaluations/*.json and docs/real-video-evaluation.md.", "small")

# 18
start(18, "Storage, authentication and privacy", "Local data remains on the review machine. Database configuration is never an authoritative source of authentication secrets.")
table(["Location / record", "Stored content / retention"], [
    ("runtime/trinethra.db", "Default SQLite state: sources, zones, observations, events, incidents, graph links, risks, forecasts, evidence metadata, reports, feedback and audit."),
    ("runtime/media/", "Downloaded/uploaded source video and cached browser previews. Input media is not automatically deleted by evidence retention."),
    ("runtime/evidence/", "Retained JPEG evidence. Default seven-day evidence retention; sweep about every five minutes."),
    ("runtime/models/", "YOLO weights and project-local Ollama blobs. Large assets, secrets and caches are excluded from Git."),
    ("Historical observations", "Default seven-day observation retention; expired observation pointers may be cleared while retained evidence snapshots survive."),
    ("Incidents / reports / audit", "Persistent summaries, report text, feedback and audit do not yet have an automatic deletion policy. Old reports can cite evidence that later expires."),
], [0.33, 0.67])
h("Authentication")
p("The local reference mode permits access without a token only when DEMO_MODE=true and OPERATOR_TOKEN is empty. Otherwise a shared token is checked; non-demo startup requires one. Sessions use an HttpOnly SameSite=Strict cookie, with COOKIE_SECURE enabled only behind HTTPS. No named-user roles or per-user attribution is implemented. Keep .env and runtime data access restricted.")
h("Privacy and agent boundaries")
p("No face recognition, biometrics, protected-attribute inference, persistent identity, person re-identification, individual threat scores or autonomous enforcement exists. IDs are short-lived and camera-local. Evidence blur covers the upper 35% of detected person boxes; missed people may remain visible. Original footage and live annotated frames remain operator-visible. This is not guaranteed anonymization.")
p("The agent has read-only structured context, no shell tool, no unrestricted filesystem reader and no database mutation tool. Questions, names and reference text are untrusted. A model response cannot gain execution authority. If an external compatible provider is deliberately configured, selected evidence factors/question text may leave the host; the default Qwen provider is local.")
h("Backup and clean reviews")
p("Stop the application before copying the SQLite database, evidence and .env to a protected backup. Back up media if replay is needed; preserve models to avoid redownloads. Use a separate extracted checkout/database for destructive tests. Do not delete runtime to 'reset' a review: it contains expensive downloads, evidence and operator history. Replay resets run state without erasing historical records.")

# 19
start(19, "Troubleshooting and recovery", "Start with health, process output and the exact failing command. Do not silently replace a missing detector or source with simulation.")
table(["Symptom", "Check / recovery"], [
    ("make / uv / ffmpeg not found", "Install prerequisites and reopen the shell. Verify versions on page 3. Run from the folder containing Makefile."),
    ("Port already in use", "Only one normal app instance should own 3000/8000; tests use 3001/8001. Stop the earlier project terminal rather than indiscriminately killing other applications. Ollama uses 11435."),
    ("Missing .venv/bin/python", "A dangling link can point to an interpreter removed from /tmp. Recreate it with persistent uv Python using the commands below, then reinstall complete vision dependencies."),
    ("Download/hash/range failure", "Retry make assets with Internet access. Check the publisher URL and disk space. The downloader verifies hashes and retries bounded requests; do not bypass a mismatch or substitute arbitrary files under a known publisher name."),
    ("Torch / OpenCV / model error", "Use make setup, not only the base API dependency install. Ensure CPU Torch, the vision extra, libGL libraries and runtime/models/yolo11n.pt exist. Inspect camera detail."),
    ("Blank frame or ended file", "Wait for model initialization; click Start/Replay. Short files play once. A retained last image is historical. Check that deliberately disabled sources are started."),
    ("No incidents / empty forecast", "Wait for persistence and at least five current observations; inspect ROI, capacity and source kind. Normal traffic need not create an anomaly. No scheduled incident is fabricated."),
    ("Video plays in OpenCV only", "Run make assets to prepare WebM previews; FFmpeg is required. Original containers/codecs may be unsupported by the browser. The API offers ?original=true for the original file."),
    ("401 / source 422 / evidence 410", "Sign in with the configured token; keep hostname consistent. Use media-root sources and valid polygons. 410 means retained evidence expired or is unavailable."),
    ("LLM fallback / long generation", "Check port 11435, ollama list under that host, model tag and LLM settings. CPU responses can take tens of seconds. Restarted backend jobs must be rerun; do not mistake queued for complete."),
    ("SQLite locked / duplicate workers", "Stop duplicate backend instances. Do not use --workers or multiple replicas. Keep one state/persistence owner."),
], [0.28, 0.72])
h("Persistent Python environment repair")
code("""# Stop the app first; ensure UV_PYTHON_INSTALL_DIR is persistent.
uv python install 3.12
uv venv --python 3.12 --clear .venv
uv pip install --python .venv/bin/python torch torchvision \\
  --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv/bin/python -c requirements.lock \\
  -e '.[vision,test,postgres]'""")

# 20
start(20, "Optional Docker and PostgreSQL", "Advanced alternative. Compose configuration was validated; container builds and PostgreSQL runtime were not exercised because the development daemon was unavailable.")
h("Prepare assets before starting containers")
p("The stack mounts runtime/ but does not download every video/model automatically at container startup. Prepare the host assets using the local setup first, or supply the exact verified runtime asset set. Keep local app processes stopped so ports 3000/8000 are free.")
code("""# After preparing host dependencies and runtime assets:
make assets
# In .env, add a strong local POSTGRES_PASSWORD.
# Set OPERATOR_TOKEN for authenticated review.
docker compose config --quiet
docker compose up --build""")
p("The stack defines PostgreSQL 17, FastAPI, Next.js and local Ollama. Published application ports bind to host loopback; the database uses a named volume. Backend API uses the internal PostgreSQL DSN and http://ollama:11434. This internal model port differs from the host project server on 11435.")
h("Populate the container model store")
code("""# In another terminal after Ollama is ready:
docker compose exec ollama ollama pull qwen2.5:1.5b
docker compose logs -f backend
# Stop logs with Ctrl+C; the container keeps running.
docker compose down""")
p("The Ollama service mounts runtime/models/ollama, so an appropriately populated host model store can be reused. First pull still requires Internet when blobs are absent. docker compose down stops/removes containers but preserves named data volumes unless explicitly requested otherwise.")
h("Database migration")
p("SQLAlchemy creates missing tables at local startup; Alembic records schema versions. Use make migrate on a new local checkout. Future changes need new immutable migrations; create_all does not modify existing columns. For container migrations, use the configured backend container and Alembic. Only stamp an unversioned existing schema after verifying it matches the initial migration.")
code("""docker compose exec backend \\
  alembic -c infrastructure/alembic.ini upgrade head""")
h("Support boundary")
p("A successful docker compose config check proves configuration interpolation/schema validity, not image build success, running inference, PostgreSQL data correctness or end-to-end connectivity. Record those separately if you exercise this route. The local Python/Node path is the primary verified review workflow.")
note("BEFORE ANY NETWORK DEPLOYMENT", "This guide describes local review, not Internet deployment. TLS, named users/roles, decoder isolation, network egress controls, distributed state/rate limiting, backup operations and independent security review remain additional work. Do not increase backend replicas to scale the current engine.")

# 21
start(21, "Review checklist and limitations", "Use observable artifacts when evaluating completion. Distinguish implemented mechanisms from real-world scientific validation.")
table(["Reviewer acceptance item", "Evidence to record"], [
    ("Correct revision / setup", "Matching source archive; Makefile/config files present; make setup and migrations complete; exact environment/version notes."),
    ("Real input and inference", "Simulation disabled; moving source preview; model/hash metadata; changing actual detections, count/motion observations and processed-frame counters."),
    ("Persistence and evidence", "Incident provenance=video_inference; real factors/times; stored evidence reference opens a retained JPEG; history survives restart."),
    ("Temporal analytics", "Sustained threshold, dedupe/cooldown, normalization/replay behavior; road rules tested without labeling ordinary traffic an accident."),
    ("Forecast / event graph", "Measured history, displayed chosen method/errors, explicit crop relationship; independent EPFL mechanics run and explanation."),
    ("Agent and review", "Actual Qwen mode or honest fallback; references exist; hypotheses separate from facts; operator review note/timeline stored."),
    ("Checks / limitations", "Unit/type/build/browser outputs, reproducible real result JSON, environment notes and acknowledged failures/missed detections."),
], [0.34, 0.66])
h("Completed mechanisms")
p("Local real-video ingestion/detection/tracking, measured crowd/road features, temporal event lifecycle, persisted evidence, aggregate relationships, count forecasting, explainable heuristic scoring, grounded local investigation/fallback, connected frontend and human review are implemented and exercised within the documented scope.")
h("Partially validated or externally blocked")
p("Dense/night crowd counting is inaccurate; sparse tracking can switch IDs. No labeled real collision dataset evaluation, accident precision/recall, verified false-alert rate, calibrated safety prediction interval, emergency lead time or regional correlation accuracy is established. Webcam/RTSP credentials, CUDA hardware and Docker daemon were unavailable. PostgreSQL configuration/migration SQL checks are not runtime tests.")
h("Operational work still required")
p("Named operators/roles, Internet hardening, isolated media decoders, large-camera-count profiling, process/distributed coordination, stronger annotated validation and comprehensive deletion/backup policies remain future work. Physical density, real-world speed and verified GPS are not inferred. No biometric identification, person matching across cameras, individual threat scoring or autonomous enforcement is implemented.")
note("REVIEWER REPORTING", "Record the command, source/model hash, current configuration, hardware, observed output and failure details. Do not convert passing mechanics tests into a claim of reliable public-safety performance. The most useful review distinguishes software correctness, detector accuracy and operational readiness.")

# 22
start(22, "References and command card", "Repository paths are relative to the extracted project root. External installation links were checked while preparing this edition.")
refs = [
    ("R1 / uv installation", "https://docs.astral.sh/uv/getting-started/installation/"),
    ("R2 / Node.js downloads", "https://nodejs.org/en/download"),
    ("R3 / Ollama Linux installation", "https://docs.ollama.com/linux"),
    ("R4 / Microsoft WSL installation", "https://learn.microsoft.com/en-us/windows/wsl/install"),
    ("R5 / Supervision assets", "https://supervision.roboflow.com/latest/assets/"),
    ("R6 / MOTChallenge MOT17", "https://motchallenge.net/data/MOT17/"),
    ("R7 / EPFL multi-camera data", "https://www.epfl.ch/labs/cvlab/data/data-pom-index-php/"),
    ("R8 / Configured repository origin", "https://github.com/karthik132007/thrinethra"),
]
for title, url in refs:
    p(f'<b>{title}</b><br/><link href="{url}" color="#a47a30">{url}</link>', "small")
p("EPFL citation: F. Fleuret, J. Berclaz, R. Lengagne and P. Fua, 'Multi-Camera People Tracking with a Probabilistic Occupancy Map,' IEEE TPAMI 30(2):267-282, 2008. DOI: <link href='https://doi.org/10.1109/TPAMI.2007.1174' color='#a47a30'>10.1109/TPAMI.2007.1174</link>.", "small")
h("Repository evidence map")
p("<b>Setup:</b> README.md, docs/installation.md, Makefile, .env.example, requirements.lock and apps/frontend/package-lock.json.<br/><b>Implementation:</b> docs/architecture.md, docs/api.md, docs/database.md, apps/, packages/ and configs/.<br/><b>Measured evidence:</b> docs/real-video-evaluation.md, evaluations/real-*.json, evaluations/physical-camera-results.json, evaluations/playwright-results.json and docs/screenshots/real-*.jpg.<br/><b>Boundaries:</b> PROGRESS.md, docs/privacy.md, docs/models.md, datasets/README.md and docs/troubleshooting.md.", "small")
h("Commands to keep nearby")
code("""# Fresh checkout, after prerequisite installation:
cp .env.example .env
make setup
make migrate
# Optional local model: make llm, then make llm-model in terminal B.
make run
# Open http://127.0.0.1:3000; Replay recordings.

# Checks and experiments:
make test typecheck build
make browser-install
make e2e
make real-evaluate physical-evaluate""")
p("PDF regeneration: scripts/build_reviewer_pdf.py with ReportLab and Noto Sans / suitable TrueType fonts in a document-tooling environment. It writes output/pdf/TRINETHRA_Reviewer_Handbook.pdf without modifying application data. This edition describes app commit 9afc1fa; later revisions should recheck commands, results and limits. Fonts are embedded in this PDF; readers need no extra fonts.", "caption")


class Handbook(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, "section"):
            number, title = flowable.section
            self.canv.bookmarkPage(f"section-{number}")
            self.canv.addOutlineEntry(f"{number:02d} {title}", f"section-{number}", level=0)
            if self.page != number:
                raise ValueError(f"Section {number} overflowed to page {self.page}: {title}")


def furniture(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, H - 40, W, 40, fill=1, stroke=0)
    canvas.setFont("BodyBold", 8.5); canvas.setFillColor(colors.white)
    canvas.drawString(48, H - 25, "TRINETHRA  /  REVIEWER HANDBOOK")
    canvas.setFont("Body", 7.5)
    canvas.drawRightString(W - 48, H - 25, "LOCAL REAL-VIDEO EDITION")
    canvas.setStrokeColor(LINE); canvas.setLineWidth(0.5)
    canvas.line(48, 38, W - 48, 38)
    canvas.setFillColor(MUTED); canvas.setFont("Body", 7)
    canvas.drawString(48, 24, "25 NOV 2026  /  APPLICATION 9afc1fa  /  EXPERIMENTAL RESEARCH")
    canvas.setFont("BodyBold", 8)
    canvas.drawRightString(W - 48, 24, f"{doc.page:02d}")
    canvas.restoreState()


doc = Handbook(str(OUT), pagesize=A4, rightMargin=48, leftMargin=48, topMargin=61, bottomMargin=49,
               title="TRINETHRA - Reviewer Handbook", author="Trinethra Project", subject="Installation, review workflow, architecture, reproducible evaluation and limitations", pageCompression=1)
doc.build(story, onFirstPage=furniture, onLaterPages=furniture)
print(OUT)
