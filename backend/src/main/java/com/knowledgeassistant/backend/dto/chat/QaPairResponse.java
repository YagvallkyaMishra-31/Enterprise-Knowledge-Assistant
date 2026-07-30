package com.knowledgeassistant.backend.dto.chat;

import com.fasterxml.jackson.databind.JsonNode;

import java.time.Instant;
import java.util.UUID;

/**
 * Response payload representing a single QA pair within a chat session.
 *
 * @param id        The UUID of the QA pair.
 * @param question  The user's question.
 * @param answer    The assistant's generated answer.
 * @param sources   The sources used for the answer, represented as a JSON node.
 * @param createdAt The time the QA pair was created.
 */
public record QaPairResponse(UUID id, String question, String answer, JsonNode sources, Instant createdAt) {
}
