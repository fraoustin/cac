import unittest

import app


class TestInterface(unittest.TestCase):

    def setUp(self):
        # execute before
        pass

    def test__basic_version(self):
        self.assertTrue(hasattr(app, '__prg_version__'))
        self.assertNotEqual(app.__prg_version__, '0.0.0')

    def test__basic_name(self):
        self.assertTrue(hasattr(app, '__prg_name__'))
        self.assertNotEqual(app.__prg_name__, '0.0.0')


if __name__ == '__main__':
    unittest.main()
