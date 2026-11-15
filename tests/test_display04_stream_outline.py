"""Compare the bounded in-place contour recurrence with a two-row oracle."""
import hashlib
import json
from pathlib import Path
import unittest
from tests.test_sfr1m_offline_current import literal_decode

ROOT=Path(__file__).resolve().parents[1]
ARTIFACT=ROOT/'openspec/changes/spacefox-watchface/evidence/site-flag-visual-batch/native-artifact'


def oracle(rows):
    result=[]
    for y,row in enumerate(rows):
        for x,pixel in enumerate(row):
            neighbors=[row[x-1] if x else pixel]
            if y:neighbors.append(rows[y-1][x])
            if max(abs(pixel[c]-other[c]) for other in neighbors for c in range(3))>8:
                result.append((x,y))
    return result


def in_place(rows):
    previous=[(0,0,0)]*len(rows[0]);result=[]
    for y,row in enumerate(rows):
        left=None
        for x,pixel in enumerate(row):
            if left is None:left=pixel
            change=max(abs(pixel[c]-left[c]) for c in range(3))
            if y:change=max(change,max(abs(pixel[c]-previous[x][c]) for c in range(3)))
            if change>8:result.append((x,y))
            previous[x]=pixel;left=pixel
    return result


class StreamOutlineTest(unittest.TestCase):
    def test_real_shards_match_two_row_contour_and_pixel_digest(self):
        feed=json.loads((ARTIFACT/'feed.json').read_text());scene=json.loads((ARTIFACT/feed['visualSelection']['path']).read_text())
        desc=json.loads((ARTIFACT/scene['roles']['map']['descriptor']['path']).read_text());chunks=[(ARTIFACT/r['path']).read_bytes() for r in desc['shards']]
        pixels=literal_decode(chunks,390,390,3);self.assertEqual(hashlib.sha256(pixels).hexdigest(),desc['pixelSha256'])
        rows=[[tuple(pixels[(y*390+x)*3:(y*390+x)*3+3]) for x in range(390)] for y in range(390)]
        expected=oracle(rows);actual=in_place(rows);self.assertEqual(actual,expected)
        # Each real shard boundary compares against the prior global row,
        # even though its compressed first row begins from an empty row.
        starts=[int(chunk.split(b':',3)[1]) for chunk in chunks][1:]
        self.assertTrue(starts)
        for start in starts:
            self.assertEqual([p for p in actual if p[1]==start], [p for p in expected if p[1]==start])

    def test_threshold_and_first_pixel(self):
        rows=[[(10,10,10),(18,10,10),(27,10,10)],[(19,10,10),(18,19,10),(27,10,10)]]
        self.assertEqual(in_place(rows),oracle(rows));self.assertEqual(oracle(rows),[(2,0),(0,1),(1,1),(2,1)])
