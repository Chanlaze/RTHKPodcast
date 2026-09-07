import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from trim_time_signal import detect_cut, np


class SignalTests(unittest.TestCase):
    def detect(self, starts):
        samples = np.zeros(420*8000)
        tone = 10000*np.sin(2*np.pi*1050*np.arange(1600)/8000)
        for start in starts:
            offset = int(start*8000)
            samples[offset:offset+1600] = tone
        responses = [subprocess.CompletedProcess([], 1, b'', b'Duration: 00:30:00.00'),
                     subprocess.CompletedProcess([], 0, samples.astype('<i2').tobytes(), b'')]
        with patch('trim_time_signal.subprocess.run', side_effect=responses):
            return detect_cut('ffmpeg', Path('sample.m4a'))

    def test_six_regular_pulses(self):
        self.assertAlmostEqual(self.detect(range(120, 126)), 1499.94, places=2)

    def test_incomplete_signal_is_preserved(self):
        self.assertIsNone(self.detect(range(120, 125)))

    def test_irregular_pulses_are_preserved(self):
        self.assertIsNone(self.detect([120, 121, 122, 123.5, 124.5, 125.5]))

    def test_ambiguous_sequences_are_preserved(self):
        self.assertIsNone(self.detect(list(range(120, 126))+list(range(140, 146))))

    def test_silence_is_preserved(self):
        self.assertIsNone(self.detect([]))


if __name__ == '__main__':
    unittest.main()
