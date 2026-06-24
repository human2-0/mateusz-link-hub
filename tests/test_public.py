import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicSiteTest(unittest.TestCase):
    def test_landing_links_to_every_project(self):
        html = (ROOT / "public" / "index.html").read_text()
        for target in (
            "/master-compounder/",
            "/thoughts-blog/",
            "/tofufu/",
            "https://github.com/human2-0/ballistics_wallet",
        ):
            self.assertIn(f'href="{target}"', html)

    def test_router_owns_root_landing_assets(self):
        router = (ROOT / "shared_site_router.py").read_text()
        self.assertIn('"/": "index.html"', router)
        self.assertIn('"/assets/project-constellation.svg"', router)


if __name__ == "__main__":
    unittest.main()
