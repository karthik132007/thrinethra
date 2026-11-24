"""Measure synthetic condition onset, event creation and live WebSocket delivery separately."""
import asyncio
import json
import time
from pathlib import Path
import httpx
import websockets
ROOT=Path(__file__).resolve().parents[1]

async def main():
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8000/api/v1',timeout=15) as client:
        (await client.post('/demo/reset',json={})).raise_for_status()
        (await client.post('/demo/control',json={'speed':5,'paused':False})).raise_for_status()
        onset={};ticks=[]
        async with websockets.connect('ws://127.0.0.1:8000/ws/live',origin='http://127.0.0.1:3000') as ws:
            await ws.send(json.dumps({'token':''}))
            deadline=time.monotonic()+45
            while time.monotonic()<deadline:
                message=json.loads(await asyncio.wait_for(ws.recv(),timeout=5));snapshot=message['data'];ticks.append(snapshot['health']['tick_ms'])
                for latest in snapshot['latest']:
                    if latest['metrics']['smoothed_count']>=32 and latest['camera_id'] in ('cam-01','cam-02'):
                        onset.setdefault(latest['camera_id'],latest['timestamp'])
                candidates=[i for i in snapshot['incidents'] if i['event']['type']=='potential_crowd_safety_risk']
                if candidates:
                    incident=min(candidates,key=lambda i:i['event']['started_at']);event=incident['event']
                    delivery=(time.time()-event['started_at'])*1000
                    detail=(await client.get('/incidents/'+incident['id'])).json()
                    evidence=detail['evidence'][0]
                    health=(await client.get('/health')).json()
                    result={'provenance':'synthetic scenario (four camera feeds), not video inference',
                            'threshold_to_event_seconds':round(event['started_at']-onset[event['camera_id']],3),
                            'event_creation_to_websocket_delivery_ms':round(delivery,2),
                            'evidence_capture_to_event_ms':evidence['data']['event_latency_ms'],
                            'mean_engine_tick_ms':round(sum(ticks)/len(ticks),2),'max_engine_tick_ms':round(max(ticks),2),
                            'samples':len(ticks),'backend_rss_mb':health['memory_mb'],'process_cpu_percent_since_last_health_call':health['process_cpu_percent'],
                            'system_cpu_percent':health['system_cpu_percent'],'gpu':'Not used or measured',
                            'note':'Condition-to-event delay includes real temporal persistence. Delivery measures WebSocket receipt, not browser paint.'}
                    (ROOT/'evaluations/demo-performance.json').write_text(json.dumps(result,indent=2)+'\n')
                    print(json.dumps(result,indent=2));break
            else:raise RuntimeError('No synthetic crowd incident within timeout')
        (await client.post('/demo/control',json={'paused':True})).raise_for_status()
if __name__=='__main__':asyncio.run(main())
