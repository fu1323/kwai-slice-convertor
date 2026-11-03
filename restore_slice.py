#!/usr/bin/env python3
"""Restore the observed Kuaishou .slice framing to FLV without transcoding."""
import argparse
from pathlib import Path
from collections import Counter

def restore(source):
    b=source.read_bytes();p=0;out=bytearray();count=0;extensions=Counter()
    while p<len(b):
        if len(b)-p<15:raise ValueError(f'Truncated header at {p}')
        n=int.from_bytes(b[p:p+2],'big')>>4
        if n<15 or p+n>len(b):raise ValueError(f'Invalid block length at {p}: {n}')
        payload=b[p+15:p+n]
        if b[p+14]&1:
            if len(payload)<2:raise ValueError('Missing extension length')
            length=int.from_bytes(payload[:2],'big')
            if length<2 or length>len(payload):raise ValueError('Invalid extension length')
            extensions[length]+=1;payload=payload[length:]
        if payload.startswith(b'FLV\x01') and out:
            if len(payload)<13 or payload[5:9]!=b'\x00\x00\x00\x09':raise ValueError('Unexpected FLV header')
            payload=payload[13:]
        out.extend(payload);p+=n;count+=1
    if out[:3]!=b'FLV':raise ValueError('No FLV header')
    pos=int.from_bytes(out[5:9],'big')+4;tags=0
    while pos<len(out):
        if pos+15>len(out):raise ValueError('Truncated FLV tag')
        size=int.from_bytes(out[pos+1:pos+4],'big');end=pos+11+size
        if out[pos] not in (8,9,18) or end+4>len(out) or int.from_bytes(out[end:end+4],'big')!=11+size:
            raise ValueError(f'FLV tag validation failed at {pos}')
        pos=end+4;tags+=1
    return out,{'blocks':count,'tags':tags,'extensions':dict(extensions)}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    data,stats=restore(a.input)
    with a.output.open('xb') as f:f.write(data)
    print(stats)
