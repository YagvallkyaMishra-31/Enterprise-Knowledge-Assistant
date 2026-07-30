package com.knowledgeassistant.backend.service;

import com.knowledgeassistant.backend.dto.chat.ChatSessionResponse;
import com.knowledgeassistant.backend.dto.chat.CreateSessionRequest;
import com.knowledgeassistant.backend.dto.chat.QaPairResponse;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.List;
import java.util.UUID;

/** Service interface for managing chat sessions and orchestrating RAG queries. */
public interface ChatService {

    /**
     * Creates a new chat session for the given user.
     *
     * @param request The session creation request.
     * @param userId  The ID of the user creating the session.
     * @return The created session response.
     */
    ChatSessionResponse createSession(CreateSessionRequest request, UUID userId);

    /**
     * Retrieves all chat sessions for the given user.
     *
     * @param userId The ID of the user.
     * @return A list of chat session responses.
     */
    List<ChatSessionResponse> getUserSessions(UUID userId);

    /**
     * Retrieves all question-answer pairs for a specific session.
     *
     * @param sessionId The ID of the session.
     * @param userId    The ID of the user, used for ownership verification.
     * @return A list of QA pair responses.
     */
    List<QaPairResponse> getSessionMessages(UUID sessionId, UUID userId);

    /**
     * Initiates a streaming RAG query for a specific session.
     *
     * @param sessionId The ID of the session.
     * @param userId    The ID of the user.
     * @param question  The user's question.
     * @return An SseEmitter that streams the answer and sources.
     */
    SseEmitter askQuestionStream(UUID sessionId, UUID userId, String question);
}
