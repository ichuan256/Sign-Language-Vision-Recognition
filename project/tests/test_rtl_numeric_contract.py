import csv
import hashlib
import json
import struct
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from project.scripts.r3.export_rtl_numeric_contract import Fixed, ROOT, export, input_map, parse_fixed

class FixedTests(unittest.TestCase):
    def test_negative_truncation_is_floor(self):
        fmt = Fixed(4, 2)
        for value, expected in [(Fraction(-1, 8), -1), (Fraction(1, 8), 0),
                                (Fraction(-3, 8), -2), (Fraction(3, 8), 1)]:
            self.assertEqual(fmt.encode(value), expected)

    def test_wrap_and_saturation_at_both_signed_limits(self):
        wrap, sat = Fixed(4, 2), Fixed(4, 2, overflow='AP_SAT')
        for value, wrapped, saturated in [(2, -8, 7), (Fraction(-9,4), 7, -8),
                                          (6, -8, 7), (-6, -8, -8)]:
            self.assertEqual(wrap.encode(value), wrapped)
            self.assertEqual(sat.encode(value), saturated)
        self.assertEqual(wrap.decode(-8), -2)
        self.assertEqual(wrap.decode(7), Fraction(7,4))

    def test_convergent_ties_and_neighbours(self):
        fmt = Fixed(4, 2, rounding='AP_RND_CONV')
        for value, expected in [(Fraction(1,8),0),(Fraction(3,8),2),
                                (Fraction(-1,8),0),(Fraction(-3,8),-2),
                                (Fraction(1,8)-Fraction(1,1000),0),
                                (Fraction(1,8)+Fraction(1,1000),1)]:
            self.assertEqual(fmt.encode(value),expected)

    def test_unsigned_and_roundtrip_all_raw_codes(self):
        for signed in (False, True):
            fmt = Fixed(6,2,signed=signed)
            lo, hi = (-32,32) if signed else (0,64)
            for raw in range(lo,hi):
                self.assertEqual(fmt.encode(fmt.decode(raw)),raw)
        self.assertEqual(Fixed(6,2,False).encode(-Fraction(1,16)),63)
        self.assertEqual(Fixed(6,2,False,overflow='AP_SAT').encode(-1),0)

    def test_formats_and_fail_closed(self):
        self.assertEqual(parse_fixed('fixed<24,10,TRN,WRAP,0>'), Fixed(24,10))
        self.assertEqual(parse_fixed('ap_ufixed<6,2,AP_RND_CONV,AP_SAT>'),
                         Fixed(6,2,False,'AP_RND_CONV','AP_SAT'))
        for bad in ['ap_fixed<4,2,AP_TRN_ZERO>', 'ap_fixed<4,2,AP_TRN,AP_WRAP,1>',
                    'ap_fixed<0,0>', 'float', 'ap_fixed<4,8>', 'ap_fixed<4,2,AP_TRN,AP_SAT_ZERO>']:
            with self.assertRaises(ValueError):
                parse_fixed(bad)

    def test_full_uint8_binary32_mapping(self):
        fmt = Fixed(40,2)
        rows = input_map(fmt)
        self.assertEqual(len(rows),256)
        self.assertEqual(rows[0]['raw_code'],0)
        self.assertEqual(rows[-1]['raw_code'],1 << 38)
        self.assertEqual(rows,sorted(rows,key=lambda r:r['raw_code']))
        # Independent nearest-neighbour check against exact p/255, using adjacent
        # binary32 bit patterns; avoid duplicating the float division algorithm.
        for row in rows[1:-1]:
            bits = struct.unpack('<I',struct.pack('<f',row['float32']))[0]
            target = Fraction(row['pixel'],255)
            actual = Fraction.from_float(row['float32'])
            for adjacent in (bits-1,bits+1):
                neighbour = Fraction.from_float(struct.unpack('<f',struct.pack('<I',adjacent))[0])
                self.assertLess(abs(actual-target),abs(neighbour-target))
            # All such binary32 values fit exactly in F=38 (lowest p is 1).
            self.assertEqual(fmt.decode(row['raw_code']),actual)
        self.assertTrue(any(r['delta'] for r in rows))

    def test_export_marks_missing_goldens_and_preserves_existing(self):
        (ROOT/'project/_tmp').mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'project/_tmp') as tmp:
            out = Path(tmp)/'contract'
            result = export(ROOT,out)
            saved = json.loads((out/'contract.json').read_text(encoding='utf-8'))
            self.assertEqual(result,saved)
            self.assertFalse(saved['model_golden_ready'])
            self.assertFalse(saved['rtl_numeric_contract_ready'])
            self.assertEqual(len(saved['layers']),18)
            self.assertEqual([r['operation'] for r in saved['layers']].count('Conv'),4)
            self.assertIsNone(saved['layers'][1]['hls_accumulator_type'])
            self.assertEqual(saved['formats']['input']['fractional'],38)
            self.assertTrue(all(rel.startswith('project/') for rel in saved['sources_sha256']))
            self.assertTrue(all(rel.startswith('project/_tmp/r3/') for rel in saved['expected_artifacts']))
            for rel,digest in saved['sources_sha256'].items():
                self.assertEqual(hashlib.sha256((ROOT/rel).read_bytes()).hexdigest(),digest)
            with (out/'input_uint8_to_fixed40.csv').open(encoding='utf-8') as f:
                self.assertEqual(len(list(csv.DictReader(f))),256)
            vectors = json.loads((out/'conversion_vectors.json').read_text(encoding='utf-8'))
            self.assertEqual(len(vectors['vectors']),35)
            before = (out/'contract.json').read_bytes()
            with self.assertRaises(FileExistsError):
                export(ROOT,out)
            self.assertEqual((out/'contract.json').read_bytes(),before)

if __name__ == '__main__':
    unittest.main()
