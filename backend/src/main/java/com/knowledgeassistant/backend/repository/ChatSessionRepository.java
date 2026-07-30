package com.knowledgeassistant.backend.repository;

import com.knowledgeassistant.backend.entity.ChatSession;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/** Persistence operations for chat sessions. */
public interface ChatSessionRepository extends JpaRepository<ChatSession, UUID> {

    /** Finds all chat sessions for a specific user, ordered by creation time descending. */
    List<ChatSession> findByOwnerIdOrderByCreatedAtDesc(UUID ownerId);

    /** Finds a specific chat session by its ID and owner ID to ensure isolation. */
    Optional<ChatSession> findByIdAndOwnerId(UUID id, UUID ownerId);
}
