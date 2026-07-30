package com.knowledgeassistant.backend.repository;

import com.knowledgeassistant.backend.entity.QaPair;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

/** Persistence operations for question-answer pairs with their source citations. */
public interface QaPairRepository extends JpaRepository<QaPair, UUID> {

    /** Finds all QA pairs for a specific chat session, ordered by creation time ascending. */
    List<QaPair> findByChatSessionIdOrderByCreatedAtAsc(UUID chatSessionId);
}
