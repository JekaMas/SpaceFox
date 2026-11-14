"""Check SDK 100% icon and value pixels against the circular screen."""
import os
from pathlib import Path
import unittest
from PIL import Image
E=Path(__file__).resolve().parents[1]/'openspec/changes/spacefox-watchface/evidence/ux02'

class BatteryGrid(unittest.TestCase):
    def test_each_battery_slot_fits_circle_and_keeps_icon_gap(self):
        files=['ux02-battery-slot1-100.png','ux02-battery-slot2-100.png',os.environ.get('SPACEFOX_SLOT3_FRAME','ux02-battery-slot3-100-green.png'),'ux02-battery-slot4-100.png']
        for index,name in enumerate(files):
            with self.subTest(slot=index+1):
                path=Path(name);path=path if path.is_absolute() else E/path
                im=Image.open(path).convert('RGB');self.assertEqual(im.size,(390,390));p=im.load();top=240 if index<2 else 278
                value=[(x,y) for y in range(top,top+44) for x in range(20,360) if p[x,y]==(205,182,255)]
                self.assertTrue(value);value_left=min(x for x,y in value)
                icon=[(x,y) for y in range(top+12,top+28) for x in range(max(0,value_left-34),value_left) if min(p[x,y])>130 and max(p[x,y])-min(p[x,y])<35]
                self.assertEqual(len(icon),171, f'icon shape changed: {name}')
                self.assertGreaterEqual(value_left-max(x for x,y in icon)-1,4)
                self.assertTrue(all((x-195)**2+(y-195)**2 < 191**2 for x,y in icon+value), f'circle margin violated: {name}')
    def test_lower_row_100_percent_and_12345_steps_do_not_overlap(self):
        im=Image.open(E/'ux02-battery-steps-paired.png').convert('RGB');p=im.load()
        battery=[(x,y) for y in range(285,325) for x in range(0,180) if p[x,y]==(205,182,255)]
        neighbor=[(x,y) for y in range(285,325) for x in range(180,390) if min(p[x,y])>130 and max(p[x,y])-min(p[x,y])<35]
        self.assertTrue(battery and neighbor)
        self.assertGreaterEqual(min(x for x,y in neighbor)-max(x for x,y in battery)-1,4)
        self.assertTrue(all((x-195)**2+(y-195)**2 < 191**2 for x,y in battery+neighbor))
if __name__=='__main__':unittest.main()
