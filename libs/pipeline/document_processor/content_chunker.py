import hashlib
from typing import List
from libs.models.pipeline import ChunkData

OVERLAP_ESTIMATED_LINE_LENGTH = 50

class ContentChunker:
    """Handles content chunking and hashing."""

    def extract_chunks(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[ChunkData]:
        """Extract chunks from the processed content."""
        chunks: List[ChunkData] = []
        lines = content.split('\n')
        current_chunk: List[str] = []
        current_length = 0
        chunk_start_line = 0
        
        for i, line in enumerate(lines):
            line_length = len(line) + 1  # +1 for newline
            
            # If we can add the line to the current chunk, do it
            if not (current_length + line_length > chunk_size and current_chunk):
                current_chunk.append(line)
                current_length += line_length
            else:
                # Else finalise the current chunk and start a new one
                chunk_text = '\n'.join(current_chunk)
                chunks.append(ChunkData(
                    content=chunk_text,
                    content_hash=self.calculate_content_hash(chunk_text),
                    chunk_index=len(chunks),
                    start_line=chunk_start_line,
                    end_line=i - 1,
                    word_count_estimate=len(chunk_text.split()),
                ))
                
                
                # Start new chunk with overlap
                if overlap > 0:
                    # Calculate how many lines to overlap (roughly overlap/50 characters per line)
                    overlap_lines_count = max(1, min(len(current_chunk), overlap // OVERLAP_ESTIMATED_LINE_LENGTH))
                    overlap_lines = current_chunk[-overlap_lines_count:]
                    current_chunk = overlap_lines + [line]
                    current_length = sum(len(l) + 1 for l in current_chunk)
                    chunk_start_line = i - len(overlap_lines)
                else:
                    current_chunk = [line]
                    current_length = line_length
                    chunk_start_line = i
        
        # Add final chunk if there's remaining content
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append(ChunkData(
                content=chunk_text,
                content_hash=self.calculate_content_hash(chunk_text),
                chunk_index=len(chunks),
                start_line=chunk_start_line,
                end_line=len(lines) - 1,
                word_count_estimate=len(chunk_text.split()),
            ))
        
        return chunks
    
    def calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of the content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest() 