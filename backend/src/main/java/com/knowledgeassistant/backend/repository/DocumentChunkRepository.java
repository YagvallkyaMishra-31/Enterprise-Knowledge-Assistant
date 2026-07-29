package com.knowledgeassistant.backend.repository;

import com.knowledgeassistant.backend.entity.DocumentChunk;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

/** Persistence operations for document chunks (metadata only — embeddings managed by the RAG service). */
public interface DocumentChunkRepository extends JpaRepository<DocumentChunk, UUID> {
}
