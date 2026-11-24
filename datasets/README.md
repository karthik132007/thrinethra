# Data policy

No surveillance footage, private camera feeds or model weights are distributed. Supply local videos only when you have permission to process them. Keep downloaded/user media under ignored runtime/media; weights under runtime/models.

Optional real-inference smoke fixture: download the public upstream Ultralytics test photograph from https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/assets/bus.jpg to runtime/media/bus.jpg, then run `.venv/bin/python scripts/vision_smoke.py`. The repository is upstream AGPL-3.0; consult the asset's original permissions before redistribution. This project does not redistribute the image. The script makes an MJPEG video from the repeated photograph; it is real image detection but has no natural motion and no evaluation annotations.

Synthetic trajectories: demo/scenario.py. Seeded benchmark: evaluations/run.py, seed 42. These contain no real identities and are labeled synthetic in every generated signal. Detector bypass in synthetic benchmarks is explicit; no counting/detection accuracy is inferred from those benchmarks.
