package com.knowledgeassistant.backend.dto.chat;

/**
 * Request payload for creating a new chat session.
 *
 * @param title Optional title for the chat session. If omitted, a default title is generated.
 */
public record CreateSessionRequest(String title) {
}
