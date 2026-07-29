package com.knowledgeassistant.backend.repository;

import com.knowledgeassistant.backend.entity.ChatSession;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

/** Persistence operations for chat sessions. */
public interface ChatSessionRepository extends JpaRepository<ChatSession, UUID> {
}
