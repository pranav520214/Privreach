"""Meeting Intelligence Engine: Diarization, chronological summaries, decisions, and action items."""

import re
import time
from typing import Dict, Any, List, Optional, Tuple

from privearch.schemas import EvidenceChunk, ArtifactRecord, ArtifactType
from privearch.multimodal.audio_engine import AudioProcessor


class MeetingIntelligenceEngine:
    """
    Extracts decisions, hypotheses, action items, and timelines
    from scientific meetings and researcher discussions.
    """

    def __init__(self, audio_processor: Optional[AudioProcessor] = None):
        self.audio_processor = audio_processor or AudioProcessor()

    @staticmethod
    def diarize_segments(raw_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assigns or normalizes speaker turns across transcript segments.
        If speakers are already tagged (e.g. 'Speaker 1', 'Speaker 2'), preserves them.
        Otherwise uses turn-based alternating heuristics or audio cues.
        """
        diarized = []
        current_speaker_idx = 1

        for idx, seg in enumerate(raw_segments):
            text = seg.get("text", "")
            # Check for inline speaker marker like "Alice: ..." or "Dr. Smith: ..."
            match = re.match(r'^([A-Z][a-zA-Z\s\.]+):\s*(.+)', text)
            if match:
                speaker = match.group(1).strip()
                clean_text = match.group(2).strip()
            else:
                speaker = seg.get("speaker") or f"Researcher {current_speaker_idx}"
                clean_text = text

            diarized.append({
                "segment_id": idx + 1,
                "start": seg.get("start", 0.0),
                "end": seg.get("end", 0.0),
                "timecode": AudioProcessor.format_timecode(seg.get("start", 0.0)),
                "speaker": speaker,
                "text": clean_text
            })

            # Heuristic turn alternation if long pause between segments
            if idx > 0 and (seg.get("start", 0.0) - raw_segments[idx - 1].get("end", 0.0)) > 2.5:
                current_speaker_idx = 2 if current_speaker_idx == 1 else 1

        return diarized

    def extract_meeting_insights(
        self,
        diarized_segments: List[Dict[str, Any]],
        title: str = "Research Lab Meeting"
    ) -> Dict[str, Any]:
        """
        Extracts structured meeting intelligence: timeline, decisions, questions, action items.
        """
        timeline = []
        decisions = []
        open_questions = []
        action_items = []

        decision_keywords = ["decided", "agreed", "concluded", "confirmed", "verified", "settled on", "choose", "select"]
        question_keywords = ["why", "how", "what if", "uncertain", "hypothesis", "unclear", "doubt", "investigate"]
        action_keywords = ["action item", "will run", "will calculate", "should test", "todo", "follow up", "next step", "assigned to"]

        for seg in diarized_segments:
            tc = seg["timecode"]
            spk = seg["speaker"]
            txt = seg["text"]
            txt_lower = txt.lower()

            # Timeline entry
            timeline.append(f"[{tc}] **{spk}**: {txt}")

            # Decisions
            for kw in decision_keywords:
                if kw in txt_lower:
                    decisions.append({
                        "timecode": tc,
                        "speaker": spk,
                        "decision": txt
                    })
                    break

            # Open Questions
            for kw in question_keywords:
                if kw in txt_lower or txt.endswith("?"):
                    open_questions.append({
                        "timecode": tc,
                        "speaker": spk,
                        "question": txt
                    })
                    break

            # Action Items
            for kw in action_keywords:
                if kw in txt_lower:
                    action_items.append({
                        "timecode": tc,
                        "assignee": spk,
                        "task": txt
                    })
                    break

        return {
            "title": title,
            "total_segments": len(diarized_segments),
            "speakers": list(set(s["speaker"] for s in diarized_segments)),
            "timeline": timeline,
            "decisions": decisions,
            "open_questions": open_questions,
            "action_items": action_items
        }

    def format_meeting_markdown(self, insights: Dict[str, Any]) -> str:
        """Formats meeting intelligence as an academic laboratory memo."""
        md = [
            f"# 🎙️ Meeting Intelligence Report: {insights['title']}",
            f"**Participants:** {', '.join(insights['speakers']) or 'Research Team'}  ",
            f"**Total Segments:** {insights['total_segments']}\n",
            "---",
            "## 📌 Scientific Decisions & Conclusions"
        ]

        if insights["decisions"]:
            for d in insights["decisions"]:
                md.append(f"• **[{d['timecode']}]** ({d['speaker']}): {d['decision']}")
        else:
            md.append("*No explicit consensus decisions identified.*")

        md.append("\n## ❓ Unresolved Hypotheses & Open Questions")
        if insights["open_questions"]:
            for q in insights["open_questions"]:
                md.append(f"• **[{q['timecode']}]** ({q['speaker']}): {q['question']}")
        else:
            md.append("*No unresolved open questions flagged.*")

        md.append("\n## 📋 Assigned Action Items")
        if insights["action_items"]:
            for a in insights["action_items"]:
                md.append(f"• **[{a['timecode']}]** [{a['assignee']}]: {a['task']}")
        else:
            md.append("*No immediate action items recorded.*")

        md.append("\n## ⏱️ Chronological Meeting Transcript Timeline")
        md.extend(insights["timeline"][:40])  # preview top 40 turns
        if len(insights["timeline"]) > 40:
            md.append(f"\n*... and {len(insights['timeline']) - 40} more speaker turns.*")

        return "\n".join(md)
