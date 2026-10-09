"""Semantic and sliding-window chunking for scientific literature."""

import re
from typing import List, Dict, Any
from privearch.schemas import DocumentChunk


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences while respecting scientific abbreviations (e.g., e.g., i.e., Fig., Eq., etc.)."""
    # Replace common scientific abbreviations with temporary tokens
    subs = {
        r'\bFig\.\s*': 'Fig_DOT_ ',
        r'\bEq\.\s*': 'Eq_DOT_ ',
        r'\bi\.e\.\s*': 'ie_DOT_ ',
        r'\be\.g\.\s*': 'eg_DOT_ ',
        r'\bref\.\s*': 'ref_DOT_ ',
        r'\bvs\.\s*': 'vs_DOT_ ',
        r'\bapprox\.\s*': 'approx_DOT_ ',
        r'\bvol\.\s*': 'vol_DOT_ ',
        r'\bno\.\s*': 'no_DOT_ ',
    }
    processed = text
    for pattern, replacement in subs.items():
        processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)

    # Split by standard sentence terminators
    raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])|\n\n+', processed)

    sentences = []
    for s in raw_sentences:
        clean_s = s.strip()
        if not clean_s:
            continue
        # Restore abbreviations
        clean_s = clean_s.replace('Fig_DOT_', 'Fig.').replace('Eq_DOT_', 'Eq.')
        clean_s = clean_s.replace('ie_DOT_', 'i.e.').replace('eg_DOT_', 'e.g.')
        clean_s = clean_s.replace('ref_DOT_', 'ref.').replace('vs_DOT_', 'vs.')
        clean_s = clean_s.replace('approx_DOT_', 'approx.').replace('vol_DOT_', 'vol.')
        clean_s = clean_s.replace('no_DOT_', 'no.')
        sentences.append(clean_s)

    return sentences


def chunk_document(
    doc_info: Dict[str, Any],
    chunk_size_words: int = 150,
    chunk_overlap_words: int = 30,
    min_chunk_words: int = 20
) -> List[DocumentChunk]:
    """
    Partitions pages into overlapping semantic chunks with explicit page and section metadata.
    """
    doc_name = doc_info["doc_name"]
    chunks: List[DocumentChunk] = []
    chunk_counter = 0

    for page_data in doc_info.get("pages", []):
        page_num = page_data["page_num"]
        section_header = page_data.get("section_header", "")
        page_text = page_data["text"]

        sentences = split_into_sentences(page_text)
        if not sentences:
            continue

        current_words: List[str] = []
        current_chunk_sentences: List[str] = []

        for sentence in sentences:
            sentence_words = sentence.split()
            if not sentence_words:
                continue

            # If adding this sentence exceeds chunk size and we already have minimum words
            if len(current_words) + len(sentence_words) > chunk_size_words and len(current_words) >= min_chunk_words:
                chunk_counter += 1
                chunk_text = " ".join(current_chunk_sentences).strip()
                chunks.append(DocumentChunk(
                    chunk_id=f"{doc_name}_p{page_num}_c{chunk_counter}",
                    doc_name=doc_name,
                    page_num=page_num,
                    section_header=section_header,
                    text=chunk_text,
                    char_count=len(chunk_text),
                    word_count=len(current_words)
                ))

                # Slide window with overlap: preserve sentences from tail up to overlap words
                overlap_words_count = 0
                new_sentences: List[str] = []
                for s in reversed(current_chunk_sentences):
                    s_words = len(s.split())
                    if overlap_words_count + s_words <= chunk_overlap_words:
                        new_sentences.insert(0, s)
                        overlap_words_count += s_words
                    else:
                        break

                current_chunk_sentences = new_sentences
                current_words = " ".join(current_chunk_sentences).split() if current_chunk_sentences else []

            current_chunk_sentences.append(sentence)
            current_words.extend(sentence_words)

        # Flush final remaining chunk on page
        if current_words and len(current_words) >= min_chunk_words:
            chunk_counter += 1
            chunk_text = " ".join(current_chunk_sentences).strip()
            chunks.append(DocumentChunk(
                chunk_id=f"{doc_name}_p{page_num}_c{chunk_counter}",
                doc_name=doc_name,
                page_num=page_num,
                section_header=section_header,
                text=chunk_text,
                char_count=len(chunk_text),
                word_count=len(current_words)
            ))

    return chunks
