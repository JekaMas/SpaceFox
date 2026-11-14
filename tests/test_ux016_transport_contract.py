"""Strict recorded HTTP media contract; never simulates or attributes a phone error."""
import json, os
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'openspec/changes/spacefox-watchface/evidence/phone-mime-readability-015'
SOURCE=Path(os.environ.get('SPACEFOX_UX_FEED_SOURCE',str(ROOT/'watchface/source/FeedService.mc')))
MODE=os.environ.get('SPACEFOX_UX_HEADERS','hosted')

class NativeTransportContract(unittest.TestCase):
    def test_ux01_text_plain_response_matches_request(self):
        src=SOURCE.read_text()
        self.assertIn('HTTP_RESPONSE_CONTENT_TYPE_TEXT_PLAIN',src)
        if MODE=='baseline':
            headers=(E/'hosted-before.headers').read_text().splitlines()
            media=next(x.split(':',1)[1].strip().split(';',1)[0].lower() for x in headers if x.lower().startswith('content-type:'))
        else:
            record=json.loads((E/'hosted-text-readback.json').read_text())
            self.assertEqual(record['status'],'passed')
            feed=next(r for r in record['responses'] if r['path']=='feed.json.txt')
            media=next(v.split(';',1)[0].lower() for k,v in feed['headers'] if k.lower()=='content-type')
        self.assertEqual(media,'text/plain',f'recorded HTTP response {media} conflicts with SDK TEXT_PLAIN request')
        self.assertIn('path+".txt"',src)
        self.assertIn('"Accept"=>"text/plain"',src)

if __name__=='__main__':unittest.main()
