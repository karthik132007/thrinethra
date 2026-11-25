import hashlib
import io
import pytest
from scripts import download_assets


def test_download_validates_ranged_asset_bytes_and_checksum(tmp_path,monkeypatch):
    content=b'published real asset bytes'*200
    class Response(io.BytesIO):
        status=206
    calls=[]
    def open_request(request,timeout):
        calls.append(request.headers.get('Range'))
        return Response(content)
    monkeypatch.setattr(download_assets,'ROOT',tmp_path)
    monkeypatch.setattr(download_assets.urllib.request,'urlopen',open_request)
    asset={'id':'test-download','path':'media/test.bin','url':'https://publisher.invalid/asset','bytes':len(content),'range_download':True,'sha256':hashlib.sha256(content).hexdigest()}
    download_assets.download(asset)
    assert (tmp_path/'media/test.bin').read_bytes()==content
    assert calls==[f'bytes=0-{len(content)-1}']
    download_assets.download(asset)
    assert len(calls)==1,'Verified assets must not be fetched again'


def test_corrupt_asset_is_never_promoted_to_verified_file(tmp_path,monkeypatch):
    class Response(io.BytesIO):status=206
    monkeypatch.setattr(download_assets,'ROOT',tmp_path)
    monkeypatch.setattr(download_assets.urllib.request,'urlopen',lambda *args,**kwargs:Response(b'bad'))
    monkeypatch.setattr(download_assets.time,'sleep',lambda _:None)
    asset={'id':'corrupt','path':'bad.bin','url':'https://publisher.invalid/asset','bytes':3,'range_download':True,'sha256':hashlib.sha256(b'yes').hexdigest()}
    with pytest.raises(ValueError,match='Checksum mismatch'):download_assets.download(asset)
    assert not (tmp_path/'bad.bin').exists()
