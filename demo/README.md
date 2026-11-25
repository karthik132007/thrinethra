The default demonstration uses actual downloaded moving recordings and pretrained detection. Run `make setup` and `make run`; see docs/demo.md.

The optional deterministic trajectory generator is in scenario.py and requires SYNTHETIC_MODE=true. It emits explicit synthetic tracks through the analytics pipeline for regression tests. Generated frames carry a visible no-inference label. These fixtures are not natural-video evaluation.
