package com.knowledgeassistant.backend.dto.chat;

import java.time.Instant;
import java.util.UUID;

/**
 * Response payload representing a chat session.
 *
 * @param id        The UUID of the chat session.
 * @param title     The title of the chat session.
 * @param createdAt The time the session was created.
 */
public record ChatSessionResponse(UUID id, String title, Instant createdAt) {
}
