import json
import os
import tempfile
import unittest
from pathlib import Path

import data_store
from relationship.judge import evaluate_affinity_delta


class RelationshipScenarioTests(unittest.TestCase):
    def setUp(self):
        self._env_backup = {k: os.environ.get(k) for k in ["DEBUG_RELATIONSHIP", "AFFINITY_TEST_FAST"]}
        os.environ["DEBUG_RELATIONSHIP"] = "1"
        os.environ["AFFINITY_TEST_FAST"] = "1"

    def tearDown(self):
        for k, v in self._env_backup.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _new_state(self, score=50.0):
        return {
            "affinity_score": score,
            "stable_streak": 0,
            "last_streak_reward_at": None,
            "risk_buffer": {
                "boundary_pressure": 0,
                "dependency_attempt": 0,
                "conflict_pattern": 0,
                "updated_at": None,
            },
        }

    def test_positive_stable_script_score_rises_with_rewards(self):
        state = self._new_state(50.0)
        deltas = []
        reward_steps = []

        for i in range(1, 61):
            delta, note = evaluate_affinity_delta(state, ["stable_interaction"], "medium")
            state["affinity_score"] = max(0.0, min(100.0, float(state["affinity_score"]) + delta))
            deltas.append(delta)
            if "streak_reward:" in note:
                reward_steps.append(i)

        self.assertAlmostEqual(deltas[0], 0.6, places=2)
        self.assertIn(4, reward_steps)
        self.assertIn(9, reward_steps)
        self.assertIn(15, reward_steps)
        self.assertGreater(state["affinity_score"], 90)

    def test_negative_medium_delayed_confirmation(self):
        state = self._new_state(60.0)

        delta1, note1 = evaluate_affinity_delta(state, ["boundary_pressure"], "medium")
        state["affinity_score"] += delta1
        self.assertEqual(delta1, 0.0)
        self.assertIn("buffer_accumulate:boundary_pressure:1", note1)
        self.assertEqual(state["risk_buffer"]["boundary_pressure"], 1)

        delta2, note2 = evaluate_affinity_delta(state, ["boundary_pressure"], "medium")
        state["affinity_score"] += delta2
        self.assertLess(delta2, 0.0)
        self.assertIn("buffer_trigger:boundary_pressure", note2)
        self.assertEqual(state["risk_buffer"]["boundary_pressure"], 0)

    def test_isolation_same_user_different_characters(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "user_data.json"
            db.write_text("{}", encoding="utf-8")
            old_file = data_store.USER_DATA_FILE
            data_store.USER_DATA_FILE = str(db)
            try:
                user = "u_iso"
                linyu = data_store.get_relationship_state(user, "linyu")
                xxm = data_store.get_relationship_state(user, "xiaxingmian")

                for _ in range(30):
                    d, _ = evaluate_affinity_delta(linyu, ["stable_interaction"], "medium")
                    linyu["affinity_score"] = max(0.0, min(100.0, float(linyu["affinity_score"]) + d))
                data_store.save_relationship_state(user, "linyu", linyu)

                for _ in range(10):
                    d, _ = evaluate_affinity_delta(xxm, ["boundary_pressure"], "medium")
                    xxm["affinity_score"] = max(0.0, min(100.0, float(xxm["affinity_score"]) + d))
                data_store.save_relationship_state(user, "xiaxingmian", xxm)

                stored = json.loads(db.read_text(encoding="utf-8"))[user]["relationships"]
                l_data = stored["linyu"]
                x_data = stored["xiaxingmian"]

                self.assertNotEqual(l_data["affinity_score"], x_data["affinity_score"])
                self.assertNotEqual(l_data["stable_streak"], x_data["stable_streak"])
                self.assertNotEqual(l_data["risk_buffer"].get("updated_at"), x_data["risk_buffer"].get("updated_at"))
            finally:
                data_store.USER_DATA_FILE = old_file


if __name__ == "__main__":
    unittest.main()
