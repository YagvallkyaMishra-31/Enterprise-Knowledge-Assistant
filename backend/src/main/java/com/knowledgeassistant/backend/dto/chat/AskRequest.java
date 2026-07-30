package com.knowledgeassistant.backend.dto.chat;

import jakarta.validation.constraints.NotBlank;

/**
 * Request payload for asking a question in a chat session.
 *
 * @param question The user's question, must not be blank.
 */
public record AskRequest(@NotBlank(message = "Question must not be blank") String question) {
}
