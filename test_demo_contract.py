from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
INDEX = ROOT / "index.html"


class DemoContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = INDEX.read_text(encoding="utf-8")

    def test_page_explains_product_before_demo(self) -> None:
        self.assertIn(
            "An open-source memory layer for AI agents and engineering teams.",
            self.html,
        )
        self.assertIn("Store one decision. In a later task", self.html)
        self.assertIn('rel="canonical"', self.html)
        self.assertIn('property="og:title"', self.html)

    def test_primary_cta_runs_the_real_story(self) -> None:
        self.assertIn('id="hero-demo"', self.html)
        self.assertIn('Run the 60-second demo', self.html)
        self.assertIn('event.preventDefault()', self.html)
        self.assertIn('headerHeight', self.html)
        self.assertIn('window.scrollTo({ top:', self.html)
        self.assertIn('runStory();', self.html)
        self.assertIn('complete · capture → recall → prepare', self.html)
        self.assertIn('Phase 1:', self.html)
        self.assertIn('Phase 2:', self.html)
        self.assertIn('Phase 3:', self.html)
        self.assertIn('Phase 4:', self.html)

    def test_empty_states_explain_the_next_observable_step(self) -> None:
        self.assertIn(
            "Run the demo to see the matching decision appear here.",
            self.html,
        )
        self.assertIn(
            "Run the demo to see the bounded context block an agent can read",
            self.html,
        )
        self.assertIn('aria-live="polite"', self.html)

    def test_story_does_not_report_success_after_api_failure(self) -> None:
        recall_block = re.search(
            r"async function recall\([^)]*\) \{(?P<body>.*?)\n  \}\n\n  async function prepareContext",
            self.html,
            re.DOTALL,
        )
        context_block = re.search(
            r"async function prepareContext\([^)]*\) \{(?P<body>.*?)\n  \}\n\n  async function runStory",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(recall_block)
        self.assertIsNotNone(context_block)
        if recall_block is None or context_block is None:
            self.fail("expected recall and context function blocks")
        self.assertIn("if (propagate) throw error;", recall_block.group("body"))
        self.assertIn("if (propagate) throw error;", context_block.group("body"))
        self.assertIn('setStoryState(error.message, "error")', self.html)

    def test_value_receipt_is_scoped_to_real_deployments(self) -> None:
        self.assertIn("REAL DEPLOYMENT ONLY", self.html)
        self.assertNotIn("LEDGER-VERIFIABLE</span>", self.html)
        self.assertIn("not a customer savings number", self.html)
        self.assertIn("Not populated by this browser demo", self.html)

    def test_copy_does_not_claim_that_the_demo_executes_agent_actions(self) -> None:
        self.assertIn("Prepare the right context", self.html)
        self.assertNotIn("Act with the right context", self.html)


if __name__ == "__main__":
    unittest.main()
