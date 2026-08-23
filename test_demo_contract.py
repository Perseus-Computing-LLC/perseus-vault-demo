from __future__ import annotations

import re
import json
import time
import unittest
from pathlib import Path
from urllib.error import URLError
from unittest.mock import patch

import app
from app import result_payload


ROOT = Path(__file__).parent
INDEX = ROOT / "index.html"
APP = ROOT / "app.py"


class DemoContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = INDEX.read_text(encoding="utf-8")
        cls.app = APP.read_text(encoding="utf-8")

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
        self.assertIn('complete · before → teach → after → use', self.html)
        for phase in ("BEFORE", "TEACH", "AFTER", "USE"):
            self.assertIn(phase, self.html)
        self.assertIn('No relevant project context in this fresh task.', self.html)

    def test_fresh_empty_state_is_explicit(self) -> None:
        self.assertIn('id="phase-before"', self.html)
        self.assertIn("0 relevant memories · empty by design", self.html)
        self.assertIn("The agent would have to rediscover these facts.", self.html)
        self.assertIn("Each run starts with a fresh opaque browser scope", self.html)

    def test_teaching_progress_shows_what_was_captured(self) -> None:
        self.assertIn('Captured in this scope', self.html)
        self.assertIn('id="capture-list"', self.html)
        self.assertIn('await remember(text, key, category, true);', self.html)
        self.assertIn('recordCaptured(textValue, result.key || keyValue, categoryValue);', self.html)
        self.assertIn('decisions captured', self.html)

    def test_recall_explains_the_relevant_subset_and_omission(self) -> None:
        self.assertIn('Vault selected ${items.length} of ${capturedMemories.length} captured memories for this task.', self.html)
        self.assertIn('Left out for this task:', self.html)
        self.assertIn('const omittedCount = capturedMemories.filter', self.html)
        self.assertIn('Captured context stays out when it is not selected for the question.', self.html)

    def test_context_is_bounded_and_copyable(self) -> None:
        self.assertIn('id="copy-context"', self.html)
        self.assertIn('navigator.clipboard.writeText(lastContextText)', self.html)
        self.assertIn('characters · bounded to 2,400 max', self.html)
        self.assertIn('max_context_chars', self.app)
        self.assertIn('role="status" aria-live="polite"', self.html)

    def test_repeated_runs_use_fresh_scopes_and_reset_visible_counts(self) -> None:
        self.assertIn('perseus-vault-demo-session-v3', self.html)
        self.assertIn('function resetRunState()', self.html)
        self.assertIn('storyRunning = true;', self.html)
        self.assertIn('stats = { stored: 0, hits: 0, contexts: 0, followed: 0 };', self.html)
        self.assertIn('Started a fresh isolated scope.', self.html)
        self.assertNotIn('perseus-vault-demo-stats-v2', self.html)

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
            r"async function prepareContext\([^)]*\) \{(?P<body>.*?)\n  \}\n\n  async function copyContext",
            self.html,
            re.DOTALL,
        )
        self.assertIsNotNone(recall_block)
        self.assertIsNotNone(context_block)
        if recall_block is None or context_block is None:
            self.fail("expected recall and context function blocks")
        self.assertIn("if (propagate) throw error;", recall_block.group("body"))
        self.assertIn("if (propagate) throw error;", context_block.group("body"))
        self.assertIn("contextResult", self.html)
        self.assertIn("if (!contextResult || !lastContextText)", self.html)
        self.assertIn('setStoryState(error.message, "error")', self.html)

    def test_recall_payload_does_not_publish_internal_diagnostics(self) -> None:
        code, payload = result_payload(
            {"ok": True, "data": {"items": [], "diagnostic": {"hint": "internal"}}},
            time.perf_counter(),
            operation="recall",
        )
        self.assertEqual(code, 200)
        self.assertNotIn("diagnostic", payload["data"])
        self.assertNotIn("diagnostic.hint", self.html)
        self.assertNotIn("no active memories carry embeddings", self.html)
        self.assertIn('data.pop("diagnostic", None)', self.app)

    def test_value_receipt_is_scoped_to_real_deployments(self) -> None:
        self.assertIn("REAL DEPLOYMENT ONLY", self.html)
        self.assertNotIn("LEDGER-VERIFIABLE</span>", self.html)
        self.assertIn("not a customer savings number", self.html)
        self.assertIn("Not populated by this browser demo", self.html)

    def test_success_state_explains_the_observed_product_change(self) -> None:
        self.assertIn('id="outcome-summary"', self.html)
        self.assertIn("Vault changed the starting point", self.html)
        self.assertIn("function renderOutcome", self.html)
        self.assertIn("outcome.hidden = false", self.html)
        self.assertIn("0 relevant memories", self.html)

    def test_context_public_projection_enforces_the_character_cap(self) -> None:
        self.assertEqual(app.public_context_text({"data": {"context_markdown": "ok"}}), "ok")
        with self.assertRaises(ValueError):
            app.public_context_text({"data": {"context_markdown": "x" * 2_401}})

    def test_context_browser_path_rejects_an_oversized_artifact(self) -> None:
        self.assertIn("if (text.length > 2400)", self.html)
        self.assertIn("context exceeds the public 2,400-character bound", self.html)

    def test_ledger_evidence_classifies_configuration_and_upstream_failures(self) -> None:
        with patch.object(app, "LEDGER_URL", ""):
            with patch.object(app, "LEDGER_ORG", ""):
                with patch.object(app, "LEDGER_API_KEY", ""):
                    code, payload = app.ledger_evidence()
        self.assertEqual(code, 503)
        self.assertEqual(payload["status"], "not_configured")

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, _limit):
                raise URLError("ledger unavailable")

        with patch.object(app, "LEDGER_URL", "https://ledger.example"):
            with patch.object(app, "LEDGER_ORG", "demo-org"):
                with patch.object(app, "LEDGER_API_KEY", "test-key"):
                    with patch.object(app, "urlopen", side_effect=URLError("ledger unavailable")):
                        code, payload = app.ledger_evidence()
        self.assertEqual(code, 502)
        self.assertEqual(payload["status"], "upstream_unavailable")

    def test_ledger_ui_distinguishes_unavailable_from_not_configured(self) -> None:
        self.assertIn("Ledger evidence is temporarily unavailable", self.html)
        self.assertIn("Ledger evidence is not configured", self.html)
        self.assertIn("data.status === \"upstream_unavailable\"", self.html)

    def test_public_response_headers_have_a_narrow_security_policy(self) -> None:
        self.assertEqual(app.SECURITY_HEADERS["X-Frame-Options"], "DENY")
        self.assertIn("Content-Security-Policy", app.SECURITY_HEADERS)
        self.assertIn("frame-src https://github.com", app.SECURITY_HEADERS["Content-Security-Policy"])
        self.assertIn("object-src 'none'", app.SECURITY_HEADERS["Content-Security-Policy"])

    def test_container_has_a_process_healthcheck(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("HEALTHCHECK", dockerfile)
        self.assertIn("/healthz", dockerfile)

    def test_copy_does_not_claim_that_the_demo_executes_agent_actions(self) -> None:
        self.assertIn("Prepare usable context", self.html)
        self.assertNotIn("Act with the right context", self.html)

    def test_ledger_zero_event_state_is_explicit(self) -> None:
        self.assertIn('"no_scoped_events"', self.app)
        self.assertIn('"organization_chain_verified"', self.app)
        self.assertIn("No demo-scoped Ledger events are available", self.html)
        self.assertIn("organization chain is verified", self.html)

    def test_ledger_evidence_rejects_mismatched_scope_and_false_string(self) -> None:
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, _limit):
                return json.dumps({
                    "organization": {"id": "other-org"},
                    "external_ref": "other-ref",
                    "events": [{"id": "unrelated"}],
                    "verification": {"chain_ok": "false", "verified_events": "1"},
                }).encode()

        with patch.object(app, "LEDGER_URL", "https://ledger.example"), \
             patch.object(app, "LEDGER_ORG", "demo-org"), \
             patch.object(app, "LEDGER_API_KEY", "test-key"), \
             patch.object(app, "LEDGER_EXTERNAL_REF", "vault-demo"), \
             patch.object(app, "urlopen", return_value=Response()):
            code, payload = app.ledger_evidence()
        self.assertEqual(code, 502)
        self.assertEqual(payload, {
            "error": "Ledger evidence scope could not be verified",
            "status": "scope_unverified",
        })

    def test_ledger_evidence_accepts_exact_empty_scope_without_truthiness(self) -> None:
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, _limit):
                return json.dumps({
                    "organization": {"id": "demo-org"},
                    "external_ref": "vault-demo",
                    "events": [],
                    "verification": {"chain_ok": True, "verified_events": 0},
                }).encode()

        with patch.object(app, "LEDGER_URL", "https://ledger.example"), \
             patch.object(app, "LEDGER_ORG", "demo-org"), \
             patch.object(app, "LEDGER_API_KEY", "test-key"), \
             patch.object(app, "LEDGER_EXTERNAL_REF", "vault-demo"), \
             patch.object(app, "urlopen", return_value=Response()):
            code, payload = app.ledger_evidence()
        self.assertEqual(code, 200)
        self.assertEqual(payload["scope_status"], "no_scoped_events")
        self.assertEqual(payload["chain_status"], "organization_chain_verified")
        self.assertIs(payload["chain_ok"], True)


if __name__ == "__main__":
    unittest.main()
