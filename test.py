from unittest import TestCase, main

class TestSemverBumper(TestCase):
    def test_semver_bumper(self):
        from xcute import semver_bumper
        self.assertEqual(semver_bumper("0.0.0"), "0.0.1")
        self.assertEqual(semver_bumper("0.0.0", "minor"), "0.1.0")
        self.assertEqual(semver_bumper("0.0.0", "major"), "1.0.0")
        self.assertEqual(semver_bumper("0.0.0", "0.9.6"), "0.9.6")

    def test_natsorted(self):
        from xcute.utils import natsorted
        self.assertEqual(natsorted(["1", "10", "2"]), ["1", "2", "10"])
        self.assertEqual(natsorted(["10. a", "2. b", "1. c"]), ["1. c", "2. b", "10. a"])

if __name__ == "__main__":
    main()
