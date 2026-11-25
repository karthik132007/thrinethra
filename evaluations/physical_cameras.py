"""Real independent-camera aggregate correlation test on synchronized EPFL recordings.

Runs offline against an isolated SQLite store. All detections are fresh YOLO inference.
Recording timestamps, not synthetic tracks, drive the unchanged application engine.
"""
import os
import sys
import time
import json
from pathlib import Path
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT);sys.path[:0]=[str(ROOT),str(ROOT/'apps/backend')]
os.environ['DATABASE_URL']=f'sqlite:///{ROOT}/runtime/epfl-evaluation-{uuid4().hex}.db'
os.environ['SYNTHETIC_MODE']='false';os.environ['LLM_PROVIDER']='none';os.environ['TORCH_THREADS']='2'
import cv2
from sqlalchemy import select
from trinethra.db import Base,engine as database,Session,Camera,Zone,Connection,Event,Incident,Evidence,Correlation,serialize
from trinethra.engine import Engine
from packages.vision.detector import Detector

def main():
    manifest=json.loads((ROOT/'configs/assets.json').read_text())
    assets=[next(a for a in manifest['assets'] if a['id']==f'epfl-c{i}') for i in (0,1)]
    Base.metadata.create_all(database);core=Engine();cameras=[];zones=[]
    with Session.begin() as db:
        for index,asset in enumerate(assets):
            id=f'epfl-c{index}';camera=Camera(id=id,name=f'EPFL laboratory · physical camera {index}',source=str(ROOT/asset['path']),lat=0,lon=index*.001,kind='crowd')
            db.add(camera);db.flush()
            # A deliberately low, explicit object-capacity fixture exercises event correlation.
            # Four people in a lab is not evidence of an actual public-safety emergency.
            zone=Zone(id=f'epfl-zone-{index}',camera_id=id,name=f'EPFL view {index} · test threshold',capacity=3,polygon=[[0,0],[1,0],[1,1],[0,1]])
            db.add(zone);db.flush();cameras.append(serialize(camera));zones.append(serialize(zone))
        db.add(Connection(camera_a='epfl-c0',camera_b='epfl-c1'))
    captures=[cv2.VideoCapture(str(ROOT/a['path'])) for a in assets]
    fps=captures[0].get(cv2.CAP_PROP_FPS);total=int(captures[0].get(cv2.CAP_PROP_FRAME_COUNT));assert fps>0
    models=[Detector(ROOT/'runtime/models/yolo11n.pt',size=640) for _ in assets]
    epoch=time.time()-total/fps-30;observations=[[],[]];latencies=[];started=time.perf_counter()
    for index in range(total):
        decoded=[cap.read() for cap in captures]
        if not all(ok for ok,_ in decoded):break
        if index%round(fps/2):continue
        media_time=index/fps
        for j,(_,frame) in enumerate(decoded):
            tracks,latency=models[j].process(frame,epoch+media_time);latencies.append(latency)
            core.process(cameras[j],zones[j],tracks,epoch+media_time,'video_inference',latency,frame,media_time,0,core.configuration())
            observations[j].append({'frame':index+1,'media_time':round(media_time,3),'detected_people':sum(t['class']=='person' for t in tracks)})
        if len(observations[0])%50==0:print(f'{len(observations[0])} samples per camera',flush=True)
    for capture in captures:capture.release()
    with Session() as db:
        incidents=[serialize(i)|{'event':serialize(e)} for i,e in db.execute(select(Incident,Event).join(Event))]
        relations=[serialize(c) for c in db.scalars(select(Correlation))]
        evidence=[serialize(e) for e in db.scalars(select(Evidence))]
    assert incidents and evidence,'No real measured threshold event produced'
    assert relations,'No aggregate event correlation found across actual synchronized camera views'
    assert all(i['event']['provenance']=='video_inference' for i in incidents)
    data={'data':'Two different publisher-synchronized physical EPFL laboratory camera recordings; no synthetic tracks',
          'publisher':'https://www.epfl.ch/labs/cvlab/data/data-pom-index-php/',
          'citation':'Fleuret et al., Multi-Camera People Tracking with a Probabilistic Occupancy Map, TPAMI 2008, DOI 10.1109/TPAMI.2007.1174',
          'camera_source_hashes':{a['id']:a['sha256'] for a in assets},'frames_per_video':total,'fps':fps,
          'object_capacity_test_threshold':3,'threshold_note':'Low test threshold to exercise mechanics, not a validated room capacity or evidence of danger.',
          'observations':{a['id']:observations[j] for j,a in enumerate(assets)},'incidents':incidents,'correlations':relations,
          'evidence_snapshots':len(evidence),'mean_inference_ms':round(sum(latencies)/len(latencies),3),'wall_seconds':round(time.perf_counter()-started,3),
          'limitations':['Offline recording-time processing, not real-time wall-clock latency.','No identities matched across cameras.','Calibration downloaded for provenance but no physical density/speed inferred.','This test establishes event-graph integration, not regional risk accuracy.']}
    (ROOT/'evaluations/physical-camera-results.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({k:v for k,v in data.items() if k not in ('observations','incidents','correlations')},indent=2))
    print(f'{len(incidents)} measured incidents; {len(relations)} aggregate relationships; {len(evidence)} evidence snapshots',flush=True)
if __name__=='__main__':main()
